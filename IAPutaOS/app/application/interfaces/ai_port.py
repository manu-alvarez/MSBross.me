from abc import ABC, abstractmethod
from typing import Tuple, Optional

class LLMPort(ABC):
    @abstractmethod
    async def process_chat(self, user_text: str, history: list) -> Tuple[str, Optional[str], str]:
        pass

class AudioPort(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: str) -> str:
        pass
        
    @abstractmethod
    async def generate_speech(self, text: str) -> str:
        pass
