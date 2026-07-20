"""Smoke tests for MSP360 MCP v2."""
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "msp360-mcp")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def clear_credentials(monkeypatch):
    monkeypatch.delenv("MSP360_API_LOGIN", raising=False)
    monkeypatch.delenv("MSP360_API_PASSWORD", raising=False)
    monkeypatch.delenv("MSP360_RMM_API_TOKEN", raising=False)


def test_server_starts_without_credentials():
    from importlib import reload

    import core.config as config_mod
    import server.fastmcp_app as app_mod

    reload(config_mod)
    reload(app_mod)

    mcp = app_mod.create_mcp_server()
    assert mcp is not None
    assert app_mod.SERVER_VERSION == "2.2.1"


@pytest.mark.asyncio
async def test_renamed_tools_and_mcp_apps_registered(monkeypatch):
    from importlib import reload

    import core.config as config_mod
    import server.fastmcp_app as app_mod
    import services.msp360 as services_mod

    monkeypatch.setenv("MSP360_API_LOGIN", "user")
    monkeypatch.setenv("MSP360_API_PASSWORD", "pass")
    monkeypatch.setenv("MSP360_RMM_API_TOKEN", "token")
    reload(config_mod)
    config_mod.settings = config_mod.Settings()
    reload(services_mod)
    reload(app_mod)

    mcp = app_mod.create_mcp_server()
    tools = await mcp.list_tools()
    names = {t.name for t in tools}

    assert "backup_rm_list_user_computers" in names
    assert "backup_rm_get_monitoring_item" in names
    assert "get_user_computers" not in names
    assert "get_monitoring_item" not in names
    assert "rmm_fleet_overview" in names
    assert "backup_rm_get_monitoring" in names
    assert "create_admin" in names
    assert "create_package" in names
    assert "request_custom_builds" in names
    assert "get_billing_filtered" in names
    assert "storage_usage_report" in names
    assert "backup_rm_list_issues" in names
    assert "backup_rm_computers_without_success" in names

    resources = await mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "ui://msp360/backup-monitoring@v3.html" in uris
    assert "ui://msp360/rmm-fleet-summary@v3.html" in uris


def test_mbs_configured_helper(monkeypatch):
    from importlib import reload

    import core.config as config_mod

    monkeypatch.setenv("MSP360_API_LOGIN", "user")
    monkeypatch.setenv("MSP360_API_PASSWORD", "pass")
    reload(config_mod)

    assert config_mod.settings.mbs_configured is True
    assert config_mod.settings.rmm_configured is False


def test_rmm_configured_helper(monkeypatch):
    from importlib import reload

    import core.config as config_mod

    monkeypatch.setenv("MSP360_RMM_API_TOKEN", "token")
    reload(config_mod)

    assert config_mod.settings.rmm_configured is True
    assert config_mod.settings.mbs_configured is False


def test_license_operation_formatting():
    from services.msp360.licenses_client import _format_license_operation

    payload = _format_license_operation(
        {"license_id": "L1", "user_id": "U1", "computer_id": "C1"}
    )
    assert payload == {"LicenseID": "L1", "UserID": "U1", "ComputerID": "C1"}


def test_server_instructions_cover_routing():
    from server.fastmcp_app import SERVER_INSTRUCTIONS

    assert "backup_rm_" in SERVER_INSTRUCTIONS
    assert "rmm_" in SERVER_INSTRUCTIONS
    assert "mcp_server_info" in SERVER_INSTRUCTIONS
    assert "create_admin" in SERVER_INSTRUCTIONS
    assert "get_packages" in SERVER_INSTRUCTIONS


def test_billing_filter_uses_put_endpoints():
    import asyncio

    from services.msp360.billing_client import BillingClient

    client = BillingClient.__new__(BillingClient)
    calls = []

    async def fake_request(method, endpoint, json_data=None, params=None):
        calls.append((method, endpoint, json_data))
        return {"ok": True}

    client._make_request = fake_request  # type: ignore[method-assign]

    asyncio.run(
        client.get_filtered_billing({"CompanyName": "ABC", "Date": "2026-01-01"})
    )
    assert calls[-1] == (
        "PUT",
        "/api/Billing",
        {"CompanyName": "ABC", "Date": "2026-01-01"},
    )

    asyncio.run(client.get_filtered_billing({"UserID": "user-1"}))
    assert calls[-1] == ("PUT", "/api/Billing/Details", {"UserID": "user-1"})


def test_report_helpers():
    from tools.mcp.reports import (
        filter_issue_rows,
        group_rows,
        is_success_status,
    )

    rows = [
        {"CompanyName": "A", "ComputerName": "pc1", "Status": "Success", "LastStart": "2026-07-01T00:00:00+00:00"},
        {"CompanyName": "A", "ComputerName": "pc2", "Status": "Failed", "LastStart": "2026-07-01T00:00:00+00:00"},
    ]
    issues = filter_issue_rows(rows)
    assert len(issues) == 1
    assert issues[0]["ComputerName"] == "pc2"
    grouped = group_rows(issues, "company")
    assert "A" in grouped
    assert is_success_status(0)
    assert not is_success_status("Failed")


def test_packed_mcpb_matches_server_version():
    import subprocess

    repo_root = os.path.dirname(__file__)
    manifest = os.path.join(repo_root, "mcpb", "manifest.json")
    if not os.path.isfile(manifest):
        pytest.skip("mcpb/ not present in this environment (Docker runtime image)")

    script = os.path.join(repo_root, "scripts", "verify_mcpb_version.py")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
