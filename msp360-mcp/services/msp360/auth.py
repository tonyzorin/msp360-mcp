"""Authentication module for MSP360 MBS API."""
import httpx
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from core.config import settings
from core.exceptions import MSP360APIError

logger = logging.getLogger("msp360_mcp.auth")


class TokenManager:
    """Singleton token manager for MBS Provider Login."""

    _instance = None
    _lock = asyncio.Lock()
    _token_requests_in_progress = 0

    def __new__(cls, login: str, password: str, token_lifetime: int = 3600):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, login: str, password: str, token_lifetime: int = 3600):
        if getattr(self, "_initialized", False):
            if self.login != login or self.password != password:
                self.login = login
                self.password = password
                self.token_lifetime = token_lifetime
                self.current_token = None
                self.token_expiry = None
            return

        self.login = login
        self.password = password
        self.token_lifetime = token_lifetime
        self.current_token = None
        self.token_expiry = None
        self._initialized = True

    async def generate_token(self) -> str:
        if not self.login.strip() or not self.password.strip():
            raise MSP360APIError("Missing MBS API credentials")

        async with self._lock:
            if TokenManager._token_requests_in_progress > 0:
                await asyncio.sleep(0.5)
                if (
                    self.current_token
                    and self.token_expiry
                    and datetime.now() < self.token_expiry
                ):
                    return self.current_token

            TokenManager._token_requests_in_progress += 1
            try:
                url = f"{settings.MSP360_API_BASE_URL}/api/Provider/Login"
                payload = {"UserName": self.login, "Password": self.password}

                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        url=url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                    if response.status_code == 403:
                        raise MSP360APIError(
                            "Authentication failed: 403 Forbidden", status_code=403
                        )

                    response.raise_for_status()
                    auth_data = response.json()
                    logger.info(
                        "Authentication succeeded; token fields present: %s",
                        list(auth_data.keys()) if isinstance(auth_data, dict) else type(auth_data),
                    )

                    token = auth_data.get("access_token") or auth_data.get("Token")
                    if not token:
                        raise MSP360APIError(
                            "Token not found in authentication response"
                        )

                    expires_in = auth_data.get("expires_in", self.token_lifetime)
                    self.current_token = token
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    return token
            finally:
                TokenManager._token_requests_in_progress -= 1

    async def get_valid_token(self) -> str:
        if not self.login.strip() or not self.password.strip():
            raise MSP360APIError("Missing MBS API credentials")

        if (
            self.current_token is None
            or self.token_expiry is None
            or datetime.now() >= self.token_expiry
        ):
            return await self.generate_token()

        if datetime.now() + timedelta(minutes=5) >= self.token_expiry:
            return await self.generate_token()

        return self.current_token

    async def get_auth_header(self) -> Dict[str, str]:
        token = await self.get_valid_token()
        return {"Authorization": f"Bearer {token}"}
