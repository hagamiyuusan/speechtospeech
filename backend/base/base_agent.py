
from abc import ABC, abstractmethod
from typing import List
from base import RetrievedDocument, BaseLLM

class IAgent(ABC):
    @abstractmethod
    def __init__(self, llm: BaseLLM):
        pass

    @abstractmethod
    def response(self, messages: List[dict]) -> str:
        pass

