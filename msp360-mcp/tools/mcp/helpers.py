"""Shared helpers for MCP tool handlers."""
import json
from typing import Any, Dict, Optional


def parse_json_object(value: Optional[str], field_name: str = "body") -> Dict[str, Any]:
    if not value or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {field_name}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def pagination_params(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    return {"page": page, "limit": limit}
