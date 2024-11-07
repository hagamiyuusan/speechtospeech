import sys
from pathlib import Path
project_root = Path().resolve()
sys.path.append(str(project_root / 'base'))
sys.path.append(str(project_root / 'retrieval_handler'))
sys.path.append(str(project_root / 'agent'))

from dependency_injector import containers, providers
from retrieval_handler.docstore_handler import DocumentStoreHandler
from retrieval_handler.vectorstore_handler import VectorStoreHandler
from retrieval_handler.embedding_handler import OpenAIEmbedder
from retrieval_handler.llm_handler import LLMHandler
from retrieval_handler.reranking_handler import RerankingHandler
from retrieval_handler.retriever_handler import HybridRetriever
from retrieval_handler.rag_handler import RAGHandler
from agent.main_agent import MainAgent
from app.services import ChatService
from app.database import AsyncSessionLocal
from retrieval_handler.reader import UnstructuredReader
from pathlib import Path
from openai import AsyncOpenAI
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    db_session = providers.Singleton(
        AsyncSessionLocal
    )

    document_store = providers.Singleton(
        DocumentStoreHandler,
        uri = config.document_store.uri,
        table_name=config.document_store.table_name,
        top_k=config.document_store.top_k)
    
    vector_store = providers.Singleton(
        VectorStoreHandler,
        collection_name=config.vector_store.collection_name,
        path = config.vector_store.path
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
    main_agent = providers.Factory(
        MainAgent,
        llm_handler=llm,
        rag_handler = rag_handler
    )
    chat_service = providers.Singleton(
        ChatService,
        redis_url=config.redis.url,
        session=db_session,
        agent=main_agent
    )
    openai_client = providers.Singleton(
        AsyncOpenAI,
        api_key=config.llm.api_key
    )


