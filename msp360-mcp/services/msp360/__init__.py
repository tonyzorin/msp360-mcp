"""Services module for MSP360 API integration."""

import sys
import os
import logging

logger = logging.getLogger("msp360_mcp.services")

# Add the project root directory to the path to resolve all imports properly
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(services_dir)
if project_root not in sys.path:
    logger.info(f"Adding project root to Python path: {project_root}")
    sys.path.insert(0, project_root)

# Create a single client instance for use throughout the application
from .client import MSP360Client
msp360_client = MSP360Client()

__all__ = ["msp360_client", "MSP360Client"] 