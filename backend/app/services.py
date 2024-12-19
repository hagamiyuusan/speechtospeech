# app/services.py
import json
from typing import List, Dict, Optional
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Conversation, Workspace, User
from .schema import ConversationBase, Message
from uuid import UUID, uuid4
from datetime import datetime
from managers import AgentManager
from retrieval_handler.llm_handler import LLMHandler
from sqlalchemy import and_
class ChatService:
    def __init__(self, redis_url: str, session: AsyncSession, agent_manager: AgentManager, llm_handler: LLMHandler):
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.session = session
        self.agent_manager = agent_manager
        self.llm_handler = llm_handler

    async def get_user_workspace(self, user_id: str, workspace_id: str) -> Optional[Workspace]:
        """Get workspace if user has access to it"""
        query = select(Workspace).join(Workspace.users).where(
            and_(
                Workspace.id == workspace_id,
                User.id == user_id
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_conversations(self, user_id: str, workspace_id: str) -> List[Dict]:
        """List conversations for a user in a specific workspace"""
        # Verify user has access to workspace
        workspace = await self.get_user_workspace(user_id, workspace_id)
        if not workspace:
            raise ValueError("User does not have access to this workspace")

        query = select(Conversation).where(
            and_(
                Conversation.workspace_id == workspace_id,
                Conversation.user_id == user_id
            )
        ).order_by(Conversation.modified_at.desc())
        
        result = await self.session.execute(query)
        convos = result.scalars().all()
        return [ConversationBase(
            id=str(convo.id),
            title=convo.title,
        ) for convo in convos]
    
    async def load_conversation(self, id: UUID, user_id: str):
        """Load a conversation with workspace access check"""
        cached_convo = await self.redis.get(f"{id}")
        if cached_convo:
            convo_data = json.loads(cached_convo)
            # Verify user has access
            workspace = await self.get_user_workspace(user_id, convo_data.get('workspace_id'))
            if not workspace:
                raise ValueError("User does not have access to this conversation")
            return convo_data

        result = await self.session.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == id,
                    Conversation.user_id == user_id
                )
            )
        )
        convo = result.scalars().first()
        if convo:
            # Verify user has access to workspace
            workspace = await self.get_user_workspace(user_id, convo.workspace_id)
            if not workspace:
                raise ValueError("User does not have access to this conversation")

            serialized_convo = {
                "id": str(convo.id),
                "title": convo.title,
                "messages": convo.messages,
                "workspace_id": convo.workspace_id,
                "created_at": convo.created_at.isoformat() if convo.created_at else None,
                "updated_at": convo.updated_at.isoformat() if convo.updated_at else None
            }
            await self.redis.setex(f"{id}", 3600, json.dumps(serialized_convo,ensure_ascii=False))
            return serialized_convo
        return None

    async def chat_response(self, id: UUID, message: Message, user_id: str, workspace_id: str):
        """Generate chat response using workspace's agent"""
        # Verify user has access to workspace
        workspace = await self.get_user_workspace(user_id, workspace_id)
        if not workspace:
            raise ValueError("User does not have access to this workspace")

        # Get workspace's agent
        agent = await self.agent_manager.get_agent(workspace_id)
        if not agent:
            raise ValueError("No agent found for this workspace")

        # Load or create conversation
        conversation = await self.load_conversation(id, user_id)
        is_new_conversation = False
        
        if not conversation:
            is_new_conversation = True
            conversation = {
                "id": str(id),
                "title": None,
                "messages": [],
                "workspace_id": workspace_id,
                "user_id": user_id
            }

        # Add user message to conversation
        conversation["messages"].append({
            "id": str(uuid4()),
            "role": "user",
            "content": message.content
        })

        # Get response from workspace's agent
        full_response = ""
        async for chunk in agent.response(conversation["messages"]):
            full_response += chunk
            yield chunk

        # Generate title for new conversations
        if is_new_conversation:
            conversation["title"] = await self.generate_title(message.content)

        # Add assistant response to conversation
        conversation["messages"].append({
            "id": str(uuid4()),
            "role": "assistant",
            "content": full_response
        })

        # Update conversation in database and cache
        await self._update_conversation(id, conversation, is_new_conversation)

    async def _update_conversation(self, id: UUID, conversation: Dict, is_new_conversation: bool = False):
        """Update or create conversation with workspace information"""
        try:
            if is_new_conversation:
                new_convo = Conversation(
                    id=id,
                    title=conversation["title"],
                    messages=conversation["messages"],
                    workspace_id=conversation["workspace_id"],
                    user_id=conversation["user_id"]
                )
                self.session.add(new_convo)
            else:
                result = await self.session.execute(
                    select(Conversation).where(Conversation.id == id)
                )
                convo = result.scalars().first()
                if convo:
                    convo.messages = conversation["messages"]
                    convo.updated_at = datetime.utcnow()

            await self.session.commit()
            
            # Cache the conversation
            await self.redis.setex(
                f"{id}",
                3600,
                json.dumps(conversation, ensure_ascii=False)
            )
        except Exception as e:
            await self.session.rollback()
            raise e

    async def generate_title(self, content: str):
        messages = [
            {"role": "user", "content": f"Generate a title for the conversation with the following content: {content}"}
        ]
        return await self.llm_handler.generate_response(messages)

    async def delete_all_conversations(self):
        try:
            # Delete all records from conversations table
            await self.session.execute("TRUNCATE TABLE conversations CASCADE")
            # Clear Redis cache
            await self.redis.flushdb()
            await self.session.commit()
            print("Database cleared successfully")
            return {"message": "All conversations deleted successfully"}
        except Exception as e:
            await self.session.rollback()
            print(f"Error clearing database: {str(e)}")
            raise Exception(f"Error deleting conversations: {str(e)}")