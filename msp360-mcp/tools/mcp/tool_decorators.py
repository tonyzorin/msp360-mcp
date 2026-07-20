"""Anthropic Connectors Directory tool annotation helpers."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from fastmcp import FastMCP

F = TypeVar("F", bound=Callable[..., Any])

READ_ONLY = {"readOnlyHint": True}
WRITE = {"destructiveHint": True}


def readonly(mcp: FastMCP, title: str, **tool_kw: Any) -> Callable[[F], F]:
    """Register a read-only MCP tool with directory-required annotations."""

    def decorator(fn: F) -> F:
        return mcp.tool(title=title, annotations=READ_ONLY, **tool_kw)(fn)

    return decorator


def write(mcp: FastMCP, title: str, **tool_kw: Any) -> Callable[[F], F]:
    """Register a mutating MCP tool with directory-required annotations."""

    def decorator(fn: F) -> F:
        return mcp.tool(title=title, annotations=WRITE, **tool_kw)(fn)

    return decorator
