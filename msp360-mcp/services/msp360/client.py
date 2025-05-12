"""Main MSP360 API client combining all specialized clients."""
import logging
from typing import Dict, Any, Optional

from .auth import TokenManager
from .client_base import MSP360ClientBase
from .users_client import UsersClient
from .companies_client import CompaniesClient
from .backup_client import BackupClient
from .packages_client import PackagesClient
from .accounts_client import AccountsClient
from .billing_client import BillingClient
from .computers_client import ComputersClient
from .destinations_client import DestinationsClient
from .administrators_client import AdministratorsClient
from .licenses_client import LicensesClient

logger = logging.getLogger("msp360_mcp.client")

class MSP360Client(
    UsersClient, 
    CompaniesClient, 
    BackupClient, 
    PackagesClient,
    AccountsClient,
    BillingClient,
    ComputersClient,
    DestinationsClient,
    AdministratorsClient,
    LicensesClient
):
    """
    Unified client for MSP360 API providing access to all endpoints.
    
    This client inherits from all specialized clients, combining their
    functionality into a single client.
    """
    
    def __init__(self):
        """Initialize the MSP360 client."""
        # Initialize the base client (will create the token manager)
        MSP360ClientBase.__init__(self)
        logger.info("MSP360 Client initialized")
        
    def close(self):
        """Close the client and release resources."""
        logger.info("Closing MSP360 Client")
        
    def __repr__(self) -> str:
        """Return string representation of client."""
        return f"MSP360Client(url={self.base_url})" 