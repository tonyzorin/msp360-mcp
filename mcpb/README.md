# Claude Desktop Extension (`.mcpb`)

This folder builds the one-click **Install in Claude Desktop** package.

## Contents

| File | Purpose |
|------|---------|
| `manifest.json` | Extension metadata + Docker `mcp_config` + user credential prompts |
| `server/stub` | Schema placeholder (`mcp_config.command` is `docker`) |
| `msp360-mcp.mcpb` | Packed bundle (commit after rebuild) |

## Rebuild

```bash
npm install -g @anthropic-ai/mcpb
cd mcpb
mcpb validate manifest.json
mcpb pack . ./msp360-mcp.mcpb
```

Requires Docker image `tonyzorin/msp360-mcp:2.2.1` on the user's machine.
