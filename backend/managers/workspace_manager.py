from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from .base_manager import BaseManager
from app.models.workspace import Workspace
from app.models.agent import Agent

class WorkspaceManager(BaseManager[Workspace]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Workspace)
    
    async def create_workspace(self, name: str, admin_id: str, collection_name: str) -> Workspace:
        """Create a new workspace with admin user"""
        try:
            workspace_data = {
                "name": name,
                "admin_id": admin_id,
                "collection_name": collection_name
            }
            
            workspace = await self.create(workspace_data)
            
            # Add admin user to workspace users
            workspace.users.append(await self.db.query(User).get(admin_id))
            await self.db.commit()
            
            return workspace
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def add_user_to_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Add a user to a workspace"""
        try:
            workspace = await self.get(workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            
            user = await self.db.query(User).get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user in workspace.users:
                raise HTTPException(status_code=400, detail="User already in workspace")
            
            workspace.users.append(user)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def remove_user_from_workspace(self, workspace_id: str, user_id: str) -> bool:
        """Remove a user from a workspace"""
        try:
            workspace = await self.get(workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            
            if workspace.admin_id == user_id:
                raise HTTPException(status_code=400, detail="Cannot remove workspace admin")
            
            user = await self.db.query(User).get(user_id)
            if not user or user not in workspace.users:
                raise HTTPException(status_code=404, detail="User not found in workspace")
            
            workspace.users.remove(user)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_workspace_agent(self, workspace_id: str) -> Optional[Agent]:
        """Get the agent associated with a workspace"""
        try:
            workspace = await self.get(workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            
            return workspace.agent
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def update_workspace_agent(self, workspace_id: str, agent_data: dict) -> Agent:
        """Update or create the agent for a workspace"""
        try:
            workspace = await self.get(workspace_id)
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            
            if workspace.agent:
                # Update existing agent
                for key, value in agent_data.items():
                    setattr(workspace.agent, key, value)
            else:
                # Create new agent
                agent = Agent(workspace_id=workspace_id, **agent_data)
                self.db.add(agent)
            
            await self.db.commit()
            return workspace.agent
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 