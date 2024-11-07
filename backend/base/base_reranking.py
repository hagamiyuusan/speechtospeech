from abc import ABC, abstractmethod
from typing import List
from base import RetrievedDocument, BaseLLM

class IRerankingHandler(ABC):
    @abstractmethod
    def __init__(self, llm: BaseLLM):

        pass

    @abstractmethod
    def rerank_documents(self, query: str, documents: List[RetrievedDocument]) -> List[RetrievedDocument]:

        pass
