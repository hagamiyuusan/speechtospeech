from sqlalchemy.orm import Session
from typing import Optional
from .user_manager import UserManager
from .workspace_manager import WorkspaceManager
from .conversation_manager import ConversationManager

class ManagerFactory:
    """Factory class to create and manage different manager instances"""
    
    def __init__(self, db: Session):
        self.db = db
        self._user_manager: Optional[UserManager] = None
        self._workspace_manager: Optional[WorkspaceManager] = None
        self._conversation_manager: Optional[ConversationManager] = None
    
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