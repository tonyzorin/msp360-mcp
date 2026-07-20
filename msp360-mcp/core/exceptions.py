"""Domain exceptions for MSP360 MCP server."""


class MSP360APIError(Exception):
    """Raised when an MSP360 API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MSP360ConfigError(Exception):
    """Raised when required credentials or configuration are missing."""
