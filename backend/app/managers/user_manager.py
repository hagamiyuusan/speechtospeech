from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from .base_manager import BaseManager
from app.models.user import User
from app.security import get_password_hash, verify_password

class UserManager(BaseManager[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    async def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user with hashed password"""
        try:
            # Check if user already exists
            existing_user = await self.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username or email already registered"
                )
            
            hashed_password = get_password_hash(password)
            user_data = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password
            }
            
            return await self.create(user_data)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        try:
            user = await self.db.query(User).filter(User.username == username).first()
            if not user or not verify_password(password, user.hashed_password):
                return None
            return user
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_user_workspaces(self, user_id: str) -> List[dict]:
        """Get all workspaces for a user"""
        try:
            user = await self.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
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