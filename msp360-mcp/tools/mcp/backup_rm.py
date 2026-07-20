"""Backup Remote Management MCP tools (full Computers + Monitoring API)."""
from typing import Any, Optional

from fastmcp import FastMCP
from fastmcp.apps import AppConfig

from apps.templates import BACKUP_MONITORING_URI
from services.msp360 import get_mbs_client
from tools.mcp.helpers import parse_json_object
from tools.mcp.reports import (
    computers_without_success,
    extract_list,
    filter_issue_rows,
    group_rows,
    monitoring_rows,
)

BACKUP_MONITORING_APP = AppConfig(resource_uri=BACKUP_MONITORING_URI)


def register_backup_rm_tools(mcp: FastMCP) -> None:
    @mcp.tool
    async def backup_rm_list_computers(
        offset: int = 0,
        count: int = 10,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        search: Optional[str] = None,
        online: Optional[bool] = None,
    ) -> Any:
        """[Backup RM] List managed backup computers (paginated, filterable).

        Use when: discovering computers in Backup Remote Management.
        Not for: RMM endpoint stats — use `rmm_get_computers_stat`.
        Params: offset, count; optional company_id, user_id, search, online.
        """
        return await get_mbs_client().get_computers(
            offset=offset,
            count=count,
            company_id=company_id,
            user_id=user_id,
            search=search,
            online=online,
        )

    @mcp.tool
    async def backup_rm_get_computer(hid: str) -> Any:
        """[Backup RM] Get one managed computer by hardware ID (hid).

        Use when: you have hid from list/monitoring and need computer details.
        Not for: RMM hardware stats — use `rmm_get_computer_stat` with stat_type=hardware.
        Params: hid (hardware ID).
        """
        return await get_mbs_client().get_computer(hid)

    @mcp.tool
    async def backup_rm_get_computer_disks(hid: str) -> Any:
        """[Backup RM] Get disk layout/volumes for a managed computer.

        Use when: planning backup plans or checking disk inventory on an agent.
        Not for: RMM SMART/HDD stats — use `rmm_get_computer_stat` with stat_type=hdd or hddsmart.
        Params: hid.
        """
        return await get_mbs_client().get_computer_disks(hid)

    @mcp.tool
    async def backup_rm_list_plans(hid: str) -> Any:
        """[Backup RM] List backup/restore plans on a computer.

        Use when: reviewing configured plans before start/stop/history calls.
        Not for: global plan run monitoring — use `backup_rm_get_monitoring`.
        Params: hid.
        """
        return await get_mbs_client().get_computer_plans(hid)

    @mcp.tool
    async def backup_rm_create_plan(hid: str, plan_data_json: str) -> Any:
        """[Backup RM] Create a backup plan on a computer (mutating).

        Use when: deploying a new plan from Swagger-compatible JSON.
        Not for: updating existing plans — use `backup_rm_update_plan`.
        Params: hid; plan_data_json (plan body).
        """
        plan_data = parse_json_object(plan_data_json, "plan_data_json")
        return await get_mbs_client().create_computer_plan(hid, plan_data)

    @mcp.tool
    async def backup_rm_get_plan(hid: str, plan_id: str) -> Any:
        """[Backup RM] Get one plan definition on a computer.

        Use when: inspecting plan settings before update/start.
        Not for: run history — use `backup_rm_plan_history`.
        Params: hid, plan_id.
        """
        return await get_mbs_client().get_computer_plan(hid, plan_id)

    @mcp.tool
    async def backup_rm_update_plan(
        hid: str, plan_id: str, plan_data_json: str
    ) -> Any:
        """[Backup RM] Update a plan on a computer (mutating).

        Use when: changing plan configuration via JSON body.
        Not for: creating plans — use `backup_rm_create_plan`.
        Params: hid, plan_id, plan_data_json.
        """
        plan_data = parse_json_object(plan_data_json, "plan_data_json")
        return await get_mbs_client().update_computer_plan(hid, plan_id, plan_data)

    @mcp.tool
    async def backup_rm_delete_plan(hid: str, plan_id: str) -> Any:
        """[Backup RM] Delete a plan from a computer (mutating).

        Use when: removing a plan definition from an agent.
        Not for: stopping a running job — use `backup_rm_stop_plan`.
        Params: hid, plan_id.
        """
        return await get_mbs_client().delete_computer_plan(hid, plan_id)

    @mcp.tool
    async def backup_rm_get_plan_info(hid: str, plan_id: str) -> Any:
        """[Backup RM] Get extended metadata for a computer plan.

        Use when: you need richer plan info beyond `backup_rm_get_plan`.
        Not for: last run status across fleet — use `backup_rm_get_monitoring`.
        Params: hid, plan_id.
        """
        return await get_mbs_client().get_computer_plan_info(hid, plan_id)

    @mcp.tool
    async def backup_rm_start_plan(
        hid: str, plan_id: str, mode: Optional[str] = None
    ) -> Any:
        """[Backup RM] Start/run a backup plan on a computer (mutating).

        Use when: triggering an on-demand or scheduled plan run.
        Not for: stopping — use `backup_rm_stop_plan`.
        Params: hid, plan_id; optional mode.
        """
        return await get_mbs_client().start_computer_plan(hid, plan_id, mode=mode)

    @mcp.tool
    async def backup_rm_stop_plan(
        hid: str, plan_id: str, force: Optional[bool] = None
    ) -> Any:
        """[Backup RM] Stop a running backup plan (mutating).

        Use when: cancelling an in-progress plan run.
        Not for: deleting plan definition — use `backup_rm_delete_plan`.
        Params: hid, plan_id; optional force.
        """
        return await get_mbs_client().stop_computer_plan(hid, plan_id, force=force)

    @mcp.tool
    async def backup_rm_plans_history(offset: int = 0, count: int = 10) -> Any:
        """[Backup RM] Get global backup plan run history (paginated).

        Use when: auditing recent runs across all computers.
        Not for: one computer's history — use `backup_rm_computer_plans_history`.
        Params: offset, count.
        """
        return await get_mbs_client().get_plans_history(offset, count)

    @mcp.tool
    async def backup_rm_computer_plans_history(
        hid: str, offset: int = 0, count: int = 10
    ) -> Any:
        """[Backup RM] Get plan run history for one computer.

        Use when: troubleshooting runs on a specific hid.
        Not for: one plan's history — use `backup_rm_plan_history`.
        Params: hid, offset, count.
        """
        return await get_mbs_client().get_computer_plans_history(hid, offset, count)

    @mcp.tool
    async def backup_rm_plan_history(hid: str, plan_id: str) -> Any:
        """[Backup RM] Get run history for one plan on one computer.

        Use when: deep-diving a single plan's execution timeline.
        Not for: live monitoring dashboard — use `backup_rm_get_monitoring`.
        Params: hid, plan_id.
        """
        return await get_mbs_client().get_computer_plan_history(hid, plan_id)

    @mcp.tool
    async def backup_rm_update_authorization(
        hid: str, auth_data_json: str = "{}"
    ) -> Any:
        """[Backup RM] Create or update computer authorization (mutating).

        Use when: linking a computer to UserId/CompanyId via JSON.
        Not for: removing authorization — use `backup_rm_remove_authorization`.
        Params: hid; auth_data_json (UserId/CompanyId fields).
        """
        auth_data = parse_json_object(auth_data_json, "auth_data_json")
        return await get_mbs_client().update_computer_authorization(hid, auth_data)

    @mcp.tool
    async def backup_rm_remove_authorization(hid: str) -> Any:
        """[Backup RM] Remove authorization from a computer (mutating).

        Use when: unassigning a computer from user/company in RM.
        Not for: deleting the user — use `delete_user`.
        Params: hid.
        """
        return await get_mbs_client().remove_computer_authorization(hid)

    @mcp.tool
    async def backup_rm_get_statistics(hid: str) -> Any:
        """[Backup RM] Get backup statistics for one computer.

        Use when: reviewing backup performance/size stats for an agent.
        Not for: RMM runtime/service stats — use `rmm_get_computer_stat`.
        Params: hid.
        """
        return await get_mbs_client().get_computer_statistics(hid)

    @mcp.tool
    async def backup_rm_get_usage(hid: str) -> Any:
        """[Backup RM] Get storage/usage information for one computer.

        Use when: checking backup storage consumption on an agent.
        Not for: MBS billing records — use `get_billing`.
        Params: hid.
        """
        return await get_mbs_client().get_computer_usage(hid)

    @mcp.tool(app=BACKUP_MONITORING_APP)
    async def backup_rm_get_monitoring(
        page: int = 1,
        limit: int = 10,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Any:
        """[Backup RM] Get backup plan run monitoring (status dashboard data).

        Use when: reviewing plan run outcomes (success/warning/failed/running) across the fleet or filtered scope.
        Not for: RMM endpoint health — use `rmm_fleet_overview`; not for one monitoring record — use `backup_rm_get_monitoring_item`.
        Params: page, limit; optional user_id, company_id, status filter.
        MCP App: renders a status chart in Apps-capable hosts; JSON is always returned.
        """
        params = {"page": page, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        if company_id:
            params["company_id"] = company_id
        if status:
            params["status"] = status
        return await get_mbs_client().get_monitoring(params)

    @mcp.tool
    async def backup_rm_get_monitoring_for_user(
        user_id: str, page: int = 1, limit: int = 10
    ) -> Any:
        """[Backup RM] Get backup monitoring rows for one user.

        Use when: narrowing monitoring to a specific user's plan runs.
        Not for: fleet-wide monitoring — use `backup_rm_get_monitoring`.
        Params: user_id, page, limit.
        """
        return await get_mbs_client().get_monitoring_for_user(
            user_id, {"page": page, "limit": limit}
        )

    @mcp.tool
    async def backup_rm_get_monitoring_item(item_id: str) -> Any:
        """[Backup RM] Get one backup monitoring/history item by ID.

        Use when: you have a monitoring item_id from a list/history and need full detail.
        Not for: paginated monitoring lists — use `backup_rm_get_monitoring`.
        Params: item_id.
        """
        return await get_mbs_client().get_monitoring_item(item_id)

    @mcp.tool
    async def backup_rm_list_user_computers(
        user_id: str, page: int = 1, limit: int = 10
    ) -> Any:
        """[Backup RM] List computers assigned to a user (Users API, RM workflows).

        Use when: finding which agents belong to a user before plan or monitoring calls.
        Not for: full computer search — use `backup_rm_list_computers`.
        Params: user_id, page, limit.
        """
        return await get_mbs_client().get_user_computers(
            user_id, {"page": page, "limit": limit}
        )

    @mcp.tool
    async def backup_rm_list_issues(
        company_id: Optional[str] = None,
        status: Optional[str] = None,
        group_by: str = "company",
        days: Optional[int] = None,
        max_pages: int = 5,
        limit: int = 100,
    ) -> Any:
        """[Backup RM] List backup issues from latest plan-run monitoring.

        Use when: finding failed/warning plan runs grouped by company or computer.
        Not for: full historical audit of every session — Monitoring reflects latest runs only.
        Params: optional company_id, status (e.g. Failed); group_by=company|computer;
        optional days filters by LastStart age; max_pages, limit for pagination.
        """
        client = get_mbs_client()
        all_rows: list = []
        for page in range(1, max_pages + 1):
            batch = await client.get_monitoring(
                {
                    "page": page,
                    "limit": limit,
                    "company_id": company_id,
                }
            )
            rows = monitoring_rows(batch)
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < limit:
                break

        issues = filter_issue_rows(
            all_rows, status=status, company_id=company_id, days=days
        )
        grouped = group_rows(issues, group_by if group_by in ("company", "computer") else "company")
        return {
            "total_issues": len(issues),
            "group_by": group_by,
            "days": days,
            "note": "Based on latest plan-run monitoring rows, not full session history.",
            "issues": issues,
            "grouped": grouped,
        }

    @mcp.tool
    async def backup_rm_computers_without_success(
        company_id: Optional[str] = None,
        max_pages: int = 5,
        limit: int = 100,
    ) -> Any:
        """[Backup RM] List computers with no successful latest plan run.

        Use when: finding agents that never show Success in current monitoring data.
        Not for: RMM health — use `rmm_fleet_overview`.
        Params: optional company_id; max_pages, limit control how much data is scanned.
        """
        client = get_mbs_client()
        computers: list = []
        offset = 0
        page_size = min(limit, 100)
        for _ in range(max_pages):
            batch = await client.get_computers(
                offset=offset,
                count=page_size,
                company_id=company_id,
            )
            rows = extract_list(batch)
            if not rows:
                break
            computers.extend(rows)
            if len(rows) < page_size:
                break
            offset += page_size

        mon_rows: list = []
        for page in range(1, max_pages + 1):
            batch = await client.get_monitoring(
                {"page": page, "limit": limit, "company_id": company_id}
            )
            rows = monitoring_rows(batch)
            if not rows:
                break
            mon_rows.extend(rows)
            if len(rows) < limit:
                break

        missing = computers_without_success(computers, mon_rows)
        return {
            "total_computers_scanned": len(computers),
            "total_without_success": len(missing),
            "note": "Compares computer inventory to latest monitoring Success status.",
            "computers": missing,
        }
