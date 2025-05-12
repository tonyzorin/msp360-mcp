"""Destinations client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional, List, Union

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.destinations")

class DestinationsClient(MSP360ClientBase):
    """Client for destination-related MSP360 API endpoints."""
    
    async def get_user_destinations(self, user_email: str) -> List[Dict[str, Any]]:
        """Get destinations for a specific user by email.
        
        Args:
            user_email: The email of the user
            
        Returns:
            API response with destination data as a list
        """
        result = await self._make_request(method="GET", endpoint=f"/api/Destinations/{user_email}")
        
        # The API returns either a list of destinations or an object with a Destinations field
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'Destinations' in result:
            return result['Destinations']
        elif isinstance(result, dict):
            # If no specific destinations field, return the entire object
            return [result]
        else:
            return []
            
    async def add_destination(self, destination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a destination.
        
        Args:
            destination_data: Destination data dictionary
            
        Returns:
            API response with created destination data
        """
        return await self._make_request(method="POST", endpoint="/api/Destinations", json_data=destination_data)
    
    async def update_destination(self, destination_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing destination.
        
        Args:
            destination_data: Destination data dictionary
            
        Returns:
            API response with updated destination data
        """
        return await self._make_request(method="PUT", endpoint="/api/Destinations", json_data=destination_data)
    
    async def delete_destination(self, destination_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a destination.
        
        Args:
            destination_id: ID of the destination to delete
            user_id: Optional user ID required by the API
            
        Returns:
            API response confirming deletion
        """
        query_params = {}
        if user_id:
            query_params['UserID'] = user_id
            
        return await self._make_request(
            method="DELETE", 
            endpoint=f"/api/Destinations/{destination_id}", 
            params=query_params
        ) 