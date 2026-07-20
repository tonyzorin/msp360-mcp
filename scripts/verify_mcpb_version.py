#!/usr/bin/env python3
"""Fail if packed .mcpb version or Docker tag drifts from SERVER_VERSION."""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_PY = ROOT / "msp360-mcp" / "core" / "version.py"
MANIFEST = ROOT / "mcpb" / "manifest.json"
MCPB = ROOT / "mcpb" / "msp360-mcp.mcpb"


def read_server_version() -> str:
    text = VERSION_PY.read_text(encoding="utf-8")
    match = re.search(r'SERVER_VERSION\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit(f"Could not parse SERVER_VERSION from {VERSION_PY}")
    return match.group(1)


def main() -> int:
    expected = read_server_version()
    errors: list[str] = []

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("version") != expected:
        errors.append(f"mcpb/manifest.json version={manifest.get('version')!r}, expected {expected!r}")

    docker_args = manifest.get("server", {}).get("mcp_config", {}).get("args", [])
    docker_tag = docker_args[-1] if docker_args else ""
    if docker_tag != f"tonyzorin/msp360-mcp:{expected}":
        errors.append(f"manifest Docker tag={docker_tag!r}, expected tonyzorin/msp360-mcp:{expected!r}")

    if not MCPB.is_file():
        errors.append(f"missing packed bundle: {MCPB}")
    else:
        with zipfile.ZipFile(MCPB) as zf:
            packed = json.loads(zf.read("manifest.json").decode("utf-8"))
        if packed.get("version") != expected:
            errors.append(
                f"packed mcpb/msp360-mcp.mcpb version={packed.get('version')!r}, expected {expected!r} "
                "(run: cd mcpb && mcpb pack . ./msp360-mcp.mcpb)"
            )

    if errors:
        print("MCPB release version check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: manifest, packed .mcpb, and Docker tag match SERVER_VERSION={expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
