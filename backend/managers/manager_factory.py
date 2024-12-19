from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Protocol
from .user_manager import UserManager
from .workspace_manager import WorkspaceManager
from .conversation_manager import ConversationManager
from .agent_manager import AgentManager
from agent.main_agent import AgentFactory

class ServiceProvider(Protocol):
    """Protocol defining the interface for accessing utility services"""
    @property
    def llm_handler(self): pass
    
    @property
    def rag_handler(self): pass
    
    @property
    def agent_factory(self): pass

    @property
    def voice_service(self):
        pass

class ManagerFactory:
    """Factory class to create and manage different manager instances"""
    
    def __init__(self, db: AsyncSession, service_provider: ServiceProvider):
        self.db = db
        self.service_provider = service_provider
        self._user_manager: Optional[UserManager] = None
        self._workspace_manager: Optional[WorkspaceManager] = None
        self._conversation_manager: Optional[ConversationManager] = None
        self._agent_manager: Optional[AgentManager] = None
    
    @property
    def user_manager(self) -> UserManager:
        """Get or create UserManager instance"""
        if not self._user_manager:
            self._user_manager = UserManager(self.db)
        return self._user_manager
    
    @property
    def workspace_manager(self) -> WorkspaceManager:
        """Get or create WorkspaceManager instance"""
        if not self._workspace_manager:
            self._workspace_manager = WorkspaceManager(self.db)
        return self._workspace_manager
    
    @property
    def conversation_manager(self) -> ConversationManager:
        """Get or create ConversationManager instance"""
        if not self._conversation_manager:
            self._conversation_manager = ConversationManager(self.db)
        return self._conversation_manager
        
    @property
    def agent_manager(self) -> AgentManager:
        """Get or create AgentManager instance"""
        if not self._agent_manager:
            self._agent_manager = AgentManager(
                db=self.db,
                agent_factory=self.service_provider.agent_factory
            )
        return self._agent_manager 