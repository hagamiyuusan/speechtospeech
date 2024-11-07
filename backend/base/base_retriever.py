import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from base import BaseLLM, RetrievedDocument, IVectorStore, IDocumentStore, IEmbedder, IRerankingHandler, Document
from typing import List


class IRetriever(ABC):
    @abstractmethod
    def __init__(self, vector_store: IVectorStore, document_store: IDocumentStore, embedder: IEmbedder, reranker: IRerankingHandler):
        pass
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> List[RetrievedDocument]:
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Document]):
        pass
