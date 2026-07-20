"""Packages client module for MSP360 API."""
import logging
from typing import Dict, Any, Optional

from .client_base import MSP360ClientBase

logger = logging.getLogger("msp360_mcp.packages")

class PackagesClient(MSP360ClientBase):
    """Client for software package-related MSP360 API endpoints."""
    
    async def get_packages(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a list of available software packages with proper pagination.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with package data
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
            if 'search' in params:
                query_params['search'] = params['search']
                
            if 'type' in params:
                query_params['type'] = params['type']
                
            if 'edition' in params:
                query_params['edition'] = params['edition']
                
            if 'version' in params:
                query_params['version'] = params['version']
        
        return await self._make_request(method="GET", endpoint="/api/Packages", params=query_params)
    
    async def get_package(self, package_id: str) -> Dict[str, Any]:
        """Get a specific package by ID.
        
        Args:
            package_id: The ID of the package to retrieve
            
        Returns:
            API response with package data
        """
        return await self._make_request(method="GET", endpoint=f"/api/Packages/{package_id}")

    async def create_package(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a storage limit package."""
        return await self._make_request(
            method="POST", endpoint="/api/Packages", json_data=package_data
        )

    async def update_package(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a storage limit package."""
        return await self._make_request(
            method="PUT", endpoint="/api/Packages", json_data=package_data
        )

    async def delete_package(self, package_id: str) -> Dict[str, Any]:
        """Delete a storage limit package by ID."""
        return await self._make_request(
            method="DELETE", endpoint=f"/api/Packages/{package_id}"
        )
    
    async def get_builds(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a list of available builds.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with build data
        """
        # Transform query parameters
        query_params = {}
        
        if params:
            # Handle pagination
            if 'page' in params and 'limit' in params:
                page = int(params['page'])
                limit = int(params['limit'])
                # MSP360 API uses skip/take for pagination
                skip = (page - 1) * limit
                query_params['take'] = limit
                query_params['skip'] = skip
                
            if 'edition' in params:
                query_params['edition'] = params['edition']
            if 'build_type' in params:
                query_params['type'] = params['build_type']
            elif 'type' in params:
                query_params['type'] = params['type']
        
        return await self._make_request(method="GET", endpoint="/api/Builds", params=query_params)
    
    async def request_custom_builds(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """Request custom builds with specified editions.
        
        Args:
            build_data: Build request data
            
        Returns:
            API response with build request status
        """
        return await self._make_request(
            method="POST",
            endpoint="/api/Builds/RequestCustomBuilds",
            json_data=build_data,
        )
    
    async def get_available_versions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get the latest available versions of builds.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            API response with version data
        """
        # Transform query parameters if needed
        query_params = {}
        
        if params:
            # Add any filter parameters
            if 'editions' in params:
                query_params['editions'] = params['editions']
                
            if 'types' in params:
                query_params['types'] = params['types']
                
            if 'version' in params:
                query_params['version'] = params['version']
        
        response_data = await self._make_request(method="GET", endpoint="/api/Builds/AvailableVersions", params=query_params)
        
        # If the response is a list, format it with descriptive type names
        if isinstance(response_data, list):
            # Define a mapping of numeric types to descriptive names
            type_mapping = {
                0: "Windows",
                1: "Virtual Machine Edition",
                2: "Linux (rpm)",
                3: "Linux (deb)",
                4: "macOS",
                5: "CloudFTP",
                6: "RMM Agent for Windows",
                7: "RMM Agent for Linux (rpm)",
                8: "RMM Agent for Linux (deb)",
                9: "RMM Agent for macOS",
                10: "Connect",
                11: "Quick Restore",
                12: "Network Discovery"
            }
            
            # Create a new list with augmented items that include human-readable types
            formatted_data = []
            for item in response_data:
                type_value = item.get('Type')
                if type_value is not None:
                    # Add a new field with the human-readable type description
                    new_item = dict(item)
                    new_item['TypeName'] = type_mapping.get(type_value, f"Unknown Type ({type_value})")
                    formatted_data.append(new_item)
                else:
                    formatted_data.append(item)
            
            return formatted_data
        
        return response_data 