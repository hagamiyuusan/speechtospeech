from typing import Dict
from agent.main_agent import MainAgent
from .workspace_service import WorkspaceService

class WorkspaceManager:
    def __init__(self):
        self._workspace_agents: Dict[str, MainAgent] = {}
        self._workspace_service: WorkspaceService | None = None
    
    def set_workspace_service(self, service: WorkspaceService):
        self._workspace_service = service
    
    async def get_agent(self, workspace_id: str) -> MainAgent:
        if workspace_id not in self._workspace_agents:
            # Get workspace details from service
            workspace = await self._workspace_service.get_workspace(workspace_id)
            if not workspace:
                raise ValueError(f"Workspace {workspace_id} not found")
            
            # Create new agent instance for this workspace
            self._workspace_agents[workspace_id] = self._workspace_service.create_agent(
                workspace.collection_name
            )
        
        return self._workspace_agents[workspace_id]
    


    
    def remove_agent(self, workspace_id: str):
        if workspace_id in self._workspace_agents:
            del self._workspace_agents[workspace_id]