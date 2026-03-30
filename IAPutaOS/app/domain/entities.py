from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel

class UserMessage(BaseModel):
    text: str
    
class AIResponse(BaseModel):
    transcript: str
    response: str
    audio_url: Optional[str] = None
    vision_url: Optional[str] = None
    emotion: str = "neutral"
