# Connectors Directory submission guide

Checklist for submitting **MSP360 MCP** as a Claude Desktop extension (`.mcpb`).

Official requirements: [Submitting to the Connectors Directory](https://claude.com/docs/connectors/building/submission) · [Pre-submission checklist](https://claude.com/docs/connectors/building/review-criteria)

## Submission path

| Item | Value |
|------|--------|
| Type | Desktop extension (MCPB) |
| Form | https://clau.de/desktop-extention-submission |
| Bundle | `mcpb/msp360-mcp.mcpb` |
| Docker image | `tonyzorin/msp360-mcp:2.2.2` |
| Source | https://github.com/tonyzorin/msp360-mcp |
| Vendor | https://www.msp360.com/ |

Remote MCP portal submission is **not** required for `.mcpb` installs.

## Repo checklist (implemented in v2.2.2+)

| Requirement | Location |
|-------------|----------|
| Tool `title` + `readOnlyHint` / `destructiveHint` on every tool | `tools/mcp/tool_decorators.py`, all `tools/mcp/*.py` |
| Privacy policy in README | README → **Privacy Policy** |
| `privacy_policies` in manifest | `mcpb/manifest.json` |
| Extension icon (512×512+) | `mcpb/icon.png` |
| Documentation | README, `docs/dockerhub-overview.md` |
| Automated annotation test | `test_mcp_v2.py` → `test_all_tools_have_directory_annotations` |
| Rebuild `.mcpb` after version bump | `./scripts/rebuild_mcpb.sh` |

## Reviewer test account (fill before submit)

Provide Anthropic reviewers a **dedicated sandbox MSP360 tenant** — not production customer data.

```
MBS API login:     <sandbox MSP360_API_LOGIN>
MBS API password:  <sandbox MSP360_API_PASSWORD>
RMM API token:     <optional MSP360_RMM_API_TOKEN>
Test company:      <company name with computers + monitoring data>
Test user ID:      <user with licensed agent>
Test computer HID: <online agent for plan/history tools>
```

### Suggested reviewer smoke test

1. Install extension from released `.mcpb` or build locally.
2. `docker pull tonyzorin/msp360-mcp:2.2.2`
3. Enter sandbox credentials in install UI.
4. New chat → `mcp_server_info` (expect version `2.2.2`, `mbs_configured: true`).
5. Read-only: `get_companies`, `backup_rm_list_computers`, `backup_rm_get_monitoring`, `rmm_fleet_overview`.
6. Write (sandbox only): `get_licenses` with `is_available=true`, then optional `grant_license` on a test user.

### Pre-submit QA (maintainer)

```bash
docker build -t tonyzorin/msp360-mcp:2.2.2 .
docker run --rm --entrypoint python tonyzorin/msp360-mcp:2.2.2 -m pytest test_mcp_v2.py -q
./scripts/rebuild_mcpb.sh
python3 scripts/update_dockerhub_overview.py
```

Exercise **every tool** via MCP Inspector or Claude custom connector against the sandbox tenant before filing the form.

## MCP App carousel assets (manual step)

If highlighting MCP Apps in the listing, capture **3–5 PNG screenshots** (≥1000px wide) of:

| # | Tool | Suggested prompt |
|---|------|------------------|
| 1 | `backup_rm_get_monitoring` | "Show backup plan monitoring dashboard with status breakdown" |
| 2 | `rmm_fleet_overview` | "Show RMM fleet overview with online/offline counts" |
| 3 | `backup_rm_list_issues` | "List backup issues grouped by company" |

Save under `docs/submission/screenshots/` (crop to app UI only — no Claude prompt chrome). Pair each image with the prompt text in the submission form.

Template: [MCP Apps Figma community file](https://www.figma.com/community/file/1597641111449594397/mcp-apps-for-claude)

## Expected install UX

Sideloaded `.mcpb` files show Anthropic's **unverified developer** warning until the extension is **approved in the Connectors Directory**. Directory listing is what removes that warning for customers — not repacking alone.

## Policy links

- [Anthropic Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)
- [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
- Review escalations: mcp-review@anthropic.com
