from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Conversation
import uuid

class ChatService:
    def __init__(self, session: AsyncSession, main_agent):
        self.session = session
        self.main_agent = main_agent

    async def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalars().first()

    async def create_conversation(self, title: str, message: Dict) -> Conversation:
        conversation = Conversation(
            title=title,
            messages=[message]
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation 