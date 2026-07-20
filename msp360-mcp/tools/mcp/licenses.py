"""Licensing MCP tools."""
from typing import Any, Optional

from fastmcp import FastMCP

from services.msp360 import get_mbs_client


def register_license_tools(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_licenses(
        is_available: Optional[bool] = None,
        page: int = 1,
        limit: int = 10,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        edition: Optional[str] = None,
        license_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        """[Licensing] List MSP360 licenses with optional filters.

        Use when: auditing license pool, availability, or assignments.
        Not for: granting/releasing — use `grant_license`, `release_license`, or `revoke_license`.
        Params: is_available, page, limit, company_id, user_id, edition, license_type, status.
        """
        client = get_mbs_client()
        return await client.get_licenses(
            is_available=is_available,
            page=page,
            limit=limit,
            company_id=company_id,
            user_id=user_id,
            edition=edition,
            license_type=license_type,
            status=status,
        )

    @mcp.tool
    async def get_license(license_id: str) -> Any:
        """[Licensing] Get one license by ID.

        Use when: you have license_id and need assignment details.
        Not for: listing licenses — use `get_licenses`.
        Params: license_id.
        """
        return await get_mbs_client().get_license(license_id)

    @mcp.tool
    async def grant_license(license_id: str, user_id: str) -> Any:
        """[Licensing] Grant a license to a user (mutating).

        Use when: assigning an available license to a user.
        Not for: releasing from a computer — use `release_license`.
        Params: license_id, user_id.
        """
        return await get_mbs_client().grant_license(license_id, user_id)

    @mcp.tool
    async def release_license(
        license_id: str,
        user_id: Optional[str] = None,
        computer_id: Optional[str] = None,
    ) -> Any:
        """[Licensing] Release a license from a user or computer (mutating).

        Use when: freeing a license seat without revoking permanently.
        Not for: permanent revocation — use `revoke_license`.
        Params: license_id; optional user_id or computer_id.
        """
        return await get_mbs_client().release_license(
            license_id, user_id=user_id, computer_id=computer_id
        )

    @mcp.tool
    async def revoke_license(
        license_id: str, user_id: Optional[str] = None
    ) -> Any:
        """[Licensing] Revoke a license assignment (mutating).

        Use when: permanently removing a license assignment.
        Not for: temporary release — use `release_license`.
        Params: license_id; optional user_id.
        """
        return await get_mbs_client().revoke_license(license_id, user_id=user_id)
