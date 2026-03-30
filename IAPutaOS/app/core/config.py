import os
import platform
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# Check if running in Docker using environment variable
IN_DOCKER = os.environ.get("RUNNING_IN_DOCKER", "false").lower() == "true"
APP_PREFIX = "/app" if IN_DOCKER else ""


class Settings(BaseSettings):
    GROQ_API_KEY: str
    
    # API Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Allowed CORS Origins (comma-separated)
    CORS_ORIGINS: str = "*"
    
    OS_TYPE: str = platform.system()

    # Optional keys — only required if their features are enabled
    GOOGLE_PROJECT_ID: Optional[str] = None
    GOOGLE_STUDIO_API_KEY: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_DEFAULT_CHAT_ID: Optional[str] = None
    
    # Hotmail OAuth2
    HOTMAIL_USER: Optional[str] = "manuelalvarezdianez@hotmail.com"
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = "common"
    
    # Search Engines
    TAVILY_API_KEY: Optional[str] = None
    
    # OpenRouter Multi-Key
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY_2: Optional[str] = None
    OPENROUTER_API_KEY_3: Optional[str] = None
    
    # API Authentication
    IAPUTA_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# Create required working directories on startup
# Use /app/ prefix for Docker, or relative paths for local development
prefix = "/app" if IN_DOCKER else "."
for folder in [f"{prefix}/temp_audio", f"{prefix}/temp_vision", f"{prefix}/scripts"]:
    os.makedirs(folder, exist_ok=True)
