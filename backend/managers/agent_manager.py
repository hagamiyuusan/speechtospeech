import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy import select
import pickle
from redis import asyncio as aioredis
from .base_manager import BaseManager
from app.models.agent import Agent
from agent.main_agent import BaseAgent
from base import BaseLLM, IRAGHandler
from agent import RAGAgent

AGENT_TTL = 3600  # 1 hour TTL for inactive agents

class AgentManager(BaseManager[Agent]):
    """
    Manages the lifecycle and state of AI agents in the application.
    Handles both database persistence and runtime agent instances using Redis.
    """
    def __init__(self, 
                 db: AsyncSession, 
                 llm_handler: BaseLLM, 
                 rag_handler: IRAGHandler,
                 redis_url: str = "redis://localhost"):
        super().__init__(db, Agent)
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self.redis = aioredis.from_url(redis_url, decode_responses=False)

    def _create_agent(self, config: Dict[str, Any]) -> BaseAgent:
        """Internal method to create agent instances"""
        return RAGAgent(
            agent_config=config,
            llm_handler=self.llm_handler,
            rag_handler=self.rag_handler
        )

    def _get_default_config(self, workspace_id: str) -> Dict[str, Any]:
        """Get default configuration for a new agent"""
        return {
            "workspace_id": workspace_id,
            "name": "Default Agent",
            "system_prompt": "You are a helpful AI assistant focused on ASEAN topics.",
            "tools_config": {
                "rag_table": "default",
                "model_name": "gpt-4"
            }
        }

    async def _get_runtime_agent(self, workspace_id: str) -> Optional[BaseAgent]:
        """Get agent from Redis cache"""
        try:
            pickled_agent = await self.redis.get(f"agent:{workspace_id}")
            if pickled_agent:
                # Reset TTL when accessed
                await self.redis.expire(f"agent:{workspace_id}", AGENT_TTL)
                return pickle.loads(pickled_agent)
        except Exception as e:
            print(f"Error retrieving agent from Redis: {e}")
        return None

    async def _set_runtime_agent(self, workspace_id: str, agent: BaseAgent):
        """Store agent in Redis cache with TTL"""
        try:
            pickled_agent = pickle.dumps(agent)
            await self.redis.set(f"agent:{workspace_id}", pickled_agent, ex=AGENT_TTL)
        except Exception as e:
            print(f"Error storing agent in Redis: {e}")

    async def create_agent(
        self,
        workspace_id: str,
        agent_config: Dict[str, Any],
        agent_type: str = "rag"
    ) -> BaseAgent:
        """Creates a new agent for the given workspace, both in database and Redis cache."""
        try:
            # Check Redis cache first
            runtime_agent = await self._get_runtime_agent(workspace_id)
            if runtime_agent:
                return runtime_agent
            
            # Create database record
            agent_data = {
                "workspace_id": workspace_id,
                "name": agent_config.get("name", "Default Agent"),
                "system_prompt": agent_config.get("system_prompt", ""),
                "tools_config": agent_config.get("tools_config", {}),
                "metadata_": agent_config.get("metadata", {})
            }
            
            db_agent = await self.create(agent_data)
            
            # Create runtime agent using factory
            runtime_agent = self._create_agent(
                config={**agent_data, "id": db_agent.id},
                
            )
            
            # Store in Redis
            await self._set_runtime_agent(workspace_id, runtime_agent)
            return runtime_agent
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def get_agent(
        self, 
        workspace_id: str
    ) -> Optional[BaseAgent]:
        """
        Retrieves an existing agent for the given workspace.
        If the agent exists in database but not in Redis, creates the runtime instance.
        """
        try:
            # Check Redis cache first
            runtime_agent = await self._get_runtime_agent(workspace_id)
            if runtime_agent:
                return runtime_agent
            
            # Get from database using async session
            result = await self.db.execute(
                select(Agent).where(Agent.workspace_id == workspace_id)
            )
            db_agent = result.scalars().first()
            
            if not db_agent:
                # Create a default agent if none exists
                agent_config = self._get_default_config(workspace_id)
                runtime_agent = self._create_agent(
                    config=agent_config,
                )
                await self._set_runtime_agent(workspace_id, runtime_agent)
                return runtime_agent

            # Initialize runtime agent using factory
            agent_config = {
                "id": db_agent.id,
                "name": db_agent.name,
                "system_prompt": db_agent.system_prompt,
                "tools_config": db_agent.tools_config,
                "workspace_id": db_agent.workspace_id,
                "metadata": db_agent.metadata_
            }
            
            runtime_agent = self._create_agent(
                config=agent_config
            )
            
            await self._set_runtime_agent(workspace_id, runtime_agent)
            return runtime_agent
            
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def update_agent(
        self, 
        workspace_id: str, 
        agent_data: dict
    ) -> Optional[BaseAgent]:
        """Updates an existing agent's configuration."""
        try:
            # Update database record
            db_agent = await self.db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
            if not db_agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            for key, value in agent_data.items():
                if hasattr(db_agent, key):
                    setattr(db_agent, key, value)
            
            await self.db.commit()
            await self.db.refresh(db_agent)
            
            # Remove existing runtime agent from Redis
            await self.redis.delete(f"agent:{workspace_id}")
            
            # Return newly initialized agent
            return await self.get_agent(workspace_id)
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_agent(self, workspace_id: str) -> bool:
        """Removes an agent from both database and Redis cache."""
        try:
            # Remove from database
            db_agent = await self.db.query(Agent).filter(Agent.workspace_id == workspace_id).first()
            if db_agent:
                await self.db.delete(db_agent)
                await self.db.commit()
            
            # Remove from Redis cache
            await self.redis.delete(f"agent:{workspace_id}")
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    async def get_all_agents(self) -> List[Agent]:
        """Returns all agents from the database."""
        try:
            return await self.db.query(Agent).all()
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def clear_runtime_agents(self) -> None:
        """Clears all runtime agent instances from Redis."""
        try:
            # Get all agent keys
            keys = await self.redis.keys("agent:*")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            print(f"Error clearing runtime agents from Redis: {e}")