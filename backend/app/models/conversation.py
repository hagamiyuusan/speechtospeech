# backend/app/models/user.py
from sqlalchemy import Column, String, DateTime, func
from uuid import uuid4
from app.database import Base

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)  # Add this line
    title = Column(String(255), nullable=False)
    messages = Column(MutableList.as_mutable(JSONB), nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Add relationship
    user = relationship("User", back_populates="conversations")