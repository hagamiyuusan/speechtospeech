import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from base import Document
from typing import List

class IDocumentStore(ABC):
    @abstractmethod
    def query(self, query: str, top_k: int) -> List[Document]:
        pass

    @abstractmethod
    def add_documents(self, documents: List[Document]):
        pass
    
    @abstractmethod
    def get_document(self, doc_ids: str) -> List[Document]:
        pass