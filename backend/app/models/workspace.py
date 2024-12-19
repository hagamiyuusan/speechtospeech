from sqlalchemy import Column, String, DateTime, func, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.database import Base

# Association table for workspace users
workspace_users = Table(
    'workspace_users',
    Base.metadata,
    Column('workspace_id', String, ForeignKey('workspaces.id', ondelete='CASCADE')),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE')),
)

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    document_database_name = Column(String, nullable=True)
    collection_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
    admin_id = Column(String, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)

    # Relationships
    users = relationship("User", 
                        secondary=workspace_users, 
                        back_populates="workspaces",
                        cascade="all, delete")
    admin = relationship("User", 
                        foreign_keys=[admin_id], 
                        backref="admin_workspaces")
    agent = relationship("Agent", 
                        back_populates="workspace", 
                        uselist=False,  # One-to-one relationship
                        cascade="all, delete-orphan")
    conversations = relationship("Conversation",
                               back_populates="workspace",
                               cascade="all, delete-orphan")
