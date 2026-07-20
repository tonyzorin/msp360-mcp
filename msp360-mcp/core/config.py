import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    MSP360_API_BASE_URL: str = "https://api.mspbackups.com"
    MSP360_API_LOGIN: str = os.getenv("MSP360_API_LOGIN", "")
    MSP360_API_PASSWORD: str = os.getenv("MSP360_API_PASSWORD", "")

    MSP360_RMM_API_BASE_URL: str = os.getenv(
        "MSP360_RMM_API_BASE_URL", "https://api.rmm.mspbackups.com"
    )
    MSP360_RMM_API_TOKEN: str = os.getenv("MSP360_RMM_API_TOKEN", "")

    TOKEN_LIFETIME: int = int(os.getenv("TOKEN_LIFETIME", 3600))
    USE_BASIC_AUTH: bool = os.getenv("USE_BASIC_AUTH", "False").lower() in (
        "true",
        "1",
        "t",
    )
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", 60))

    PORT: int = int(os.getenv("PORT", 51817))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")

    @property
    def mbs_configured(self) -> bool:
        return bool(self.MSP360_API_LOGIN.strip() and self.MSP360_API_PASSWORD.strip())

    @property
    def rmm_configured(self) -> bool:
        return bool(self.MSP360_RMM_API_TOKEN.strip())


settings = Settings()
