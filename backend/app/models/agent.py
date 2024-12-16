# backend/app/models/user.py
from sqlalchemy import Column, String, DateTime, func, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.database import Base

class Agents(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    system_prompt = Column(String, nullable=False)
    tools_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    workspace = relationship("Workspace", back_populates="agent")
    