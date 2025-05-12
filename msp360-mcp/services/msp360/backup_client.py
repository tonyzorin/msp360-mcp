"""Backup client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.backup")

class BackupClient(MSP360ClientBase):
    """Client for backup-related MSP360 API endpoints."""
    
    async def get_backup_plans(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of backup plans.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with backup plan data
        """
        # This may redirect to monitoring endpoint in some API versions
        logger.warning("get_backup_plans may be deprecated, consider using get_monitoring instead")
        return await self.get_monitoring(params)
    
    async def get_backup_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get a specific backup plan by ID.
        
        Args:
            plan_id: The ID of the backup plan to retrieve
            
        Returns:
            API response with backup plan data
        """
        # This may redirect to monitoring endpoint in some API versions
        logger.warning("get_backup_plan may be deprecated, consider using get_monitoring_item instead")
        return await self.get_monitoring_item(plan_id)
    
    async def get_backup_history(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get backup history.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with backup history data
        """
        # This may redirect to monitoring endpoint in some API versions
        logger.warning("get_backup_history may be deprecated, consider using get_monitoring instead")
        return await self.get_monitoring(params)
    
    async def get_backup_session(self, session_id: str) -> Dict[str, Any]:
        """Get a specific backup session by ID.
        
        Args:
            session_id: The ID of the backup session to retrieve
            
        Returns:
            API response with backup session data
        """
        # This may redirect to monitoring endpoint in some API versions
        logger.warning("get_backup_session may be deprecated, consider using get_monitoring_item instead")
        return await self.get_monitoring_item(session_id)
    
    async def get_monitoring(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get backup monitoring data with filtering options.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with monitoring data
        """
        # Transform pagination parameters from page/limit to skip/take
        query_params = {}
        
        if params:
            # Handle pagination parameters
            if 'page' in params and 'limit' in params:
                page = int(params['page'])
                limit = int(params['limit'])
                # MSP360 API uses skip/take for pagination
                skip = (page - 1) * limit
                query_params['take'] = limit
                query_params['skip'] = skip
            elif 'skip' in params and 'take' in params:
                # Pass through if already in correct format
                query_params['skip'] = params['skip']
                query_params['take'] = params['take']
                
            # Add other filter parameters
            if 'userId' in params:
                query_params['userId'] = params['userId']
            elif 'user_id' in params:
                query_params['userId'] = params['user_id']
                
            if 'companyId' in params:
                query_params['companyId'] = params['companyId']
            elif 'company_id' in params:
                query_params['companyId'] = params['company_id']
                
            if 'fromDate' in params:
                query_params['fromDate'] = params['fromDate']
            elif 'from_date' in params:
                query_params['fromDate'] = params['from_date']
                
            if 'toDate' in params:
                query_params['toDate'] = params['toDate']
            elif 'to_date' in params:
                query_params['toDate'] = params['to_date']
                
            if 'status' in params:
                query_params['status'] = params['status']
        
        return await self._make_request(method="GET", endpoint="/api/Monitoring", params=query_params)
    
    async def get_monitoring_item(self, item_id: str) -> Dict[str, Any]:
        """Get a specific monitoring item by ID.
        
        Args:
            item_id: The ID of the monitoring item to retrieve
            
        Returns:
            API response with monitoring item data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Monitoring/{item_id}")
    
    async def get_monitoring_for_user(self, user_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get monitoring data for a specific user.
        
        Args:
            user_id: The ID of the user
            params: Additional query parameters
            
        Returns:
            API response with monitoring data
        """
        # Create a new params dict if none provided
        if params is None:
            params = {}
            
        # Add user_id to params
        params['user_id'] = user_id
        
        # Use the standard get_monitoring method
        return await self.get_monitoring(params)
        
    async def create_backup_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new backup plan.
        
        Args:
            plan_data: Backup plan data
            
        Returns:
            API response with created plan data
        """
        return await self._make_request(method="POST", endpoint="/api/BackupPlans", json_data=plan_data)
    
    async def update_backup_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing backup plan.
        
        Args:
            plan_data: Backup plan data with ID
            
        Returns:
            API response with updated plan data
        """
        return await self._make_request(method="PUT", endpoint="/api/BackupPlans", json_data=plan_data)
    
    async def delete_backup_plan(self, plan_id: str) -> Dict[str, Any]:
        """Delete a backup plan.
        
        Args:
            plan_id: ID of the backup plan to delete
            
        Returns:
            API response confirming deletion
        """
        return await self._make_request(method="DELETE", endpoint=f"/api/BackupPlans/{plan_id}") 