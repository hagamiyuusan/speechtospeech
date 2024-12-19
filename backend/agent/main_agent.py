import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from base import IRAGHandler, BaseLLM, IAgent
from app.models import Agent
from typing import List, Dict, Any, Optional
from dependency_injector.wiring import inject, Provide
from uuid import uuid4
from schemas import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class BaseAgent(IAgent, ABC):
    """Base agent class that defines common functionality"""
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.agent_id = agent_config.get('id')
        self.name = agent_config.get('name', 'Default Agent')
        self.system_prompt = agent_config.get('system_prompt', '')
        self.tools_config = agent_config.get('tools_config', {})
        self.workspace_id = agent_config.get('workspace_id')
        
    @abstractmethod
    def _initialize_functions(self) -> Dict[str, callable]:
        """Initialize agent functions - must be implemented by subclasses"""
        pass
        
    @abstractmethod
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize tools - must be implemented by subclasses"""
        pass
        
    def _prepare_messages(self, messages: List[dict]) -> List[Dict[str, str]]:
        """Prepare messages for the agent including system prompt"""
        message_objects = []
        for msg in messages:
            if isinstance(msg, dict):
                if 'id' not in msg:
                    msg['id'] = str(uuid4())
                message_objects.append(Message(**msg))
            else:
                message_objects.append(msg)
                
        if not message_objects or message_objects[0].role != "system":
            message_objects.insert(0, Message(
                id=str(uuid4()),
                role="system",
                content=self.system_prompt
            ))
            
        return [{"role": msg.role, "content": msg.content} for msg in message_objects]

class RAGAgent(BaseAgent):
    """Agent specialized in RAG (Retrieval Augmented Generation) operations"""
    
    @inject
    def __init__(self, agent_config: Dict[str, Any], 
                 llm_handler: BaseLLM = None, 
                 rag_handler: IRAGHandler = None):
        super().__init__(agent_config or {})
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self.agent_functions = None
        self.tools = None
        self.tools_config = self.tools_config or {}
        
    def _initialize_functions(self) -> Dict[str, callable]:
        return {
            "rag_handler": lambda query: self.rag_handler.generate_response(
                table_name=self.tools_config.get('rag_table', 'default'),
                query=query,
                model_name=self.tools_config.get('model_name', 'gpt-4')
            )
        }
        
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                'type': 'function',
                'function': {
                    'name': 'rag_handler',
                    'description': self.tools_config.get('rag_description', 
                        "Use this tool to retrieve and generate responses based on the knowledge base"),
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': "The query to process"
                            }
                        },
                        'required': ['query']
                    }
                }
            }
        ]
        
    async def response(self, messages: List[dict]):
        if not self.agent_functions:
            self.agent_functions = self._initialize_functions()
        if not self.tools:
            self.tools = self._initialize_tools()
            
        messages_dicts = self._prepare_messages(messages)
        response_stream = self.llm_handler.stream_response(
            messages=messages_dicts,
            tools=self.tools,
            function_map=self.agent_functions,
        )
        
        # Collect the complete response
        full_response = ""
        async for chunk in response_stream:
            full_response += chunk
            yield chunk
            
        # Store the full response in the instance for later use if needed
        self.last_full_response = full_response

class AgentFactory:
    """Combined factory and manager for agents"""
    def __init__(self, db: AsyncSession, llm_handler: BaseLLM, rag_handler: IRAGHandler):
        self.db = db
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self._runtime_agents: Dict[str, BaseAgent] = {}
    
    def _get_default_config(self, workspace_id: str) -> Dict[str, Any]:
        """Get default configuration for a new agent"""
        return {
            "workspace_id": workspace_id,
            "name": "Default Agent",
            "system_prompt": "You are a helpful AI assistant focused on ASEAN topics.",
            "tools_config": {
                "rag_table": "default",
                "model_name": "gpt-4",
                "rag_description": "Use this tool to retrieve and generate responses based on the knowledge base"
            }
        }
    
    async def get_or_create_agent(self, workspace_id: str) -> BaseAgent:
        """Get existing agent or create new one"""
        # Check runtime cache
        if workspace_id in self._runtime_agents:
            return self._runtime_agents[workspace_id]
        
        # Check database
        result = await self.db.execute(
            select(Agent).where(Agent.workspace_id == workspace_id)
        )
        db_agent = result.scalars().first()
        
        if not db_agent:
            # Create new agent with default config
            agent_config = self._get_default_config(workspace_id)
            agent = self._create_agent(agent_config)
            self._runtime_agents[workspace_id] = agent
            return agent
        
        # Create runtime agent from DB config
        agent_config = {
            "id": db_agent.id,
            "name": db_agent.name,
            "system_prompt": db_agent.system_prompt,
            "tools_config": db_agent.tools_config or {},  # Ensure tools_config is not None
            "workspace_id": db_agent.workspace_id
        }
        agent = self._create_agent(agent_config)
        self._runtime_agents[workspace_id] = agent
        return agent
    
    def _create_agent(self, config: Dict[str, Any]) -> BaseAgent:
        """Create new agent instance"""
        return RAGAgent(
            agent_config=config,
            llm_handler=self.llm_handler,
            rag_handler=self.rag_handler
        )




