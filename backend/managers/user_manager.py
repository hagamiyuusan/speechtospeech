from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from .base_manager import BaseManager
from app.models.user import User
from uuid import UUID

class UserManager(BaseManager[User]):
    """Manages user operations without security features (MVP version)"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def create_user(self, username: str, email: str) -> User:
        """Create a new user without password"""
        try:
            # Check if user already exists
            stmt = select(User).where(
                (User.username == username) | (User.email == email)
            )
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username or email already registered"
                )
            
            user_data = {
                "username": username,
                "email": email,
                "is_active": True
            }
            
            return await self.create(user_data)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_user_workspaces(self, user_id: str | UUID) -> List[dict]:
        """Get all workspaces for a user"""
        try:
            # Convert UUID to string if necessary
            if isinstance(user_id, UUID):
                user_id = str(user_id)
                
            user = await self.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Load workspaces relationship
            stmt = select(User).where(User.id == user_id).options(
                selectinload(User.workspaces)
            )
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            return [
                {
                    "id": workspace.id,
                    "name": workspace.name,
                    "is_admin": workspace.admin_id == user_id
                }
                for workspace in user.workspaces
            ]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e)) 