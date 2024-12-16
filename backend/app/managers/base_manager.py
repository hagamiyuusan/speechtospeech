from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

T = TypeVar('T')

class BaseManager(Generic[T]):
    """Base manager class with common CRUD operations"""
    
    def __init__(self, db: Session, model: T):
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
    
    async def get(self, id: str) -> Optional[T]:
        try:
            return await self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_all(self, **filters) -> List[T]:
        try:
            query = self.db.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return await query.all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async def update(self, id: str, data: dict) -> Optional[T]:
        try:
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
    
    async def delete(self, id: str) -> bool:
        try:
            instance = await self.get(id)
            if not instance:
                raise HTTPException(status_code=404, detail="Item not found")
            
            await self.db.delete(instance)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 