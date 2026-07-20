"""Licenses client module for MSP360 API."""
import logging
from typing import Any, Dict, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.licenses")


def _format_license_operation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map snake/camel case inputs to Swagger PascalCase LicenseOperation body."""
    formatted: Dict[str, Any] = {}

    license_id = (
        data.get("LicenseID")
        or data.get("licenseId")
        or data.get("license_id")
    )
    if license_id:
        formatted["LicenseID"] = license_id

    user_id = data.get("UserID") or data.get("userId") or data.get("user_id")
    if user_id:
        formatted["UserID"] = user_id

    computer_id = (
        data.get("ComputerID")
        or data.get("computerId")
        or data.get("computer_id")
    )
    if computer_id:
        formatted["ComputerID"] = computer_id

    return formatted


class LicensesClient(MSP360ClientBase):
    """Client for license-related MSP360 API endpoints."""

    async def get_licenses(
        self,
        is_available: Optional[bool] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        edition: Optional[str] = None,
        license_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        query_params: Dict[str, Any] = {}
        if is_available is not None:
            query_params["isAvailable"] = is_available
        if page is not None and limit is not None:
            query_params["skip"] = (page - 1) * limit
            query_params["take"] = limit
        if company_id:
            query_params["companyId"] = company_id
        if user_id:
            query_params["userId"] = user_id
        if edition:
            query_params["edition"] = edition
        if license_type:
            query_params["licenseType"] = license_type
        if status:
            query_params["status"] = status

        logger.info("Getting licenses with params: %s", query_params)
        return await self._get("/api/Licenses", params=query_params or None)

    async def get_license(self, license_id: str) -> Any:
        if not license_id:
            raise ValueError("Missing license_id")
        return await self._get(f"/api/Licenses/{license_id}")

    async def grant_license(
        self,
        license_id: str,
        user_id: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload = _format_license_operation(
            {"license_id": license_id, "user_id": user_id, **(extra or {})}
        )
        if "LicenseID" not in payload or "UserID" not in payload:
            raise ValueError("grant_license requires license_id and user_id")
        return await self._post("/api/Licenses/Grant", json=payload)

    async def release_license(
        self,
        license_id: str,
        user_id: Optional[str] = None,
        computer_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload = _format_license_operation(
            {
                "license_id": license_id,
                "user_id": user_id,
                "computer_id": computer_id,
                **(extra or {}),
            }
        )
        if "LicenseID" not in payload:
            raise ValueError("release_license requires license_id")
        return await self._post("/api/Licenses/Release", json=payload)

    async def revoke_license(
        self,
        license_id: str,
        user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Any:
        payload = _format_license_operation(
            {"license_id": license_id, "user_id": user_id, **(extra or {})}
        )
        if "LicenseID" not in payload:
            raise ValueError("revoke_license requires license_id")
        return await self._post("/api/Licenses/Revoke", json=payload)
