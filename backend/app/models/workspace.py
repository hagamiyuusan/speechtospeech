from sqlalchemy import Column, String, DateTime, func
from uuid import uuid4
from app.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    document_database_name = Column(String, nullable = True)
    collection_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now()) 
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)
    users = relationship("User", secondary="workspace_users", back_populates="workspaces")
    admin = relationship("User", foreign_keys=[admin_id], backref="admin_workspaces")
    agent = relationship("Agent", back_populates="workspace")
