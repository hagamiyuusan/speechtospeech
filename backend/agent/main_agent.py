import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from base import IRAGHandler, BaseLLM, IAgent
from typing import List, Dict, Any, Optional
from dependency_injector.wiring import inject, Provide
from uuid import uuid4
from schemas import Message

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
        super().__init__(agent_config)
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self.agent_functions = self._initialize_functions()
        self.tools = self._initialize_tools()
        
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
        messages_dicts = self._prepare_messages(messages)
        return self.llm_handler.stream_response(
            messages=messages_dicts,
            tools=self.tools,
            function_map=self.agent_functions,
        )

class AgentFactory:
    """Factory for creating and managing agent instances"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        
    @inject
    def create_agent(self, 
                    agent_config: Dict[str, Any], 
                    agent_type: str = "rag",
                    llm_handler: Optional[BaseLLM] = None, 
                    rag_handler: Optional[IRAGHandler] = None) -> BaseAgent:
        """
        Create or retrieve an agent instance
        
        Args:
            agent_config: Configuration dictionary for the agent
            agent_type: Type of agent to create ("rag", "chat", etc.)
            llm_handler: Language model handler
            rag_handler: RAG handler for retrieval operations
            
        Returns:
            BaseAgent: An instance of the appropriate agent type
        """
        workspace_id = agent_config['workspace_id']
        
        if workspace_id in self._agents:
            return self._agents[workspace_id]
            
        agent: BaseAgent
        if agent_type == "rag":
            agent = RAGAgent(
                agent_config=agent_config,
                llm_handler=llm_handler,
                rag_handler=rag_handler
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        self._agents[workspace_id] = agent
        return agent
        
    def get_agent(self, workspace_id: str) -> Optional[BaseAgent]:
        """Retrieve an existing agent instance"""
        return self._agents.get(workspace_id)
        
    def remove_agent(self, workspace_id: str) -> None:
        """Remove an agent instance"""
        if workspace_id in self._agents:
            del self._agents[workspace_id]




