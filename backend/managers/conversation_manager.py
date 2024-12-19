from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func
from fastapi import HTTPException
from .base_manager import BaseManager
from app.models.conversation import Conversation
from .agent_manager import AgentManager
from base import BaseLLM
from redis import asyncio as aioredis
from app.models import Workspace, User
from uuid import UUID
from datetime import datetime
from typing import Dict
from app.schema import Message
import json
from sqlalchemy import and_
from uuid import uuid4

class ConversationManager(BaseManager[Conversation]):
    def __init__(self, db: AsyncSession, redis_url : str, agent_manager: AgentManager, llm_handler: BaseLLM):
        super().__init__(db, Conversation)
        self.redis = aioredis.from_url(redis_url)
        self.agent_manager = agent_manager
        self.llm_handler = llm_handler
        
    
    async def create_conversation(self, user_id: str, workspace_id: str, title: str) -> Conversation:
        """Create a new conversation for a user"""
        try:
            conversation_data = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "title": title,
                "messages": []
            }
            return await self.create(conversation_data)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def add_message(self, conversation_id: str, message: dict) -> Conversation:
        """Add a message to a conversation"""
        try:
            conversation = await self.get(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            if conversation.messages is None:
                conversation.messages = []
            
            conversation.messages.append(message)
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_user_conversations(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Conversation]:
        """Get all conversations for a user with pagination"""
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.modified_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def clear_conversation(self, conversation_id: str) -> Conversation:
        """Clear all messages from a conversation"""
        try:
            conversation = await self.get(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            conversation.messages = []
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_conversation_messages(self, conversation_id: str, limit: int = 50, before_id: Optional[str] = None) -> List[dict]:
        """Get messages from a conversation with pagination"""
        try:
            conversation = await self.get(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            messages = conversation.messages or []
            if before_id:
                # Find the index of the message with before_id
                for i, msg in enumerate(messages):
                    if msg.get('id') == before_id:
                        messages = messages[:i]
                        break
            
            return messages[-limit:] if limit else messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e)) 

    async def get_user_workspace(self, user_id: str, workspace_id: str) -> Optional[Workspace]:
        """Get workspace if user has access to it"""
        query = select(Workspace).join(Workspace.users).where(
            and_(Workspace.id == workspace_id, User.id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def load_conversation(self, id: UUID, user_id: str):
        """Load a conversation with caching and workspace access check"""
        # Try cache first
        cached_convo = await self.redis.get(f"{id}")
        if cached_convo:
            convo_data = json.loads(cached_convo)
            # Verify user has access
            workspace = await self.get_user_workspace(user_id, convo_data.get('workspace_id'))
            if not workspace:
                raise HTTPException(status_code=403, detail="Access denied to this conversation")
            return convo_data

        # If not in cache, get from database
        conversation = await self.get(str(id))
        if not conversation:
            return None

        # Verify workspace access
        workspace = await self.get_user_workspace(user_id, conversation.workspace_id)
        if not workspace:
            raise HTTPException(status_code=403, detail="Access denied to this conversation")

        # Cache the conversation
        serialized_convo = {
            "id": str(conversation.id),
            "title": conversation.title,
            "messages": conversation.messages,
            "workspace_id": conversation.workspace_id,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        }
        await self.redis.setex(f"{id}", 3600, json.dumps(serialized_convo, ensure_ascii=False))
        return serialized_convo

    async def chat_response(self, id: UUID, message: Message, user_id: str, workspace_id: str):
        """Generate chat response using workspace's agent"""
        # Verify workspace access
        workspace = await self.get_user_workspace(user_id, workspace_id)
        if not workspace:
            raise HTTPException(status_code=403, detail="Access denied to this workspace")

        # Get workspace's agent
        agent = await self.agent_manager.get_agent(workspace_id)
        if not agent:
            raise HTTPException(status_code=404, detail="No agent found for this workspace")

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
        """
        Update or create conversation with workspace information
        
        Args:
            id (UUID): Conversation ID
            conversation (Dict): Conversation data including messages and metadata
            is_new_conversation (bool): Flag indicating if this is a new conversation
        
        Raises:
            HTTPException: If database operation fails
        """
        try:
            if is_new_conversation:
                new_convo = Conversation(
                    id=id,
                    title=conversation["title"],
                    messages=conversation["messages"],
                    workspace_id=conversation["workspace_id"],
                    user_id=conversation["user_id"]
                )
                self.db.add(new_convo)
            else:
                # Get existing conversation
                stmt = select(Conversation).where(Conversation.id == id)
                result = await self.db.execute(stmt)
                convo = result.scalars().first()
                
                if not convo:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Conversation {id} not found"
                    )
                
                # Update fields
                convo.messages = conversation["messages"]
                if "title" in conversation:
                    convo.title = conversation["title"]
                convo.modified_at = datetime.utcnow()

            # Commit changes
            await self.db.commit()
            
            # Update cache with new data
            cache_data = {
                "id": str(id),
                "title": conversation["title"],
                "messages": conversation["messages"],
                "workspace_id": conversation["workspace_id"],
                "created_at": conversation.get("created_at"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Set cache with expiration
            await self.redis.setex(
                f"{id}",
                3600,  # 1 hour expiration
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            return cache_data

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error updating conversation: {str(e)}"
            )
    async def generate_title(self, content: str):
        messages = [
            {"role": "user", "content": f"Generate a title for the conversation with the following content: {content}"}
        ]
        return await self.llm_handler.generate_response(messages)