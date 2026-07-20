# MSP360 MCP Server v2

[Model Context Protocol](https://modelcontextprotocol.io/) server for **MSP360 Managed Backup** and **read-only RMM** endpoint statistics.

Connect **Cursor**, **Claude Desktop**, or any STDIO MCP client to MSP360 APIs — manage users, licenses, backup plans, monitoring, and fleet health through tool calls instead of raw HTTP.

**Vendor:** [MSP360](https://www.msp360.com/) — Managed Backup and RMM platform this server integrates with.

**Current tags:** `2.2.1`, `latest`  
**Source:** https://github.com/tonyzorin/msp360-mcp

---

## Quick start

```bash
docker pull tonyzorin/msp360-mcp:2.2.1
```

### Cursor / Claude Desktop (STDIO)

Use the same Docker pattern in your MCP config (`mcp.json` or Claude Desktop extension):

```json
{
  "mcpServers": {
    "MSP360": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "-e", "MSP360_API_LOGIN=YOUR_API_LOGIN",
        "-e", "MSP360_API_PASSWORD=YOUR_API_PASSWORD",
        "-e", "MSP360_RMM_API_TOKEN=YOUR_RMM_TOKEN",
        "-e", "API_TIMEOUT=60",
        "tonyzorin/msp360-mcp:2.2.1"
      ]
    }
  }
}
```

**Claude Desktop (recommended):** install the one-click [Desktop Extension](https://github.com/tonyzorin/msp360-mcp/raw/main/mcpb/msp360-mcp.mcpb), enter credentials in the install UI, then ask for `mcp_server_info`.

Omit `MSP360_RMM_API_TOKEN` for Managed Backup only. Omit MBS login/password for RMM-only tools.

---

## Prerequisites

- Docker installed and running
- **Managed Backup (MBS):** API login + password
- **RMM (optional):** bearer token for `api.rmm.mspbackups.com`

Either credential set alone is valid — the server registers only the tools that can run.

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
| `PORT` / `HOST` | HTTP mode | Default `51817` / `0.0.0.0` |

### Streamable HTTP (optional)

```bash
docker run --rm -p 51817:51817 \
  -e MCP_TRANSPORT=http \
  -e MSP360_API_LOGIN=YOUR_API_LOGIN \
  -e MSP360_API_PASSWORD=YOUR_API_PASSWORD \
  tonyzorin/msp360-mcp:2.2.1
```

---

## How to use

Once connected, call MSP360 tools directly (prefer tools over curl).

| Goal | Tool |
|------|------|
| Check version & configured APIs | `mcp_server_info` |
| List managed computers | `backup_rm_list_computers` |
| Backup plan run status | `backup_rm_get_monitoring` |
| Fleet health (RMM) | `rmm_fleet_overview` |
| RMM stat types | `rmm_list_stat_types` |
| Licenses | `get_licenses`, `grant_license`, `release_license`, `revoke_license` |

### Product surfaces

| Prefix / names | API | Use |
|----------------|-----|-----|
| Plain names (`get_users`, `get_companies`, …) | MBS admin | Users, companies, accounts, packages, billing, builds, destinations, admins |
| `get_licenses`, `grant_license`, … | Licensing | License pool and assignments |
| `backup_rm_*` | Backup Remote Management | Computers, plans, history, monitoring |
| `rmm_*` | RMM (read-only) | Endpoint stats |

**Do not mix:** `backup_rm_get_monitoring` = backup **plan run** status. `rmm_fleet_overview` = **endpoint health** stats.

Full tool catalog: https://github.com/tonyzorin/msp360-mcp#all-mcp-tools

---

## Tags

| Tag | Notes |
|-----|--------|
| `2.2.1` | Current release — admin write, packages CRUD, builds download, usage/issue helpers |
| `2.2.0` | Semantic tool descriptions, MCP Apps MVP |
| `2.0.0` | FastMCP rewrite, full Backup RM, read-only RMM |
| `latest` | Points to current stable (`2.2.1`) |

---

## Build from source

```bash
git clone https://github.com/tonyzorin/msp360-mcp.git
cd msp360-mcp
docker build -t tonyzorin/msp360-mcp:2.2.1 .
docker run --rm --entrypoint python tonyzorin/msp360-mcp:2.2.1 -m pytest test_mcp_v2.py
```

---

## Links

- **MSP360 (vendor):** https://www.msp360.com/
- GitHub: https://github.com/tonyzorin/msp360-mcp
- MBS API docs: https://mspbackups.com/AP/Help/mbs-api-specification/get-started-api
- RMM Swagger: https://api.rmm.mspbackups.com/swagger/index.html
- Issues: https://github.com/tonyzorin/msp360-mcp/issues

## License

MIT — see [LICENSE](https://github.com/tonyzorin/msp360-mcp/blob/main/LICENSE).
