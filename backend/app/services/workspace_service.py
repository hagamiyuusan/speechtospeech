from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Workspace
from agent.main_agent import MainAgent

class WorkspaceService:
    def __init__(self, session: AsyncSession, document_store, vector_store, 
                 embedder, llm, reranking_handler, reader, workspace_manager):
        self.session = session
        self.document_store = document_store
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm
        self.reranking_handler = reranking_handler
        self.reader = reader
        self.workspace_manager = workspace_manager
        # Set this service in workspace manager for circular reference
        self.workspace_manager.set_workspace_service(self)

    async def create_workspace(self, name: str) -> Workspace:
        workspace = Workspace(
            name=name,
            collection_name=f"workspace_{str(uuid4())}"
        )
        self.session.add(workspace)
        await self.session.commit()
        return workspace

    def create_agent(self, collection_name: str) -> MainAgent:
        retriever = HybridRetriever(
            vector_store=self.vector_store,
            document_store=self.document_store,
            embedder=self.embedder,
            reranker=self.reranking_handler,
            reader=self.reader
        )
        rag_handler = RAGHandler(retriever=retriever, llm=self.llm)
        return MainAgent(llm_handler=self.llm, rag_handler=rag_handler)

    async def get_workspace(self, workspace_id: str) -> Workspace:
        return await self.session.get(Workspace, workspace_id)

    async def list_workspaces(self) -> List[Workspace]:
        result = await self.session.execute(select(Workspace))
        return result.scalars().all()