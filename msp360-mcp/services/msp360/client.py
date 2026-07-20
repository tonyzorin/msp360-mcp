"""Main MSP360 MBS API client combining all specialized clients."""
import logging

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
    LicensesClient,
):
    """Unified client for MSP360 Managed Backup API."""

    def __init__(self):
        MSP360ClientBase.__init__(self)
        logger.info("MSP360 MBS client initialized")

    def __repr__(self) -> str:
        return f"MSP360Client(url={self.base_url})"
