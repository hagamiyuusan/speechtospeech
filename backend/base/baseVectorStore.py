from abc import ABC, abstractmethod
from .basedocument import  Document, DocumentWithEmbedding
from typing import List

class IVectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List[DocumentWithEmbedding]):
        pass
    
    @abstractmethod
    def query(self, query_embedding, top_k: int):
        pass