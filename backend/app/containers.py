import sys
from pathlib import Path
project_root = Path().resolve()
sys.path.append(str(project_root / 'base'))
sys.path.append(str(project_root / 'retrieval_handler'))
sys.path.append(str(project_root / 'agent'))
sys.path.append(str(project_root / 'voice'))
sys.path.append(str(project_root / 'managers'))

from voice import STT
from dependency_injector import containers, providers
from retrieval_handler.docstore_handler import DocumentStoreHandler
from retrieval_handler.vectorstore_handler import VectorStoreHandler
from retrieval_handler.embedding_handler import OpenAIEmbedder
from retrieval_handler.llm_handler import LLMHandler
from retrieval_handler.reranking_handler import RerankingHandler
from retrieval_handler.retriever_handler import HybridRetriever
from retrieval_handler.rag_handler import RAGHandler
from app.services import ChatService
from app.database import AsyncSessionLocal
from retrieval_handler.reader import UnstructuredReader
from pathlib import Path
from openai import AsyncOpenAI
from managers.agent_manager import AgentManager
from managers.user_manager import UserManager
from managers.workspace_manager import WorkspaceManager
from managers.conversation_manager import ConversationManager

class ServiceProviderImpl:
    """Implementation of the ServiceProvider protocol"""
    def __init__(self, llm_handler, rag_handler, agent_manager, voice_service):
        self._llm_handler = llm_handler
        self._rag_handler = rag_handler
        self._agent_manager = agent_manager
        self._voice_service = voice_service
    
    @property
    def llm_handler(self):
        return self._llm_handler
    
    @property
    def rag_handler(self):
        return self._rag_handler
    
    @property
    def agent_manager(self):
        return self._agent_manager
    
    @property
    def voice_service(self):
        return self._voice_service

class Container(containers.DeclarativeContainer):
    """Main dependency injection container"""
    config = providers.Configuration()

    # Database
    db_session = providers.Singleton(
        AsyncSessionLocal   
    )

    # Utility Services
    document_store = providers.Singleton(
        DocumentStoreHandler,
        uri=config.document_store.uri,
        top_k=config.document_store.top_k
    )
    
    vector_store = providers.Singleton(
        VectorStoreHandler,
        path=config.vector_store.path
    )
    
    embedder = providers.Singleton(
        OpenAIEmbedder,
        api_key=config.embedder.api_key
    )
    
    llm = providers.Singleton(
        LLMHandler,
        api_key=config.llm.api_key,
        model_name=config.llm.model_name
    )
    
    reranking_handler = providers.Singleton(
        RerankingHandler,
        llm=llm
    )
    
    reader = providers.Singleton(
        UnstructuredReader
    )
    
    voice_service_provider = providers.Singleton(
        STT,
        api_key=config.llm.groq_api_key
    )
    
    retriever = providers.Singleton(
        HybridRetriever,
        vector_store=vector_store,
        document_store=document_store,
        embedder=embedder,
        reranker=reranking_handler,
        reader=reader
    )
    
    rag_handler = providers.Singleton(
        RAGHandler,
        retriever=retriever,
        llm=llm
    )

    user_manager = providers.Singleton(
        UserManager,
        db=db_session
    )

    workspace_manager = providers.Singleton(
        WorkspaceManager,
        db=db_session
    )

    agent_manager = providers.Singleton(
        AgentManager,
        db=db_session,
        llm_handler=llm,
        rag_handler=rag_handler
    )

    conversation_manager = providers.Singleton(
        ConversationManager,
        db=db_session,
        redis_url=config.redis.url,
        agent_manager=agent_manager,
        llm_handler=llm
    )


    
    openai_client = providers.Singleton(
        AsyncOpenAI,
        api_key=config.llm.api_key
    )

