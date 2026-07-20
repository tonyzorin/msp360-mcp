#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/mcpb"

if ! command -v mcpb >/dev/null 2>&1; then
  echo "Install mcpb: npm install -g @anthropic-ai/mcpb" >&2
  exit 1
fi

mcpb validate manifest.json
mcpb pack . ./msp360-mcp.mcpb

cd "$ROOT"
python3 scripts/verify_mcpb_version.py

echo "Rebuilt mcpb/msp360-mcp.mcpb — commit the binary before pushing to GitHub."
