"""
Compatibility module for MSP360 API client.
This module provides backward compatibility for imports from the old location.
"""
import sys
import os
import importlib.util
import logging

# Set up logging
logger = logging.getLogger("msp360_mcp.services.compatibility")

# First, make sure we can import from the services/msp360 directory
services_dir = os.path.dirname(os.path.abspath(__file__))
msp360_dir = os.path.join(services_dir, 'msp360')
client_path = os.path.join(msp360_dir, 'client.py')

# Add parent directory to path
parent_dir = os.path.dirname(services_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the real client directly
try:
    logger.info("Importing MSP360Client directly from services.msp360")
    from services.msp360 import MSP360Client
    from services.msp360 import msp360_client as real_client
    
    # Use the real client directly
    msp360_client = real_client
    
    # For debugging
    logger.info(f"Successfully loaded real MSP360Client: {type(msp360_client)}")
    logger.info(f"Client base URL: {msp360_client.base_url}")
    
except Exception as e:
    logger.error(f"Failed to import MSP360Client: {str(e)}")
    
    # Fall back to the mock implementation if direct import fails
    class MockMSP360Client:
        def __init__(self):
            self._real_client = None
            logger.warning("Using MockMSP360Client - functionality will be limited")
            
        def _ensure_real_client(self):
            if self._real_client is None:
                # Import dynamically when needed
                try:
                    # Try importing from the services/msp360 package
                    from services.msp360 import MSP360Client as RealClient
                    
                    # Create a real client instance
                    self._real_client = RealClient()
                    logger.info("Successfully loaded real client on demand")
                except Exception as e:
                    logger.error(f"Failed to import MSP360Client on demand: {str(e)}")
                    raise ImportError(f"Failed to import MSP360Client: {str(e)}")
            
            return self._real_client
            
        def __getattr__(self, name):
            # Forward all attribute access to the real client
            real_client = self._ensure_real_client()
            return getattr(real_client, name)
    
    # Create a mock client instance only if we couldn't load the real one
    msp360_client = MockMSP360Client()

# Compatibility function
def update_credentials(login, password):
    """Update the API credentials.
    
    Args:
        login: API login
        password: API password
    """
    if hasattr(msp360_client, "update_credentials"):
        logger.info(f"Updating credentials for {login}")
        msp360_client.update_credentials(login, password)
    else:
        logger.error("Cannot update credentials - client not properly initialized")

# Proxy for token manager, only used if we have the mock client
if hasattr(msp360_client, "_ensure_real_client"):
    class TokenManagerProxy:
        def __getattr__(self, name):
            return getattr(msp360_client._ensure_real_client().token_manager, name)
    
    token_manager = TokenManagerProxy()
else:
    # Use the real token manager
    token_manager = msp360_client.token_manager

# Export the client and client class
__all__ = ["msp360_client", "update_credentials", "token_manager"] 