# Claude Desktop Extension (`.mcpb`)

This folder builds the one-click **Install in Claude Desktop** package.

## Contents

| File | Purpose |
|------|---------|
| `manifest.json` | Extension metadata + Docker `mcp_config` + user credential prompts |
| `server/stub` | Schema placeholder (`mcp_config.command` is `docker`) |
| `msp360-mcp.mcpb` | Packed bundle (commit after rebuild) |

## Rebuild

**Important:** Claude Desktop reads version from the **packed** `msp360-mcp.mcpb`, not from `manifest.json` alone. After any version bump, rebuild and commit the binary.

```bash
# from repo root
./scripts/rebuild_mcpb.sh
# or manually:
npm install -g @anthropic-ai/mcpb
cd mcpb
mcpb validate manifest.json
mcpb pack . ./msp360-mcp.mcpb
cd ..
python3 scripts/verify_mcpb_version.py
```

Requires Docker image `tonyzorin/msp360-mcp:<version>` on the user's machine (tag must match `msp360-mcp/core/version.py`).

After a release, update the Docker Hub page:

```bash
python3 scripts/update_dockerhub_overview.py
```
