# backend/agent/agent_manager.py
from typing import Dict
from .main_agent import MainAgent

class AgentManager:
    def __init__(self):
        self._user_agents: Dict[str, MainAgent] = {}
    
    async def get_agent(self, user_id: str, agent_factory) -> MainAgent:
        """Get or create an agent for a specific user"""
        if user_id not in self._user_agents:
            self._user_agents[user_id] = agent_factory()
        return self._user_agents[user_id]
    
    def remove_agent(self, user_id: str):
        """Remove an agent for a specific user"""
        if user_id in self._user_agents:
            del self._user_agents[user_id]
    
    