import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from fastapi import UploadFile

class IVoice(ABC):
    @abstractmethod
    def generate_audio(self, file: UploadFile) -> bytes:
        pass
