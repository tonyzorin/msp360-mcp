"""FastMCP application factory for MSP360 MCP v2."""
import logging

from fastmcp import FastMCP

from apps.register import register_mcp_apps
from core.config import settings
from core.version import SERVER_VERSION
from services.msp360 import mbs_available, rmm_available
from tools.mcp.backup_rm import register_backup_rm_tools
from tools.mcp.licenses import register_license_tools
from tools.mcp.mbs import register_info_tool, register_mbs_tools
from tools.mcp.rmm import register_rmm_tools

logger = logging.getLogger("msp360_mcp.server")

SERVER_INSTRUCTIONS = """\
MSP360 MCP — Managed Backup (MBS), Backup Remote Management (Backup RM), and read-only RMM stats.

Routing guide:
- Start with `mcp_server_info` when unsure which APIs are configured.
- MBS admin (users, companies, accounts, packages, billing, builds, destinations, admins): plain names like `get_users`, `get_companies`.
- Storage limits: `get_packages`, `create_package`, `update_package`, `delete_package` (Packages API — not agent installers).
- Agent downloads: `get_builds` (returns DownloadLink), `get_available_versions`, `request_custom_builds`.
- Admins: `get_admins`, `create_admin`, `update_admin`, `delete_admin` (permissions + Companies in JSON body).
- Usage reports: `get_billing_filtered`, `get_company_storage_usage`, `storage_usage_report`; backup issues: `backup_rm_list_issues`, `backup_rm_computers_without_success`.
- Licensing: `get_licenses`, `grant_license`, `release_license`, `revoke_license`.
- Backup RM (computers, plans, history, monitoring on api.mspbackups.com): tools prefixed `backup_rm_*`.
- RMM endpoint statistics (read-only, separate token on api.rmm.mspbackups.com): tools prefixed `rmm_*`. Use `rmm_list_stat_types` to discover valid stat_type values.
- Backup monitoring dashboards vs RMM fleet health: use `backup_rm_get_monitoring` (plan run status) or `rmm_fleet_overview` (RMM summary stat). Do not mix them.
- MCP Apps: `backup_rm_get_monitoring` and `rmm_fleet_overview` may render charts in Apps-capable hosts; JSON results remain the source of truth for all hosts (including Cursor).

Credentials: MBS tools need MSP360_API_LOGIN + MSP360_API_PASSWORD. RMM tools need MSP360_RMM_API_TOKEN. Either set alone is valid — only matching tools register.\
"""


def create_mcp_server() -> FastMCP:
    """Build FastMCP server with tools for configured credential sets only."""
    mcp = FastMCP(
        name="msp360",
        instructions=SERVER_INSTRUCTIONS,
    )

    register_info_tool(mcp)
    register_mcp_apps(mcp)

    if mbs_available():
        logger.info("Registering MBS tools (licensing + backup RM + general)")
        register_mbs_tools(mcp)
        register_license_tools(mcp)
        register_backup_rm_tools(mcp)
    else:
        logger.warning(
            "MBS credentials not configured — licensing and backup RM tools omitted"
        )

    if rmm_available():
        logger.info("Registering read-only RMM tools")
        register_rmm_tools(mcp)
    else:
        logger.warning("RMM token not configured — RMM tools omitted")

    logger.info(
        "MSP360 MCP v%s ready (mbs=%s, rmm=%s, transport=%s)",
        SERVER_VERSION,
        mbs_available(),
        rmm_available(),
        settings.MCP_TRANSPORT,
    )
    return mcp
