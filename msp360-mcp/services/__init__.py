"""Services package for MSP360 MCP Server."""
import sys
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Add the project root directory to the path to resolve all imports properly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    logger.info(f"Adding project root to Python path: {project_root}")
    sys.path.insert(0, project_root)

# Import directly from the msp360 package
try:
    # Import from the msp360 package directly
    from .msp360 import msp360_client
    logger.info("Successfully imported msp360_client from msp360 package")
except ImportError as e:
    logger.error(f"Failed to import msp360_client from msp360 package: {e}")
    
    # Fall back to the compatibility layer if direct import fails
    try:
        from .msp360_client import msp360_client
        logger.info("Successfully imported msp360_client from compatibility layer")
    except ImportError as e:
        logger.error(f"Failed to import msp360_client from compatibility layer: {e}")
        # Create a placeholder
        msp360_client = None

# If we still don't have msp360_client, warn about it
if msp360_client is None:
    logger.warning("msp360_client could not be imported - functionality will be limited")

__all__ = ["msp360_client"] 