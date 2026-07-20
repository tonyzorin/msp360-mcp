"""Read-only RMM MCP tools."""
from typing import Any, Literal, Optional

from fastmcp import FastMCP
from fastmcp.apps import AppConfig

from apps.templates import RMM_FLEET_URI
from services.msp360 import get_rmm_client
from services.msp360.rmm_client import RMM_STAT_TYPES
from tools.mcp.tool_decorators import readonly

RMMStatType = Literal[
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
]

RMM_FLEET_APP = AppConfig(resource_uri=RMM_FLEET_URI)


def register_rmm_tools(mcp: FastMCP) -> None:
    @readonly(mcp, "Get RMM Computer Stat")
    async def rmm_get_computer_stat(
        hid: str,
        stat_type: RMMStatType,
        mbs_stage_key: Optional[str] = None,
    ) -> Any:
        """[RMM read-only] Get one RMM stat payload for a single computer.

        Use when: inspecting antivirus, hardware, services, etc. for a known hid.
        Not for: backup plan monitoring — use `backup_rm_get_monitoring`; not for: fleet-wide stats — use `rmm_get_computers_stat`.
        Params: hid, stat_type (see `rmm_list_stat_types`), optional mbs_stage_key.
        """
        return await get_rmm_client().get_computer_stat(
            hid, stat_type, mbs_stage_key=mbs_stage_key
        )

    @readonly(mcp, "Get RMM Fleet Stat")
    async def rmm_get_computers_stat(
        stat_type: RMMStatType,
        page_number: int = 1,
        page_size: int = 10,
        mbs_stage_key: Optional[str] = None,
    ) -> Any:
        """[RMM read-only] Get fleet-wide RMM stat rows for a stat_type (paginated).

        Use when: querying a specific RMM dataset across many endpoints.
        Not for: a curated fleet health summary UI — prefer `rmm_fleet_overview` (stat_type=summary).
        Params: stat_type, page_number, page_size, optional mbs_stage_key.
        """
        return await get_rmm_client().get_computers_stat(
            stat_type,
            page_number=page_number,
            page_size=page_size,
            mbs_stage_key=mbs_stage_key,
        )

    @readonly(mcp, "List RMM Stat Types")
    async def rmm_list_stat_types() -> list[str]:
        """[RMM read-only] List valid stat_type values for RMM stat tools.

        Use when: unsure which stat_type to pass to `rmm_get_computer_stat` or `rmm_get_computers_stat`.
        Not for: fetching stat data — call a stat tool after choosing a type.
        Params: none.
        """
        return list(RMM_STAT_TYPES)

    @readonly(mcp, "RMM Fleet Overview", app=RMM_FLEET_APP)
    async def rmm_fleet_overview(
        page_number: int = 1,
        page_size: int = 10,
        mbs_stage_key: Optional[str] = None,
    ) -> Any:
        """[RMM read-only] Fleet health summary (wraps stat_type=summary).

        Use when: you want a high-level RMM fleet snapshot (counts/table) rather than a raw stat dump.
        Not for: backup plan run status — use `backup_rm_get_monitoring`; not for: other stat types — use `rmm_get_computers_stat`.
        Params: page_number, page_size, optional mbs_stage_key.
        MCP App: renders a summary table in Apps-capable hosts; JSON is always returned.
        """
        return await get_rmm_client().get_computers_stat(
            "summary",
            page_number=page_number,
            page_size=page_size,
            mbs_stage_key=mbs_stage_key,
        )
