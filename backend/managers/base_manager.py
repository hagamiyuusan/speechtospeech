from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

T = TypeVar('T')

class BaseManager(Generic[T]):
    """Base manager class with common CRUD operations"""
    
    def __init__(self, db: AsyncSession, model: T):
        self.db = db
        self.model = model
    
    async def create(self, data: dict) -> T:
        try:
            instance = self.model(**data)
            self.db.add(instance)
            await self.db.commit()
            await self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get(self, id: str | UUID) -> Optional[T]:
        try:
            # Convert UUID to string if necessary
            if isinstance(id, UUID):
                id = str(id)
                
            stmt = select(self.model).where(self.model.id == id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_all(self, **filters) -> List[T]:
        try:
            stmt = select(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    # Convert UUID to string if necessary
                    if isinstance(value, UUID):
                        value = str(value)
                    stmt = stmt.where(getattr(self.model, key) == value)
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def update(self, id: str | UUID, data: dict) -> Optional[T]:
        try:
            # Convert UUID to string if necessary
            if isinstance(id, UUID):
                id = str(id)
                
            instance = await self.get(id)
            if not instance:
                raise HTTPException(status_code=404, detail="Item not found")
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            await self.db.commit()
            await self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def delete(self, id: str | UUID) -> bool:
        try:
            # Convert UUID to string if necessary
            if isinstance(id, UUID):
                id = str(id)
                
            instance = await self.get(id)
            if not instance:
                raise HTTPException(status_code=404, detail="Item not found")
            
            await self.db.delete(instance)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 