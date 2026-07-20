"""Read-only RMM API client."""
import logging
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from core.config import settings
from core.exceptions import MSP360APIError, MSP360ConfigError

logger = logging.getLogger("msp360_mcp.rmm")

RMM_STAT_TYPES = (
    "antivirus",
    "eventtotal",
    "eventtotal_latest",
    "hardware",
    "hdd",
    "hddsmart",
    "host",
    "hyperv",
    "memory",
    "printer",
    "runtime",
    "service",
    "software",
    "summary",
    "update",
)

COMPUTER_STAT_PATHS: Dict[str, str] = {
    "antivirus": "stat/antivirus/latest",
    "eventtotal": "stat/eventtotal",
    "eventtotal_latest": "stat/eventtotal/latest",
    "hardware": "stat/hardware/latest",
    "hdd": "stat/hdd/latest",
    "hddsmart": "stat/hddsmart/latest",
    "host": "stat/host/latest",
    "hyperv": "stat/hyperv/latest",
    "memory": "stat/memory/latest",
    "printer": "stat/printer/latest",
    "runtime": "stat/runtime/latest",
    "service": "stat/service/latest",
    "software": "stat/software/latest",
    "summary": "stat/summary/latest",
    "update": "stat/update/latest",
}

COMPUTERS_STAT_PATHS: Dict[str, str] = {
    "antivirus": "stat/antivirus/latest",
    "eventtotal_latest": "stat/eventtotal/latest",
    "hardware": "stat/hardware/latest",
    "hdd": "stat/hdd/latest",
    "hddsmart": "stat/hddsmart/latest",
    "host": "stat/host/latest",
    "hyperv": "stat/hyperv/latest",
    "memory": "stat/memory/latest",
    "printer": "stat/printer/latest",
    "runtime": "stat/runtime/latest",
    "service": "stat/service/latest",
    "software": "stat/software/latest",
    "summary": "stat/summary/latest",
    "update": "stat/update/latest",
}


class RMMClient:
    """Read-only client for MSP360 RMM public API."""

    def __init__(self):
        if not settings.rmm_configured:
            raise MSP360ConfigError(
                "RMM API token not configured. Set MSP360_RMM_API_TOKEN."
            )
        self.base_url = settings.MSP360_RMM_API_BASE_URL.rstrip("/")
        self.timeout = settings.API_TIMEOUT
        self.token = settings.MSP360_RMM_API_TOKEN.strip()

    async def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        logger.info("RMM request GET %s", url)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise MSP360APIError(
                f"RMM HTTP error {exc.response.status_code}: {exc.response.text[:500]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            raise MSP360APIError(f"RMM request error: {exc}") from exc

    async def get_computer_stat(
        self,
        hid: str,
        stat_type: str,
        mbs_stage_key: Optional[str] = None,
    ) -> Any:
        stat_path = COMPUTER_STAT_PATHS.get(stat_type)
        if not stat_path:
            valid = ", ".join(sorted(COMPUTER_STAT_PATHS))
            raise MSP360APIError(f"Unknown stat_type '{stat_type}'. Valid: {valid}")

        clean_hid = quote(hid.strip("{}"), safe="")
        endpoint = f"/api/v1/computers/{clean_hid}/{stat_path}"
        params: Dict[str, Any] = {}
        if mbs_stage_key:
            params["mbsStageKey"] = mbs_stage_key
        return await self._get(endpoint, params=params or None)

    async def get_computers_stat(
        self,
        stat_type: str,
        page_number: int = 1,
        page_size: int = 10,
        mbs_stage_key: Optional[str] = None,
    ) -> Any:
        stat_path = COMPUTERS_STAT_PATHS.get(stat_type)
        if not stat_path:
            valid = ", ".join(sorted(COMPUTERS_STAT_PATHS))
            raise MSP360APIError(f"Unknown stat_type '{stat_type}'. Valid: {valid}")

        endpoint = f"/api/v1/computers/{stat_path}"
        params: Dict[str, Any] = {
            "pageNumber": page_number,
            "pageSize": page_size,
        }
        if mbs_stage_key:
            params["mbsStageKey"] = mbs_stage_key
        return await self._get(endpoint, params=params)
