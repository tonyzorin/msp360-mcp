"""Computers client module for MSP360 Backup Remote Management API."""
import logging
from typing import Any, Dict, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.computers")


def _clean_hid(hid: str) -> str:
    return hid.strip("{}")


class ComputersClient(MSP360ClientBase):
    """Client for computer-related MSP360 Backup RM endpoints."""

    async def get_computers(
        self,
        offset: int = 0,
        count: int = 10,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        search: Optional[str] = None,
        online: Optional[bool] = None,
    ) -> Any:
        query_params: Dict[str, Any] = {}
        if company_id:
            query_params["companyId"] = company_id
        if user_id:
            query_params["userId"] = user_id
        if search:
            query_params["search"] = search
        if online is not None:
            query_params["online"] = online

        endpoint = f"/api/Computers/{offset}/{count}"
        return await self._get(endpoint, params=query_params or None)

    async def get_computer(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._get(f"/api/Computers/{_clean_hid(hid)}")

    async def get_computer_disks(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        clean = _clean_hid(hid)
        return await self._get(f"/api/Computers/{clean}/Disks")

    async def get_computer_plans(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._get(f"/api/Computers/{_clean_hid(hid)}/Plans")

    async def create_computer_plan(self, hid: str, plan_data: Dict[str, Any]) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._post(
            f"/api/Computers/{_clean_hid(hid)}/Plans", json=plan_data
        )

    async def get_computer_plan(self, hid: str, plan_id: str) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        return await self._get(f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}")

    async def update_computer_plan(
        self, hid: str, plan_id: str, plan_data: Dict[str, Any]
    ) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        return await self._put(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}", json=plan_data
        )

    async def delete_computer_plan(self, hid: str, plan_id: str) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        return await self._delete(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}"
        )

    async def get_computer_plan_info(self, hid: str, plan_id: str) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        return await self._get(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}/info"
        )

    async def start_computer_plan(
        self, hid: str, plan_id: str, mode: Optional[str] = None
    ) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        body = {"Mode": mode} if mode is not None else {}
        return await self._post(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}/start", json=body
        )

    async def stop_computer_plan(
        self, hid: str, plan_id: str, force: Optional[bool] = None
    ) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        body = {"Force": force} if force is not None else {}
        return await self._post(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}/stop", json=body
        )

    async def get_plans_history(self, offset: int = 0, count: int = 10) -> Any:
        return await self._get(f"/api/Computers/Plans/history/{offset}/{count}")

    async def get_computer_plans_history(
        self, hid: str, offset: int = 0, count: int = 10
    ) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._get(
            f"/api/Computers/{_clean_hid(hid)}/Plans/history/{offset}/{count}"
        )

    async def get_computer_plan_history(self, hid: str, plan_id: str) -> Any:
        if not hid or not plan_id:
            raise ValueError("Missing hid or plan_id")
        return await self._get(
            f"/api/Computers/{_clean_hid(hid)}/Plans/{plan_id}/history"
        )

    async def remove_computer_authorization(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._delete(
            f"/api/Computers/{_clean_hid(hid)}/authorization"
        )

    async def update_computer_authorization(
        self, hid: str, auth_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        endpoint = f"/api/Computers/{_clean_hid(hid)}/authorization"
        if auth_data:
            normalized = {}
            for key, value in auth_data.items():
                normalized[key[0].upper() + key[1:]] = value
            return await self._post(endpoint, json=normalized)
        return await self._post(endpoint, headers={"Content-Length": "0"})

    async def get_computer_statistics(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._get(f"/api/Computers/{_clean_hid(hid)}/Statistics")

    async def get_computer_usage(self, hid: str) -> Any:
        if not hid:
            raise ValueError("Missing hid")
        return await self._get(f"/api/Computers/{_clean_hid(hid)}/Usage")
