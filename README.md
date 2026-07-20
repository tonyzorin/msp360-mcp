# MSP360 MCP Server v2

[Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for **MSP360 Managed Backup** and **read-only RMM** endpoint statistics.

Connect Cursor, Claude Desktop, or any STDIO MCP client to MSP360 APIs — list computers, manage licenses and backup plans, pull monitoring data, and inspect fleet health — through tool calls instead of raw HTTP.

**Vendor:** [MSP360](https://www.msp360.com/) — Managed Backup and RMM platform this server integrates with.

**Current image:** `tonyzorin/msp360-mcp:2.2.1`

### Quick add

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=MSP360&config=eyJjb21tYW5kIjoiZG9ja2VyIiwiYXJncyI6WyJydW4iLCItaSIsIi1lIiwiTVNQMzYwX0FQSV9MT0dJTj1ZT1VSX0FQSV9MT0dJTiIsIi1lIiwiTVNQMzYwX0FQSV9QQVNTV09SRD1ZT1VSX0FQSV9QQVNTV09SRCIsIi1lIiwiTVNQMzYwX1JNTV9BUElfVE9LRU49WU9VUl9STU1fVE9LRU4iLCItZSIsIkFQSV9USU1FT1VUPTYwIiwidG9ueXpvcmluL21zcDM2MC1tY3A6Mi4yLjEiXX0%3D)
[![Install in Claude Desktop](https://img.shields.io/badge/Install_in-Claude_Desktop-191919?style=for-the-badge&logo=anthropic&logoColor=white)](https://github.com/tonyzorin/msp360-mcp/raw/main/mcpb/msp360-mcp.mcpb)

| Host | Install path |
|------|--------------|
| **Cursor** | One-click deeplink above → Docker STDIO prefilled ([install-link docs](https://cursor.com/docs/mcp/install-links)) |
| **Claude Desktop** | Downloads [`msp360-mcp.mcpb`](https://github.com/tonyzorin/msp360-mcp/raw/main/mcpb/msp360-mcp.mcpb) — open/double-click to install as a [Desktop Extension](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop), then enter API credentials in the install UI |

**Before either install:** `docker pull tonyzorin/msp360-mcp:2.2.1` (Docker must be running).

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- MSP360 API credentials for the surfaces you need:
  - **Managed Backup (MBS):** API login + password  
  - **RMM (optional):** bearer token for `api.rmm.mspbackups.com`

You can set either credential set alone. The server starts and registers only the tools that can run.

---

## Install the Docker image

### Option A — Pull the published image

```bash
docker pull tonyzorin/msp360-mcp:2.2.1
```

### Option B — Build from this repo

```bash
git clone https://github.com/tonyzorin/msp360-mcp.git
cd msp360-mcp
docker build -t tonyzorin/msp360-mcp:2.2.1 .
```

---

## Configure Cursor or Claude Desktop

Both hosts use the same Docker STDIO pattern.

### Cursor

1. Click **Install in Cursor** above (or open the [install link](https://cursor.com/en/install-mcp?name=MSP360&config=eyJjb21tYW5kIjoiZG9ja2VyIiwiYXJncyI6WyJydW4iLCItaSIsIi1lIiwiTVNQMzYwX0FQSV9MT0dJTj1ZT1VSX0FQSV9MT0dJTiIsIi1lIiwiTVNQMzYwX0FQSV9QQVNTV09SRD1ZT1VSX0FQSV9QQVNTV09SRCIsIi1lIiwiTVNQMzYwX1JNTV9BUElfVE9LRU49WU9VUl9STU1fVE9LRU4iLCItZSIsIkFQSV9USU1FT1VUPTYwIiwidG9ueXpvcmluL21zcDM2MC1tY3A6Mi4yLjEiXX0%3D)).
2. Confirm the install prompt in Cursor.
3. Edit the saved MCP entry and replace the credential placeholders.
4. Ensure the image is available (`docker pull tonyzorin/msp360-mcp:2.2.1`), then reload MCP / restart Cursor.

Manual alternative: project `.cursor/mcp.json` or global Cursor MCP settings — same JSON as [`mcp.json.example`](mcp.json.example).

### Claude Desktop

<a id="claude-desktop"></a>

**Recommended — Desktop Extension (one-click):**

1. `docker pull tonyzorin/msp360-mcp:2.2.1`
2. Click **Install in Claude Desktop** above (or download [`mcpb/msp360-mcp.mcpb`](mcpb/msp360-mcp.mcpb)).
3. Open the downloaded `.mcpb` file (double-click, or drag into Claude Desktop, or Settings → Extensions → Advanced → Install Extension…).
4. Enter **API Login**, **API Password**, and optional **RMM Token** in the install UI.
5. Confirm install, then ask for `mcp_server_info` in a new chat.

See Anthropic’s [local MCP / Desktop Extensions guide](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

**Alternative — config file** (same Docker STDIO JSON as Cursor):

| OS | Config path |
|----|-------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Merge in the JSON from [`mcp.json.example`](mcp.json.example), replace placeholders, then fully quit and reopen Claude Desktop.

### Credentials tips

- Omit `-e MSP360_RMM_API_TOKEN=...` if you only need Managed Backup tools.
- Omit MBS login/password if you only need RMM tools.
- Never commit real credentials to git. Keep secrets in local MCP config only.

---

## How to use

Once the server is connected, the host’s AI can call MSP360 tools directly. Prefer tool calls over curl or hand-written API scripts.

### Start here

| Goal | Tool |
|------|------|
| Check version & which APIs are live | `mcp_server_info` |
| List managed computers | `backup_rm_list_computers` |
| Backup plan run status | `backup_rm_get_monitoring` |
| Fleet health (RMM summary) | `rmm_fleet_overview` |
| Discover RMM stat types | `rmm_list_stat_types` |
| Licenses | `get_licenses`, `grant_license`, `release_license`, `revoke_license` |

### Product surfaces (routing)

| Prefix / names | API | Typical use |
|----------------|-----|-------------|
| Plain names (`get_users`, `get_companies`, …) | MBS admin | Users, companies, accounts, packages, billing, builds, destinations, admins |
| `get_licenses`, `grant_license`, … | MBS licensing | License inventory and assignments |
| `backup_rm_*` | Backup Remote Management | Computers, plans, history, monitoring on `api.mspbackups.com` |
| `rmm_*` | RMM (read-only) | Endpoint stats on `api.rmm.mspbackups.com` |

**Do not mix:** `backup_rm_get_monitoring` is backup **plan run** status. `rmm_fleet_overview` / `rmm_get_*_stat` are **endpoint health** stats.

### Example prompts

- “Call `mcp_server_info` and tell me what’s configured.”
- “List my backup computers and show which are online.”
- “Show RMM fleet overview and highlight alarms.”
- “List available licenses and which ones are taken.”

### MCP Apps (visuals)

Some tools ship optional HTML UIs ([MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview)):

| Tool | UI |
|------|----|
| `backup_rm_get_monitoring` | Status chart for plan runs |
| `rmm_fleet_overview` | Fleet cards + CPU / RAM / HDD bars |

- **Claude Desktop** (and other Apps-capable hosts): may render an interactive widget next to the tool result.
- **Cursor:** JSON only today; the same tools still return full structured data.

Full tool list: [All MCP tools](#all-mcp-tools) at the bottom of this README.

---

## Environment variables

| Variable | Required for | Description |
|----------|--------------|-------------|
| `MSP360_API_LOGIN` | MBS tools | Managed Backup API login |
| `MSP360_API_PASSWORD` | MBS tools | Managed Backup API password |
| `MSP360_RMM_API_TOKEN` | RMM tools | RMM API bearer token |
| `MSP360_API_BASE_URL` | — | Default `https://api.mspbackups.com` |
| `MSP360_RMM_API_BASE_URL` | — | Default `https://api.rmm.mspbackups.com` |
| `API_TIMEOUT` | — | HTTP timeout in seconds (default `60`) |
| `MCP_TRANSPORT` | — | `stdio` (default) or `http` |
| `PORT` / `HOST` | HTTP mode | Bind address (default `51817` / `0.0.0.0`) |

### Optional: Streamable HTTP

For remote MCP hosts that speak Streamable HTTP (not legacy SSE):

```bash
docker run --rm -p 51817:51817 \
  -e MCP_TRANSPORT=http \
  -e MSP360_API_LOGIN=YOUR_API_LOGIN \
  -e MSP360_API_PASSWORD=YOUR_API_PASSWORD \
  tonyzorin/msp360-mcp:2.2.1
```

---

## Develop from source

The rest of this README uses **Docker** to run MCP (Cursor, Claude Desktop, production-like STDIO). Use the same approach for development — you get Python 3.14 and dependencies without installing them locally.

### Recommended — Docker (matches production)

```bash
git clone https://github.com/tonyzorin/msp360-mcp.git
cd msp360-mcp
docker build -t tonyzorin/msp360-mcp:2.2.1 .

# Run unit/smoke tests
docker run --rm --entrypoint python tonyzorin/msp360-mcp:2.2.1 -m pytest test_mcp_v2.py

# Run the server (STDIO — same as MCP hosts; use --debug for verbose logs)
docker run --rm -i \
  -e MSP360_API_LOGIN=YOUR_API_LOGIN \
  -e MSP360_API_PASSWORD=YOUR_API_PASSWORD \
  -e MSP360_RMM_API_TOKEN=YOUR_RMM_TOKEN \
  tonyzorin/msp360-mcp:2.2.1 --debug

# Live code mount while editing (rebuild not needed for Python changes)
docker run --rm -i \
  -v "$(pwd)/msp360-mcp:/app/msp360-mcp" \
  -e MSP360_API_LOGIN=YOUR_API_LOGIN \
  -e MSP360_API_PASSWORD=YOUR_API_PASSWORD \
  tonyzorin/msp360-mcp:2.2.1 --debug
```

Point Cursor or Claude Desktop at the locally built image tag (`tonyzorin/msp360-mcp:2.2.1`) instead of pulling.

### Optional — native Python

Use this only if you already have **Python 3.14** locally and want a faster edit-run loop without Docker:

```bash
git clone https://github.com/tonyzorin/msp360-mcp.git
cd msp360-mcp
pip install -r requirements.txt
export PYTHONPATH=msp360-mcp
export MSP360_API_LOGIN=YOUR_API_LOGIN
export MSP360_API_PASSWORD=YOUR_API_PASSWORD
# optional:
# export MSP360_RMM_API_TOKEN=YOUR_RMM_TOKEN

python msp360-mcp/main.py --debug
pytest test_mcp_v2.py
```

Requires **Python 3.14** (same as the Docker image).

---

## Version history

| Tag | Notes |
|-----|--------|
| `1.0.1` | Legacy custom STDIO server |
| `2.0.0` | FastMCP rewrite, full Backup RM, read-only RMM |
| `2.2.0` | Semantic tool descriptions, routing instructions, MCP Apps MVP |
| `2.2.1` | Admin write, storage limit packages CRUD, builds download, usage/issue report helpers |

**2.0 → 2.2 renames:** `get_user_computers` → `backup_rm_list_user_computers`; `get_monitoring_item` → `backup_rm_get_monitoring_item`.

---

## API documentation

- [MSP360 website](https://www.msp360.com/)
- [MBS API — get started](https://mspbackups.com/AP/Help/mbs-api-specification/get-started-api)
- [MBS Swagger](https://api.mspbackups.com/Swagger/)
- [RMM Swagger](https://api.rmm.mspbackups.com/swagger/index.html)
- Local RMM OpenAPI snapshot: [`docs/rmm-openapi.json`](docs/rmm-openapi.json)

---

<a id="all-mcp-tools"></a>

## All MCP tools

Full catalog for **v2.2.1**. Which tools register depends on your credentials — call `mcp_server_info` first.

| Credential | Tools |
|------------|-------|
| Always | Meta |
| `MSP360_API_LOGIN` + `MSP360_API_PASSWORD` | MBS admin, licensing, Backup RM |
| `MSP360_RMM_API_TOKEN` | RMM (read-only) |

**Routing:** plain names = MBS admin · `backup_rm_*` = Backup Remote Management · `rmm_*` = RMM stats.

**Renamed since v1:** `get_user_computers` → `backup_rm_list_user_computers` · `get_monitoring_data` / `get_monitoring_item` → `backup_rm_get_monitoring` / `backup_rm_get_monitoring_item` · computer/plan tools now use the `backup_rm_*` prefix.

### Meta

| Tool | Description | Parameters |
|------|-------------|------------|
| `mcp_server_info` | Version and which API surfaces are configured | — |

### Users (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_users` | List Managed Backup users | `page`, `limit` |
| `get_user` | Get one user | `user_id` |
| `create_user` | Create user | `user_data_json` |
| `update_user` | Update user | `user_data_json` |
| `delete_user` | Delete user | `user_id` |

### Companies (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_companies` | List companies | `page`, `limit` |
| `get_company` | Get one company | `company_id` |
| `create_company` | Create company (incl. `StorageLimit` in JSON) | `company_data_json` |
| `update_company` | Update company | `company_data_json` |
| `delete_company` | Delete company | `company_id` |

### Storage accounts (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_accounts` | List cloud storage accounts | `page`, `limit` |
| `get_account` | Get one account | `account_id` |
| `create_account` | Create account | `account_data_json` |
| `update_account` | Update account | `account_data_json` |

### Storage limits / packages (MBS)

Packages API = **storage limits**, not agent installers.

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_packages` | List storage limit packages | `page`, `limit` |
| `get_package` | Get one package | `package_id` |
| `create_package` | Create storage limit | `package_data_json` |
| `update_package` | Update storage limit | `package_data_json` |
| `delete_package` | Delete storage limit | `package_id` |

### Destinations (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_user_destinations` | List destinations for a user email | `user_email` |
| `add_destination` | Add destination (assign `PackageID` in JSON) | `destination_data_json` |
| `update_destination` | Update destination | `destination_data_json` |
| `delete_destination` | Delete destination | `destination_id`, optional `user_id` |

### Agent downloads / builds (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_builds` | List builds with `DownloadLink` | `page`, `limit`, optional `build_type` |
| `get_available_versions` | Version catalog | — |
| `request_custom_builds` | Request custom/sandbox builds | `build_data_json` |

### Billing and storage usage (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_billing` | Billing for current month | `page`, `limit` |
| `get_billing_filtered` | Filtered billing (PUT `/api/Billing` or `/Details`) | `filter_json` — `CompanyName`, `company_id`, `UserID`, `Date` |
| `get_company_storage_usage` | Company storage via billing API | `company_id` |
| `storage_usage_report` | Usage summary | `scope` (`company` or `computer`), `id` |

### Administrators (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_admins` | List portal admins | `page`, `limit` |
| `get_admin` | Get one admin | `admin_id` |
| `create_admin` | Create admin (`PermissionsModels`, `Companies` in JSON) | `admin_data_json` |
| `update_admin` | Update admin | `admin_data_json` (includes `AdminID`) |
| `delete_admin` | Delete admin | `admin_id` |

### Licensing (MBS)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_licenses` | List/filter licenses | `is_available`, `page`, `limit`, `company_id`, `user_id`, `edition`, `license_type`, `status` |
| `get_license` | Get one license | `license_id` |
| `grant_license` | Assign license to user | `license_id`, `user_id` |
| `release_license` | Release license seat | `license_id`, optional `user_id` or `computer_id` |
| `revoke_license` | Revoke license | `license_id`, optional `user_id` |

### Backup Remote Management — computers

| Tool | Description | Parameters |
|------|-------------|------------|
| `backup_rm_list_computers` | List managed computers | `offset`, `count`, optional `company_id`, `user_id`, `search`, `online` |
| `backup_rm_get_computer` | Get one computer | `hid` |
| `backup_rm_get_computer_disks` | Disk layout | `hid` |
| `backup_rm_list_user_computers` | Computers for a user | `user_id`, `page`, `limit` |
| `backup_rm_update_authorization` | Authorize / change company | `hid`, `auth_data_json` |
| `backup_rm_remove_authorization` | Remove authorization | `hid` |
| `backup_rm_get_statistics` | Backup statistics | `hid` |
| `backup_rm_get_usage` | Per-computer storage usage | `hid` |

### Backup Remote Management — plans

| Tool | Description | Parameters |
|------|-------------|------------|
| `backup_rm_list_plans` | List plans on computer | `hid` |
| `backup_rm_create_plan` | Create plan (File/IBB in JSON) | `hid`, `plan_data_json` |
| `backup_rm_get_plan` | Get plan | `hid`, `plan_id` |
| `backup_rm_update_plan` | Update plan | `hid`, `plan_id`, `plan_data_json` |
| `backup_rm_delete_plan` | Delete plan | `hid`, `plan_id` |
| `backup_rm_get_plan_info` | Extended plan info | `hid`, `plan_id` |
| `backup_rm_start_plan` | Start/run plan | `hid`, `plan_id`, optional `mode` |
| `backup_rm_stop_plan` | Stop running plan | `hid`, `plan_id`, optional `force` |

### Backup Remote Management — history and monitoring

| Tool | Description | Parameters |
|------|-------------|------------|
| `backup_rm_plans_history` | Global plan run history | `offset`, `count` |
| `backup_rm_computer_plans_history` | History for one computer | `hid`, `offset`, `count` |
| `backup_rm_plan_history` | History for one plan | `hid`, `plan_id` |
| `backup_rm_get_monitoring` | Plan run status dashboard (MCP App) | `page`, `limit`, optional `user_id`, `company_id`, `status` |
| `backup_rm_get_monitoring_for_user` | Monitoring for one user | `user_id`, `page`, `limit` |
| `backup_rm_get_monitoring_item` | One monitoring row | `item_id` |
| `backup_rm_list_issues` | Failed/warning runs (latest monitoring) | optional `company_id`, `status`, `group_by`, `days`, `max_pages`, `limit` |
| `backup_rm_computers_without_success` | Computers with no Success in monitoring | optional `company_id`, `max_pages`, `limit` |

### RMM — read-only

| Tool | Description | Parameters |
|------|-------------|------------|
| `rmm_list_stat_types` | Valid `stat_type` values | — |
| `rmm_get_computer_stat` | One computer stat | `hid`, `stat_type`, optional `mbs_stage_key` |
| `rmm_get_computers_stat` | Fleet stat rows | `stat_type`, `page_number`, `page_size`, optional `mbs_stage_key` |
| `rmm_fleet_overview` | Fleet health summary (MCP App) | `page_number`, `page_size`, optional `mbs_stage_key` |

---

## License

See [LICENSE](LICENSE).
