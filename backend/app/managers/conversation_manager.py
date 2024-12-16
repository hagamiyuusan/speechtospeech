from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from .base_manager import BaseManager
from app.models.conversation import Conversation

class ConversationManager(BaseManager[Conversation]):
    def __init__(self, db: Session):
        super().__init__(db, Conversation)
    
    async def create_conversation(self, user_id: str, title: str) -> Conversation:
        """Create a new conversation for a user"""
        try:
            conversation_data = {
                "user_id": user_id,
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
            
            conversation.messages.append(message)
            conversation.modified_at = func.now()
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_user_conversations(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Conversation]:
        """Get all conversations for a user with pagination"""
        try:
            return await self.db.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .order_by(Conversation.modified_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def clear_conversation(self, conversation_id: str) -> Conversation:
        """Clear all messages from a conversation"""
        try:
            conversation = await self.get(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            conversation.messages = []
            conversation.modified_at = func.now()
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
            
            messages = conversation.messages
            if before_id:
                # Find the index of the message with before_id
                for i, msg in enumerate(messages):
                    if msg.get('id') == before_id:
                        messages = messages[:i]
                        break
            
            return messages[-limit:] if limit else messages
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e)) 