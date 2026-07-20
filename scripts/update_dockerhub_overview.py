#!/usr/bin/env python3
"""Publish docs/dockerhub-overview.md to Docker Hub repository full description."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "docs" / "dockerhub-overview.md"
REPO = "tonyzorin/msp360-mcp"
SHORT_DESCRIPTION = "MCP server for MSP360 Managed Backup and read-only RMM. Cursor & Claude Desktop."


def docker_hub_credentials() -> tuple[str, str]:
    proc = subprocess.run(
        ["docker-credential-desktop", "get"],
        input="https://index.docker.io/v1/\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Could not read Docker credentials. Run `docker login` first.\n"
            + (proc.stderr or proc.stdout)
        )
    data = json.loads(proc.stdout)
    username = data.get("Username") or data.get("username")
    secret = data.get("Secret") or data.get("secret")
    if not username or not secret:
        raise SystemExit("Docker credential helper returned no username/secret")
    return username, secret


def hub_token(username: str, secret: str) -> str:
    payload = json.dumps({"username": username, "password": secret}).encode("utf-8")
    req = urllib.request.Request(
        "https://hub.docker.com/v2/users/login/",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    token = body.get("token")
    if not token:
        raise SystemExit("Docker Hub login did not return a token")
    return token


def patch_repository(token: str, full_description: str) -> None:
    payload = json.dumps(
        {
            "description": SHORT_DESCRIPTION[:256],
            "full_description": full_description,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"https://hub.docker.com/v2/repositories/{REPO}/",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"JWT {token}",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        json.loads(resp.read().decode("utf-8"))


def main() -> int:
    if not OVERVIEW.is_file():
        raise SystemExit(f"Missing overview file: {OVERVIEW}")

    full_description = OVERVIEW.read_text(encoding="utf-8")
    username, secret = docker_hub_credentials()
    token = hub_token(username, secret)
    try:
        patch_repository(token, full_description)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Docker Hub API error {exc.code}: {detail}", file=sys.stderr)
        return 1

    print(f"Updated Docker Hub overview for {REPO}")
    print(f"  short: {SHORT_DESCRIPTION}")
    print(f"  full:  {OVERVIEW} ({len(full_description)} chars)")
    print(f"  url:   https://hub.docker.com/r/{REPO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
