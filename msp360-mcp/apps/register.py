"""Register MCP App UI resources on the FastMCP server."""

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP
from fastmcp.utilities.mime import UI_MIME_TYPE

from apps.templates import (
    BACKUP_MONITORING_URI,
    RMM_FLEET_URI,
    backup_monitoring_html,
    rmm_fleet_html,
)

# Official @modelcontextprotocol/ext-apps SDK is loaded from unpkg.
_APP_RESOURCE_CONFIG = AppConfig(
    prefers_border=True,
    csp=ResourceCSP(resource_domains=["https://unpkg.com"]),
)


def register_mcp_apps(mcp: FastMCP) -> None:
    """Expose ui:// HTML bundles for Apps-capable MCP hosts."""

    @mcp.resource(
        BACKUP_MONITORING_URI,
        mime_type=UI_MIME_TYPE,
        app=_APP_RESOURCE_CONFIG,
    )
    def backup_monitoring_app() -> str:
        """Interactive backup plan run status chart (success / warning / failed / running)."""
        return backup_monitoring_html()

    @mcp.resource(
        RMM_FLEET_URI,
        mime_type=UI_MIME_TYPE,
        app=_APP_RESOURCE_CONFIG,
    )
    def rmm_fleet_summary_app() -> str:
        """Interactive RMM fleet summary with CPU/RAM/HDD bars."""
        return rmm_fleet_html()
