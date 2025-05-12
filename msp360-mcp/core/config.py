import os
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API Base URL
    MSP360_API_BASE_URL: str = "https://api.mspbackups.com"
    
    # Authentication credentials
    MSP360_API_LOGIN: str = os.getenv("MSP360_API_LOGIN", "")  # Empty default to avoid startup issues
    MSP360_API_PASSWORD: str = os.getenv("MSP360_API_PASSWORD", "")  # Empty default to avoid startup issues
    
    # Token configuration
    TOKEN_LIFETIME: int = int(os.getenv("TOKEN_LIFETIME", 3600))  # Token lifetime in seconds (1 hour)
    USE_BASIC_AUTH: bool = os.getenv("USE_BASIC_AUTH", "False").lower() in ("true", "1", "t")  # Default to False
    
    # API Configuration
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", 60))  # Timeout in seconds for API calls
    
    # Server Configuration
    PORT: int = int(os.getenv("PORT", 51817))
    HOST: str = os.getenv("HOST", "0.0.0.0")


settings = Settings() 