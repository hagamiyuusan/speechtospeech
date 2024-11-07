from abc import ABC, abstractmethod
from .base_retriever import IRetriever
from .basedocument import RetrievedDocument
from typing import List

class IRAGHandler(ABC):
    @abstractmethod
    def __init__(self, retriever: IRetriever):
        pass
    
    @abstractmethod
    def generate_response(self, query: str, top_k: int) ->str:
        pass
