"""General MBS MCP tools (users, companies, accounts, etc.)."""
from typing import Any, Optional

from fastmcp import FastMCP

from core.version import SERVER_VERSION
from services.msp360 import get_mbs_client
from tools.mcp.helpers import parse_json_object, pagination_params


def register_info_tool(mcp: FastMCP) -> None:
    @mcp.tool
    async def mcp_server_info() -> dict:
        """[Meta] Report MSP360 MCP version and which API surfaces are configured.

        Use when: starting a session, debugging missing tools, or confirming MBS vs RMM availability.
        Not for: fetching backup or RMM data — call domain tools instead.
        Params: none.
        """
        from core.config import settings
        from services.msp360 import mbs_available, rmm_available

        return {
            "version": SERVER_VERSION,
            "mbs_configured": mbs_available(),
            "rmm_configured": rmm_available(),
            "mbs_base_url": settings.MSP360_API_BASE_URL,
            "rmm_base_url": settings.MSP360_RMM_API_BASE_URL,
        }


def register_mbs_tools(mcp: FastMCP) -> None:
    @mcp.tool
    async def get_users(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List Managed Backup users (paginated).

        Use when: browsing or searching MSP360 user accounts.
        Not for: computers or backup plans — use `backup_rm_*` tools.
        Params: page, limit pagination.
        """
        return await get_mbs_client().get_users(pagination_params(page, limit))

    @mcp.tool
    async def get_user(user_id: str) -> Any:
        """[MBS] Get one Managed Backup user by ID.

        Use when: you have a user_id and need profile details.
        Not for: listing a user's computers — use `backup_rm_list_user_computers`.
        Params: user_id.
        """
        return await get_mbs_client().get_user(user_id)

    @mcp.tool
    async def create_user(user_data_json: str) -> Any:
        """[MBS] Create a Managed Backup user (mutating).

        Use when: provisioning a new user from a Swagger-compatible JSON body.
        Not for: updates — use `update_user`.
        Params: user_data_json (JSON object string).
        """
        return await get_mbs_client().create_user(
            parse_json_object(user_data_json, "user_data_json")
        )

    @mcp.tool
    async def update_user(user_data_json: str) -> Any:
        """[MBS] Update a Managed Backup user (mutating).

        Use when: changing user fields from a JSON body that includes the user ID.
        Not for: creating users — use `create_user`.
        Params: user_data_json (JSON object string).
        """
        return await get_mbs_client().update_user(
            parse_json_object(user_data_json, "user_data_json")
        )

    @mcp.tool
    async def delete_user(user_id: str) -> Any:
        """[MBS] Delete a Managed Backup user (mutating).

        Use when: permanently removing a user account.
        Not for: releasing licenses — use `release_license`.
        Params: user_id.
        """
        return await get_mbs_client().delete_user(user_id)

    @mcp.tool
    async def get_companies(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List companies (paginated).

        Use when: browsing tenant/company hierarchy.
        Not for: computer inventory — use `backup_rm_list_computers`.
        Params: page, limit.
        """
        return await get_mbs_client().get_companies(pagination_params(page, limit))

    @mcp.tool
    async def get_company(company_id: str) -> Any:
        """[MBS] Get one company by ID.

        Use when: you have company_id and need company metadata.
        Not for: filtering computers — pass company_id to `backup_rm_list_computers`.
        Params: company_id.
        """
        return await get_mbs_client().get_company(company_id)

    @mcp.tool
    async def create_company(company_data_json: str) -> Any:
        """[MBS] Create a company (mutating).

        Use when: adding a new company from JSON (Name, StorageLimit, license settings, etc.).
        Not for: updates — use `update_company`.
        Params: company_data_json.
        """
        return await get_mbs_client().create_company(
            parse_json_object(company_data_json, "company_data_json")
        )

    @mcp.tool
    async def update_company(company_data_json: str) -> Any:
        """[MBS] Update a company (mutating).

        Use when: changing company fields via JSON (including StorageLimit).
        Not for: creating — use `create_company`.
        Params: company_data_json.
        """
        return await get_mbs_client().update_company(
            parse_json_object(company_data_json, "company_data_json")
        )

    @mcp.tool
    async def delete_company(company_id: str) -> Any:
        """[MBS] Delete a company (mutating).

        Use when: removing a company record.
        Not for: deleting computers — use Backup RM authorization tools.
        Params: company_id.
        """
        return await get_mbs_client().delete_company(company_id)

    @mcp.tool
    async def get_accounts(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List cloud storage accounts (paginated).

        Use when: reviewing destination/storage account configuration.
        Not for: per-user destinations — use `get_user_destinations`.
        Params: page, limit.
        """
        return await get_mbs_client().get_accounts(pagination_params(page, limit))

    @mcp.tool
    async def get_account(account_id: str) -> Any:
        """[MBS] Get one storage account by ID.

        Use when: inspecting a specific storage account.
        Not for: listing all accounts — use `get_accounts`.
        Params: account_id.
        """
        return await get_mbs_client().get_account(account_id)

    @mcp.tool
    async def create_account(account_data_json: str) -> Any:
        """[MBS] Create a storage account (mutating).

        Use when: registering new cloud storage credentials via JSON.
        Not for: user-level destinations — use `add_destination`.
        Params: account_data_json.
        """
        return await get_mbs_client().create_account(
            parse_json_object(account_data_json, "account_data_json")
        )

    @mcp.tool
    async def update_account(account_data_json: str) -> Any:
        """[MBS] Update a storage account (mutating).

        Use when: changing storage account settings via JSON.
        Not for: creating — use `create_account`.
        Params: account_data_json.
        """
        return await get_mbs_client().update_account(
            parse_json_object(account_data_json, "account_data_json")
        )

    @mcp.tool
    async def get_packages(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List storage limit packages (paginated).

        Use when: reviewing storage limits available for user destinations.
        Not for: agent downloads — use `get_builds`.
        Params: page, limit.
        """
        return await get_mbs_client().get_packages(pagination_params(page, limit))

    @mcp.tool
    async def get_package(package_id: str) -> Any:
        """[MBS] Get one storage limit package by ID.

        Use when: inspecting StorageLimit, Cost, and package settings.
        Not for: listing packages — use `get_packages`.
        Params: package_id.
        """
        return await get_mbs_client().get_package(package_id)

    @mcp.tool
    async def create_package(package_data_json: str) -> Any:
        """[MBS] Create a storage limit package (mutating).

        Use when: defining a new storage limit (Name, StorageLimit in GB, Cost, etc.).
        Not for: assigning to a user — use `add_destination` with PackageID.
        Params: package_data_json (JSON object string).
        """
        return await get_mbs_client().create_package(
            parse_json_object(package_data_json, "package_data_json")
        )

    @mcp.tool
    async def update_package(package_data_json: str) -> Any:
        """[MBS] Update a storage limit package (mutating).

        Use when: changing package properties via JSON body that includes package ID.
        Not for: creating — use `create_package`.
        Params: package_data_json.
        """
        return await get_mbs_client().update_package(
            parse_json_object(package_data_json, "package_data_json")
        )

    @mcp.tool
    async def delete_package(package_id: str) -> Any:
        """[MBS] Delete a storage limit package (mutating).

        Use when: removing an unused storage limit definition.
        Not for: removing user destinations — use `delete_destination`.
        Params: package_id.
        """
        return await get_mbs_client().delete_package(package_id)

    @mcp.tool
    async def get_billing(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List billing records for the current month (paginated).

        Use when: reviewing billing/usage charges in MBS.
        Not for: filtered billing by company/user/date — use `get_billing_filtered`.
        Params: page, limit.
        """
        return await get_mbs_client().get_billing(pagination_params(page, limit))

    @mcp.tool
    async def get_billing_filtered(filter_json: str = "{}") -> Any:
        """[MBS] Get filtered billing / storage usage statistics.

        Use when: billing by company or user. Uses PUT /api/Billing (CompanyName, Date)
        or PUT /api/Billing/Details (UserID, Date).
        Not for: per-computer agent usage — use `backup_rm_get_usage`.
        Params: filter_json — e.g. {"CompanyName": "Acme"}, {"company_id": "..."},
        {"UserID": "...", "Date": "2026-01-01"}.
        """
        filter_data = parse_json_object(filter_json, "filter_json")
        if not filter_data:
            return await get_mbs_client().get_billing()

        client = get_mbs_client()
        company_id = filter_data.get("CompanyId") or filter_data.get("company_id")
        if company_id and not (
            filter_data.get("CompanyName") or filter_data.get("company_name")
        ):
            company = await client.get_company(str(company_id))
            if isinstance(company, dict):
                name = company.get("Name") or company.get("name")
                if name:
                    filter_data["CompanyName"] = name

        return await client.get_filtered_billing(filter_data)

    @mcp.tool
    async def get_company_storage_usage(company_id: str) -> Any:
        """[MBS] Get storage usage for one company (via billing API).

        Use when: reviewing backup storage consumption for a company.
        Not for: per-computer usage — use `backup_rm_get_usage`.
        Params: company_id — resolved to company name, then PUT /api/Billing.
        """
        return await get_mbs_client().get_company_storage_usage(company_id)

    @mcp.tool
    async def storage_usage_report(scope: str, id: str) -> Any:
        """[MBS] Storage usage summary for a company or computer.

        Use when: you need a single structured answer for storage usage by company or computer.
        Not for: raw billing exports — use `get_billing_filtered`.
        Params: scope — `company` or `computer`; id — company_id or computer hid.
        """
        client = get_mbs_client()
        scope_norm = scope.strip().lower()
        if scope_norm == "company":
            company = await client.get_company(id)
            company_name = None
            if isinstance(company, dict):
                company_name = company.get("Name") or company.get("name")
            billing = await client.get_company_storage_usage(id)
            return {
                "scope": "company",
                "company_id": id,
                "company_name": company_name,
                "billing": billing,
                "source": "PUT /api/Billing filtered by company name",
            }
        if scope_norm == "computer":
            usage = await client.get_computer_usage(id)
            return {"scope": "computer", "hid": id, "usage": usage}
        raise ValueError("scope must be 'company' or 'computer'")

    @mcp.tool
    async def get_builds(
        page: int = 1,
        limit: int = 10,
        build_type: Optional[str] = None,
    ) -> Any:
        """[MBS] List available agent builds with download links.

        Use when: downloading or distributing backup agents (returns Type, Version, DownloadLink).
        Not for: storage limits — use `get_packages`.
        Params: page, limit; optional build_type (Windows, LinuxDEB, LinuxRPM, macOS, RMMWindows, ...).
        """
        params = pagination_params(page, limit)
        if build_type:
            params["build_type"] = build_type
        return await get_mbs_client().get_builds(params)

    @mcp.tool
    async def request_custom_builds(build_data_json: str) -> Any:
        """[MBS] Request custom or sandbox agent builds (mutating).

        Use when: requesting branded/custom builds for specific editions.
        Not for: listing public builds — use `get_builds`.
        Params: build_data_json — BuildType and BuildEditions per Swagger.
        """
        return await get_mbs_client().request_custom_builds(
            parse_json_object(build_data_json, "build_data_json")
        )

    @mcp.tool
    async def get_available_versions() -> Any:
        """[MBS] List available agent/build version catalog.

        Use when: choosing which agent version to deploy before calling `get_builds`.
        Not for: download URLs — use `get_builds` (includes DownloadLink).
        Params: none.
        """
        return await get_mbs_client().get_available_versions()

    @mcp.tool
    async def get_user_destinations(user_email: str) -> Any:
        """[MBS] List backup destinations configured for a user email.

        Use when: auditing where a user's backups are stored.
        Not for: storage accounts — use `get_accounts`.
        Params: user_email.
        """
        return await get_mbs_client().get_user_destinations(user_email)

    @mcp.tool
    async def add_destination(destination_data_json: str) -> Any:
        """[MBS] Add a backup destination (mutating).

        Use when: assigning a destination to a user via JSON body.
        Not for: storage account CRUD — use `create_account`.
        Params: destination_data_json.
        """
        return await get_mbs_client().add_destination(
            parse_json_object(destination_data_json, "destination_data_json")
        )

    @mcp.tool
    async def update_destination(destination_data_json: str) -> Any:
        """[MBS] Update a backup destination (mutating).

        Use when: changing destination settings via JSON.
        Not for: deleting — use `delete_destination`.
        Params: destination_data_json.
        """
        return await get_mbs_client().update_destination(
            parse_json_object(destination_data_json, "destination_data_json")
        )

    @mcp.tool
    async def delete_destination(
        destination_id: str, user_id: Optional[str] = None
    ) -> Any:
        """[MBS] Delete a backup destination (mutating).

        Use when: removing a user's destination assignment.
        Not for: revoking computer access — use `backup_rm_remove_authorization`.
        Params: destination_id; optional user_id.
        """
        return await get_mbs_client().delete_destination(destination_id, user_id)

    @mcp.tool
    async def get_admins(page: int = 1, limit: int = 10) -> Any:
        """[MBS] List MSP360 portal administrators (paginated).

        Use when: reviewing who has admin access to the backup console.
        Not for: end users — use `get_users`.
        Params: page, limit.
        """
        return await get_mbs_client().get_administrators(
            pagination_params(page, limit)
        )

    @mcp.tool
    async def get_admin(admin_id: str) -> Any:
        """[MBS] Get one administrator by ID.

        Use when: inspecting a specific admin account and permissions.
        Not for: listing admins — use `get_admins`.
        Params: admin_id.
        """
        return await get_mbs_client().get_administrator(admin_id)

    @mcp.tool
    async def create_admin(admin_data_json: str) -> Any:
        """[MBS] Create a portal administrator (mutating).

        Use when: provisioning an admin with PermissionsModels and Companies in JSON.
        Not for: updates — use `update_admin`.
        Params: admin_data_json — Email, PermissionsModels, Companies, AccessToCompaniesMode, etc.
        """
        return await get_mbs_client().create_administrator(
            parse_json_object(admin_data_json, "admin_data_json")
        )

    @mcp.tool
    async def update_admin(admin_data_json: str) -> Any:
        """[MBS] Update a portal administrator (mutating).

        Use when: changing permissions or company assignment via JSON with AdminID.
        Not for: creating — use `create_admin`.
        Params: admin_data_json — must include AdminID, PermissionsModels, Companies as needed.
        """
        return await get_mbs_client().update_administrator(
            parse_json_object(admin_data_json, "admin_data_json")
        )

    @mcp.tool
    async def delete_admin(admin_id: str) -> Any:
        """[MBS] Delete a portal administrator (mutating).

        Use when: removing admin access from the backup console.
        Not for: deleting end users — use `delete_user`.
        Params: admin_id.
        """
        return await get_mbs_client().delete_administrator(admin_id)
