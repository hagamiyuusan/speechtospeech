
from abc import ABC, abstractmethod
from .basedocument import Document

class IEmbedder(ABC):
    
    @abstractmethod
    def fetch_embeddings(self, tokenized : str | list[str] | Document | list[Document]):
        pass