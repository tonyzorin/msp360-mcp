"""Backward-compatible re-export of the MBS client."""
from services.msp360 import get_mbs_client, msp360_client, MSP360Client

__all__ = ["get_mbs_client", "msp360_client", "MSP360Client"]
