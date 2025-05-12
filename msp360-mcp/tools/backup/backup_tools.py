"""Base backup tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from .backup_crud import (
    get_monitoring_data_list,
    get_monitoring_item_detail,
    get_user_monitoring_data,
    get_detailed_report_data
)

logger = logging.getLogger("msp360_mcp.tools")

class BackupTools:
    """Tools for interacting with MSP360/CloudBerry backup operations."""
    
    class MonitoringParams(BaseModel):
        """Parameters model for filtering monitoring data."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        user_id: Optional[str] = Field(None, description="Filter by user ID")
        company_id: Optional[str] = Field(None, description="Filter by company ID")
        from_date: Optional[datetime] = Field(None, description="Filter by start date")
        to_date: Optional[datetime] = Field(None, description="Filter by end date")
        status: Optional[str] = Field(None, description="Filter by backup status")
    
    def __init__(self):
        """Initialize the backup tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        logger.info("BackupTools initialized")
        
    def _register_tools(self):
        """Register all backup tools with the tool registry."""
        # Define get_monitoring_data tool
        self._tool_definitions["get_monitoring_data"] = {
            "description": "Get monitoring data for MSP360 backup/restore plans with optional filtering",
            "function": self.get_monitoring_data,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters (page, limit, user_id, company_id, from_date, to_date, status)"
            },
            "parameters": {
                "params": {
                    "description": "JSON string with filter parameters (page, limit, user_id, company_id, from_date, to_date, status)",
                    "type": "string", 
                    "default": "{\"page\": 1, \"limit\": 10}"
                }
            }
        }
        
        # Define get_monitoring_item tool
        self._tool_definitions["get_monitoring_item"] = {
            "description": "Get a specific MSP360 monitoring item by ID",
            "function": self.get_monitoring_item,
            "parameter_descriptions": {
                "item_id": "Monitoring item ID"
            }
        }
        
        # Define get_user_monitoring tool
        self._tool_definitions["get_user_monitoring"] = {
            "description": "Get monitoring data for a specific MSP360 user",
            "function": self.get_user_monitoring,
            "parameter_descriptions": {
                "user_id": "User ID",
                "page": "Page number (default: 1)",
                "limit": "Number of items per page (default: 10)"
            }
        }
        
        # Define get_detailed_report tool
        self._tool_definitions["get_detailed_report"] = {
            "description": "Get a detailed report from a DetailedReportLink URL",
            "function": self.get_detailed_report,
            "parameter_descriptions": {
                "report_url": "The DetailedReportLink URL"
            }
        }
            
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all backup tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_monitoring_data(self, params: str) -> Dict[str, Any]:
        """
        Get monitoring data for backup/restore plans with optional filtering.
        
        Args:
            params: Filter parameters as a JSON string
            
        Returns:
            Dictionary with monitoring data
        """
        logger.info(f"Getting monitoring data with params: {params}")
        return await get_monitoring_data_list(self.client, params)
    
    async def get_monitoring_item(self, item_id: str) -> Dict[str, Any]:
        """
        Get a specific monitoring item by ID.
        
        Args:
            item_id: Monitoring item ID
            
        Returns:
            Dictionary with monitoring item data
        """
        logger.info(f"Getting monitoring item with ID: {item_id}")
        return await get_monitoring_item_detail(self.client, item_id)
    
    async def get_user_monitoring(self, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """
        Get monitoring data for a specific user.
        
        Args:
            user_id: User ID
            page: Page number (default: 1)
            limit: Number of items per page (default: 10)
            
        Returns:
            Dictionary with monitoring data
        """
        logger.info(f"Getting monitoring data for user: {user_id}, page: {page}, limit: {limit}")
        return await get_user_monitoring_data(self.client, user_id, page, limit)
    
    async def get_backup_plans(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get backup plans (redirects to monitoring API).
        
        Args:
            params: Filter parameters as a dictionary
            
        Returns:
            Dictionary with backup plans data
        """
        logger.warning("get_backup_plans is deprecated, use get_monitoring_data instead")
        return await self.get_monitoring_data(params=params)
    
    async def get_backup_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Get a specific backup plan by ID (redirects to monitoring API).
        
        Args:
            plan_id: The ID of the backup plan to retrieve
            
        Returns:
            Dictionary with backup plan data
        """
        logger.warning("get_backup_plan is deprecated, use get_monitoring_item instead")
        return await self.get_monitoring_item(item_id=plan_id)
    
    async def get_backup_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get backup history (redirects to monitoring API).
        
        Args:
            params: Filter parameters as a dictionary
            
        Returns:
            Dictionary with backup history data
        """
        logger.warning("get_backup_history is deprecated, use get_monitoring_data instead")
        return await self.get_monitoring_data(params=params)
    
    async def get_backup_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get a specific backup session by ID (redirects to monitoring API).
        
        Args:
            session_id: The ID of the backup session to retrieve
            
        Returns:
            Dictionary with backup session data
        """
        logger.warning("get_backup_session is deprecated, use get_monitoring_item instead")
        return await self.get_monitoring_item(item_id=session_id)
    
    async def get_detailed_report(self, report_url: str) -> Dict[str, Any]:
        """
        Get a detailed report from a URL.
        
        Args:
            report_url: URL for the detailed report
            
        Returns:
            Dictionary with report data
        """
        logger.info(f"Getting detailed report from URL: {report_url}")
        return await get_detailed_report_data(self.client, report_url)
    
    def close(self) -> None:
        """Close any resources."""
        logger.info("Closing backup tools resources")

# Create instance for dependency injection
backup_tools = BackupTools() 