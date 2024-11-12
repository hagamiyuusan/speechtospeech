# app/services.py
import json
from typing import List, Dict, Optional
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Conversation
from .schema import ConversationBase, Message
from uuid import UUID, uuid4
from datetime import datetime
from agent.main_agent import MainAgent
from retrieval_handler.llm_handler import LLMHandler

class ChatService:
    def __init__(self, redis_url: str, session: AsyncSession, agent: MainAgent, llm_handler: LLMHandler):
        print(redis_url)
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.session = session
        self.agent = agent
        self.llm_handler = llm_handler

    async def generate_title(self, content: str):
        messages = [
            {"role": "user", "content": f"Generate a title for the conversation with the following content: {content}"}
        ]
        return await self.llm_handler.generate_response(messages)

    async def list_conversations(self) -> List[Dict]:
        query = select(Conversation).order_by(Conversation.modified_at.desc())
        result = await self.session.execute(query)
        convos = result.scalars().all()
        return [ConversationBase(
            id=str(convo.id),
            title=convo.title,
        ) for convo in convos]
    

    async def load_conversation(self, id: UUID):
        cached_convo = await self.redis.get(f"{id}")
        if cached_convo:
            return json.loads(cached_convo)
        result = await self.session.execute(select(Conversation).where(Conversation.id == id))
        convo = result.scalars().first()
        if convo:
            serialized_convo = {
                "id": str(convo.id),
                "title": convo.title,
                "messages": convo.messages,
                "created_at": convo.created_at.isoformat() if convo.created_at else None,
                "modified_at": convo.modified_at.isoformat() if convo.modified_at else None
            }
            await self.redis.setex(f"{id}", 3600, json.dumps(serialized_convo,ensure_ascii=False))
            return serialized_convo
        else:
            return None
    

    async def _update_conversation(self, id: UUID, new_message: Dict, is_new_conversation: bool = False):
        """Helper function to update both database and Redis cache atomically"""
        try:
            # Update database
            if is_new_conversation:
                title = await self.generate_title(new_message['content'])
                db_convo = Conversation(
                    id=id,
                    title=title,
                    messages=[new_message],
                    created_at=datetime.now(),
                    modified_at=datetime.now()
                )
                self.session.add(db_convo)
            else:
                db_convo = await self.session.execute(
                    select(Conversation).where(Conversation.id == id)
                )
                db_convo = db_convo.scalars().first()
                if not db_convo:
                    raise ValueError(f"Conversation {id} not found")
                
                db_convo.messages.append(new_message)
                db_convo.modified_at = datetime.now()
            
            await self.session.commit()
            await self.session.refresh(db_convo)

            # Update Redis cache
            serialized_convo = {
                "id": str(db_convo.id),
                "title": db_convo.title,
                "messages": db_convo.messages,
                "created_at": db_convo.created_at.isoformat() if db_convo.created_at else None,
                "modified_at": db_convo.modified_at.isoformat()
            }
            await self.redis.setex(
                f"{id}",
                3600,
                json.dumps(serialized_convo, ensure_ascii=False)
            )
            
            return db_convo
            
        except Exception as e:
            await self.session.rollback()
            print(f"Error updating conversation: {str(e)}")
            raise


    async def create_conversation(self, conversation_id: UUID, messages: List[Dict]):
        """Create a new conversation"""
        messages_dicts = []
        for message in messages:
            if isinstance(message, Message):
                messages_dicts.append(message.dict())
            elif isinstance(message, dict):
                messages_dicts.append(message)
            else:
                raise ValueError('Messages must be list of dicts or Message objects')
        
        first_message = messages_dicts[0]
        db_convo = await self._update_conversation(
            id=conversation_id,
            new_message=first_message,
            is_new_conversation=True
        )
        return db_convo


    async def stream_response(self, id: UUID, message: Message):
        try:
            convo = await self.load_conversation(id)
            message_dict = {
                "id": str(message.id),
                "role": message.role,
                "content": message.content
            }

            # Update conversation with user message
            try:
                db_convo = await self._update_conversation(
                    id=id,
                    new_message=message_dict,
                    is_new_conversation=(convo is None)
                )
                messages_list = db_convo.messages
            except Exception as e:
                yield json.dumps({"error": f"Failed to save message: {str(e)}"}) + "\n"
                return

            # Generate and stream response
            response_stream = await self.agent.response(messages_list)
            full_response = ""
            async for chunk in response_stream:
                full_response += chunk
                yield json.dumps({"content": chunk}) + "\n"

            # Send final response
            response_id = str(uuid4())
            yield json.dumps({
                "id": response_id,
                "full_response": full_response
            }) + "\n"

            # Update conversation with assistant's response
            try:
                await self._update_conversation(
                    id=id,
                    new_message={
                        "id": response_id,
                        "role": "assistant",
                        "content": full_response
                    },
                    is_new_conversation=False
                )
            except Exception as e:
                yield json.dumps({"error": f"Failed to save response: {str(e)}"}) + "\n"

            # Send completion signal
            yield json.dumps({"done": True}) + "\n"

        except Exception as e:
            print(f"Stream response error: {str(e)}")
            yield json.dumps({"error": str(e)}) + "\n"
            yield json.dumps({"done": True}) + "\n"


    async def delete_all_conversations(self):
        try:
            # Delete all records from conversations table
            await self.session.execute("TRUNCATE TABLE conversations CASCADE")
            # Clear Redis cache
            await self.redis.flushdb()
            await self.session.commit()
            print("Database cleared successfully")  # Log để kiểm tra
            return {"message": "All conversations deleted successfully"}
        except Exception as e:
            await self.session.rollback()
            print(f"Error clearing database: {str(e)}")  # Log lỗi nếu có
            raise Exception(f"Error deleting conversations: {str(e)}")