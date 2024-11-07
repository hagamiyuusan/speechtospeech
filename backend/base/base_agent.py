
from abc import ABC, abstractmethod
from typing import List
from base import RetrievedDocument, BaseLLM

class IAgent(ABC):
    @abstractmethod
    def __init__(self, llm: BaseLLM):
        pass

    @abstractmethod
    def handle_query(self, query: str) -> str:
        pass

