# from sqlalchemy import Column, String, Integer, JSON
# from .database import Base

# class ChatLog(Base):
#     """
#     SQLAlchemy model for storing chat logs.
#     """
#     __tablename__ = "chatlogs"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(String, unique=True, index=True, nullable=False)
#     history = Column(JSON, nullable=False)

from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableList

import uuid
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    messages = Column(MutableList.as_mutable(JSONB), nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

