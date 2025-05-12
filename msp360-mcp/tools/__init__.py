"""Tools package for MSP360 MCP Server."""
from typing import Dict, Any, List, Callable, Type, Optional
import logging

logger = logging.getLogger("msp360_mcp.tools")

# Dictionary to store registered tools
REGISTERED_TOOLS: Dict[str, Dict[str, Any]] = {}

def register_tool(
    tool_name: str, 
    description: str, 
    function: Callable,
    parameter_descriptions: Optional[Dict[str, str]] = None
) -> None:
    """
    Register a tool with the MCP server.
    
    Args:
        tool_name: Name of the tool
        description: Description of what the tool does
        function: Function to call when the tool is invoked
        parameter_descriptions: Dictionary mapping parameter names to descriptions
    """
    if tool_name in REGISTERED_TOOLS:
        logger.warning(f"Tool {tool_name} already registered, overwriting")
        
    REGISTERED_TOOLS[tool_name] = {
        "description": description,
        "function": function,
        "parameter_descriptions": parameter_descriptions or {}
    }
    
    logger.info(f"Registered tool: {tool_name}")
    
def get_tool_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Get all registered tool definitions.
    
    Returns:
        Dictionary of tool definitions
    """
    return REGISTERED_TOOLS

def get_tool_list() -> List[str]:
    """
    Get a list of all registered tool names.
    
    Returns:
        List of tool names
    """
    return list(REGISTERED_TOOLS.keys())

def get_tool(tool_name: str) -> Dict[str, Any]:
    """
    Get a specific tool definition by name.
    
    Args:
        tool_name: Name of the tool to get
        
    Returns:
        Tool definition dictionary
    
    Raises:
        KeyError: If the tool doesn't exist
    """
    if tool_name not in REGISTERED_TOOLS:
        raise KeyError(f"Tool {tool_name} not registered")
        
    return REGISTERED_TOOLS[tool_name]

# Import tool modules for convenient access
# These are still initialized by MCPServer to avoid circular imports
from .accounts import AccountTools
from .destinations import DestinationTools
from .admin import AdminTools
from .computers import ComputerTools
from .users import UserTools
from .companies import CompanyTools
from .builds import BuildsTools
from .packages import PackageTools
from .licenses import LicensesTools
from .reports import ReportTools
from .backup import BackupTools
from .billing import BillingTools

# Import utility functions
from .utils import (
    format_size, 
    humanize_time, 
    format_json_field, 
    parse_params_json,
    convert_pagination,
    normalize_field_names
)

# Don't import tool modules here to avoid circular imports
# MCPServer will handle all tool registration 