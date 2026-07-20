"""Base client for MSP360 MBS API."""
import httpx
import logging
import json
from typing import Dict, Any, Optional

from core.config import settings
from core.exceptions import MSP360APIError, MSP360ConfigError
from .auth import TokenManager

logger = logging.getLogger("msp360_mcp.client")


class MSP360ClientBase:
    """Base client for interacting with MSP360 Managed Backup API."""

    def __init__(self):
        if not settings.mbs_configured:
            raise MSP360ConfigError(
                "MBS API credentials not configured. Set MSP360_API_LOGIN and MSP360_API_PASSWORD."
            )
        self.base_url = settings.MSP360_API_BASE_URL
        self.timeout = settings.API_TIMEOUT
        self.token_manager = TokenManager(
            login=settings.MSP360_API_LOGIN,
            password=settings.MSP360_API_PASSWORD,
            token_lifetime=settings.TOKEN_LIFETIME,
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"

        try:
            auth_headers = await self.token_manager.get_auth_header()
        except Exception as token_err:
            logger.error("Failed to retrieve authentication token: %s", token_err)
            raise MSP360APIError(
                f"Failed to retrieve authentication token: {token_err}"
            ) from token_err

        final_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        final_headers.update(auth_headers)
        if headers:
            final_headers.update(headers)

        auth = None
        if settings.USE_BASIC_AUTH:
            auth = (settings.MSP360_API_LOGIN, settings.MSP360_API_PASSWORD)
            final_headers.pop("Authorization", None)

        logger.info("MBS request %s %s", method, url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=final_headers,
                    auth=auth,
                )

                if response.status_code == 403:
                    raise MSP360APIError(
                        "API access forbidden (403): invalid credentials or insufficient permissions.",
                        status_code=403,
                    )

                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    try:
                        return response.json()
                    except json.JSONDecodeError as exc:
                        raise MSP360APIError(
                            f"Invalid JSON response from {endpoint}: {exc}"
                        ) from exc

                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "text": response.text[:500],
                }

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            detail = exc.response.text[:500]
            try:
                payload = exc.response.json()
                if isinstance(payload, dict):
                    detail = (
                        payload.get("message")
                        or payload.get("error")
                        or payload.get("error_description")
                        or detail
                    )
            except Exception:
                pass
            raise MSP360APIError(
                f"HTTP error {status_code}: {detail}", status_code=status_code
            ) from exc
        except httpx.RequestError as exc:
            raise MSP360APIError(f"Request error: {exc}") from exc

    async def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def _post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._make_request(
            "POST", endpoint, json_data=json, data=data, headers=headers
        )

    async def _put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._make_request("PUT", endpoint, json_data=json, headers=headers)

    async def _delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return await self._make_request(
            "DELETE", endpoint, params=params, headers=headers
        )
