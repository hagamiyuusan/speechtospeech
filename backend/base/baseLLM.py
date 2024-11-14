from abc import ABC, abstractmethod

class BaseLLM(ABC):
    
    @abstractmethod
    def generate_response(self, messages: list[dict] | str, tools: list = None, function_map : dict = None) -> str:
        pass
    
    @abstractmethod
    def stream_response(self, messages: list[dict] | str, tools: list = None, function_map : dict = None) -> str:
        pass