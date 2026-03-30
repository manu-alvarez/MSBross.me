"""
Centralized Groq client singleton.
All modules must import from here instead of creating their own instances.
"""

from groq import AsyncGroq
from app.core.config import settings

groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
