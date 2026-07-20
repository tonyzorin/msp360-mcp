"""Services module for MSP360 API integration."""

import logging
from typing import Optional

from core.config import settings
from core.exceptions import MSP360ConfigError

logger = logging.getLogger("msp360_mcp.services")

_mbs_client = None
_rmm_client = None


def get_mbs_client():
    """Return the MBS client singleton, or raise if not configured."""
    global _mbs_client
    if not settings.mbs_configured:
        raise MSP360ConfigError(
            "MBS API not configured. Set MSP360_API_LOGIN and MSP360_API_PASSWORD."
        )
    if _mbs_client is None:
        from .client import MSP360Client

        _mbs_client = MSP360Client()
    return _mbs_client


def get_rmm_client():
    """Return the RMM client singleton, or raise if not configured."""
    global _rmm_client
    if not settings.rmm_configured:
        raise MSP360ConfigError(
            "RMM API not configured. Set MSP360_RMM_API_TOKEN."
        )
    if _rmm_client is None:
        from .rmm_client import RMMClient

        _rmm_client = RMMClient()
    return _rmm_client


def mbs_available() -> bool:
    return settings.mbs_configured


def rmm_available() -> bool:
    return settings.rmm_configured


# Backward-compatible alias used by legacy imports
def _lazy_mbs_client():
    return get_mbs_client() if settings.mbs_configured else None


class _LazyMBSProxy:
    def __getattr__(self, name):
        return getattr(get_mbs_client(), name)


msp360_client = _LazyMBSProxy()

__all__ = [
    "get_mbs_client",
    "get_rmm_client",
    "mbs_available",
    "rmm_available",
    "msp360_client",
    "MSP360Client",
]

from .client import MSP360Client  # noqa: E402
