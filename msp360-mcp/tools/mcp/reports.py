"""Helpers for MCP monitoring and usage report tools."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional


SUCCESS_STATUS_VALUES = {"success", "0", 0}


def extract_list(payload: Any) -> List[Any]:
    """Normalize API list responses to a flat list."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in (
            "items",
            "Items",
            "data",
            "Data",
            "Computers",
            "computers",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def monitoring_rows(payload: Any) -> List[Dict[str, Any]]:
    rows = extract_list(payload)
    return [row for row in rows if isinstance(row, dict)]


def is_success_status(status: Any) -> bool:
    if status is None:
        return False
    if isinstance(status, int):
        return status == 0
    return str(status).strip().lower() in SUCCESS_STATUS_VALUES


def parse_last_start(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def within_days(last_start: Any, days: Optional[int]) -> bool:
    if days is None or days <= 0:
        return True
    parsed = parse_last_start(last_start)
    if parsed is None:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return parsed >= cutoff


def row_company_name(row: Dict[str, Any]) -> str:
    return str(
        row.get("CompanyName")
        or row.get("companyName")
        or row.get("company_name")
        or "Unknown"
    )


def row_computer_name(row: Dict[str, Any]) -> str:
    return str(
        row.get("ComputerName")
        or row.get("computerName")
        or row.get("computer_name")
        or row.get("Name")
        or "Unknown"
    )


def row_status(row: Dict[str, Any]) -> str:
    status = row.get("Status") if "Status" in row else row.get("status")
    if status is None:
        return "Unknown"
    if isinstance(status, int):
        mapping = {0: "Success", 1: "Warning", 2: "Failed", 3: "Running"}
        return mapping.get(status, str(status))
    return str(status)


def filter_issue_rows(
    rows: Iterable[Dict[str, Any]],
    *,
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for row in rows:
        if company_id:
            row_company_id = (
                row.get("CompanyId")
                or row.get("companyId")
                or row.get("company_id")
            )
            if row_company_id and str(row_company_id) != str(company_id):
                continue

        if not within_days(row.get("LastStart") or row.get("lastStart"), days):
            continue

        row_is_success = is_success_status(
            row.get("Status") if "Status" in row else row.get("status")
        )
        if status:
            if row_status(row).lower() != status.strip().lower():
                continue
        elif row_is_success:
            continue

        issues.append(row)
    return issues


def group_rows(
    rows: Iterable[Dict[str, Any]], group_by: str
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    key_fn = row_company_name if group_by == "company" else row_computer_name
    for row in rows:
        key = key_fn(row)
        grouped.setdefault(key, []).append(row)
    return grouped


def computers_without_success(
    computers: Iterable[Dict[str, Any]],
    monitoring_rows_data: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    success_keys = set()
    for row in monitoring_rows_data:
        if is_success_status(
            row.get("Status") if "Status" in row else row.get("status")
        ):
            success_keys.add(_computer_key(row))

    missing: List[Dict[str, Any]] = []
    for computer in computers:
        if not isinstance(computer, dict):
            continue
        key = _computer_key(computer)
        if key not in success_keys:
            missing.append(computer)
    return missing


def _computer_key(record: Dict[str, Any]) -> str:
    hid = record.get("HID") or record.get("hid") or record.get("Hid")
    if hid:
        return f"hid:{hid}"
    name = (
        record.get("ComputerName")
        or record.get("Name")
        or record.get("computerName")
    )
    company = record.get("CompanyName") or record.get("companyName") or ""
    return f"name:{company}:{name}"
