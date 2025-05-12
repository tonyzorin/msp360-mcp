"""Companies tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool

logger = logging.getLogger("msp360_mcp.tools")

class CompanyTools:
    """Tools for interacting with MSP360/CloudBerry companies."""
    
    class CompanyParams(BaseModel):
        """Parameters model for filtering companies."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        name: Optional[str] = Field(None, description="Filter by company name")
    
    def __init__(self):
        """Initialize the company tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Register all company tools with the tool registry."""
        self._tool_definitions["get_companies"] = {
            "description": "Get a list of MSP360 companies with optional filtering",
            "function": self.get_companies,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters (page, limit, name)"
            }
        }
        
        self._tool_definitions["get_company"] = {
            "description": "Get a specific MSP360 company by ID",
            "function": self.get_company,
            "parameter_descriptions": {
                "company_id": "Company ID"
            }
        }
        
        # Don't register tools globally here - let MCPServer handle that
            
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all company tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_companies(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of companies with optional filtering.
        
        Args:
            params: JSON string with filter parameters
            
        Returns:
            Dictionary with companies data
        """
        logger.info(f"Getting companies with params: {params}")
        
        # Parse the JSON string to get parameters
        try:
            if params and params.strip():
                param_dict = json.loads(params)
            else:
                param_dict = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            return {"content": [], "error": f"Invalid JSON parameters: {str(e)}"}
        
        query_params = {}
        
        # Extract pagination parameters
        if 'page' in param_dict:
            query_params['page'] = param_dict['page']
        if 'limit' in param_dict:
            query_params['limit'] = param_dict['limit']
        
        # Extract filter parameters
        if 'name' in param_dict and param_dict['name']:
            query_params['name'] = param_dict['name']
        
        try:
            # Call the MSP360 API to get companies
            response = await self.client.get_companies(params=query_params)
            
            # Process companies into a content array format for MCP
            result_content = []
            
            # Extract the companies data
            if isinstance(response, list):
                companies_data = response
            elif isinstance(response, dict):
                if 'items' in response and isinstance(response['items'], list):
                    companies_data = response['items']
                elif 'content' in response and isinstance(response['content'], list):
                    companies_data = response['content']
                else:
                    companies_data = []
            else:
                companies_data = []
            
            logger.info(f"Retrieved {len(companies_data)} companies")
            
            # Apply limit directly in case the API didn't respect it
            limit = param_dict.get('limit')
            if limit and isinstance(limit, int) and limit > 0 and len(companies_data) > limit:
                companies_data = companies_data[:limit]
                logger.info(f"Applied limit {limit}, reduced to {len(companies_data)} companies")
            
            # Format each company as a text item
            for company in companies_data:
                company_info = []
                
                # Get standard fields
                company_id = company.get('Id', 'N/A')
                company_name = company.get('Name', 'N/A')
                company_description = company.get('Description', 'N/A')
                
                company_info.append(f"ID: {company_id}")
                company_info.append(f"Name: {company_name}")
                company_info.append(f"Description: {company_description}")
                
                # Get storage limit if available
                if 'StorageLimit' in company:
                    limit_value = company.get('StorageLimit')
                    if limit_value == -1:
                        company_info.append(f"Storage Limit: Unlimited")
                    else:
                        try:
                            limit_bytes = int(limit_value)
                            limit_readable = self._format_storage_size(limit_bytes)
                            company_info.append(f"Storage Limit: {limit_readable}")
                        except (ValueError, TypeError):
                            company_info.append(f"Storage Limit: {limit_value}")
                
                # Add parent company if available
                if 'ParentCompany' in company and company['ParentCompany']:
                    company_info.append(f"Parent Company: {company.get('ParentCompany')}")
                
                result_content.append({
                    "type": "text",
                    "text": "\n".join(company_info)
                })
            
            # If no companies were found, add a message
            if not result_content:
                result_content.append({
                    "type": "text",
                    "text": "No companies found matching the criteria."
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving companies: {str(e)}")
            return {"content": [], "error": str(e)}
            
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get a detailed company report including users and destinations.
        
        Args:
            company_id: The ID of the company to retrieve
            
        Returns:
            Dictionary with company data including related information
        """
        logger.info(f"Getting company with ID: {company_id}")
        
        try:
            # Request the company data from the API
            company = await self.client.get_company(company_id=company_id)
            
            # Log the response for debugging
            logger.debug(f"API response type: {type(company)}")
            logger.debug(f"API response data: {company}")
            
            # Check for null or empty response
            if company is None:
                logger.warning(f"Received null response from API for company ID: {company_id}")
                return {"content": [{
                    "type": "text",
                    "text": f"Error: Company with ID {company_id} not found in the MSP360 system."
                }], "error": f"Company not found: {company_id}"}
            
            # Check if the response is empty dict or other non-useful response
            if isinstance(company, dict) and not company:
                logger.warning(f"Received empty dict response from API for company ID: {company_id}")
                return {"content": [{
                    "type": "text",
                    "text": f"Error: Company with ID {company_id} exists but returned empty data."
                }], "error": f"Company returned empty data: {company_id}"}
                
            # Check for error responses
            if isinstance(company, dict) and ('error' in company or 'ErrorMessage' in company):
                error_msg = company.get('error') or company.get('ErrorMessage') or 'Unknown error'
                logger.warning(f"Received error response from API: {error_msg}")
                return {"content": [{
                    "type": "text",
                    "text": f"Error from MSP360 API: {error_msg}"
                }], "error": error_msg}
            
            # Format company details
            if isinstance(company, dict):
                formatted_lines = []
                
                # Add company header
                formatted_lines.append(f"COMPANY DETAILS: {company.get('Name', 'Unknown')}")
                formatted_lines.append("=" * 50)
                
                # Order important fields first
                formatted_lines.append("BASIC INFORMATION")
                formatted_lines.append("-" * 20)
                for key in ['Id', 'Name', 'Description', 'ParentCompany']:
                    if key in company:
                        formatted_lines.append(f"{key}: {company.get(key)}")
                
                # Handle PackageId specially
                if 'PackageId' in company:
                    package_id = company.get('PackageId')
                    if package_id == -2:
                        formatted_lines.append("Package ID: -2 (Default package - unlimited)")
                    else:
                        formatted_lines.append(f"Package ID: {package_id}")
                
                # Add explanations for specific fields
                if 'StorageLimit' in company:
                    formatted_lines.append("\nSTORAGE INFORMATION")
                    formatted_lines.append("-" * 20)
                    
                    storage_limit = company.get('StorageLimit')
                    if storage_limit == -1:
                        formatted_lines.append(f"StorageLimit: {storage_limit} (Not Set)")
                    else:
                        # Convert to human readable size if possible
                        try:
                            size_bytes = int(storage_limit)
                            if size_bytes > 0:
                                formatted_size = self._format_storage_size(size_bytes)
                                formatted_lines.append(f"StorageLimit: {formatted_size}")
                            else:
                                formatted_lines.append(f"StorageLimit: {storage_limit} (Not Set)")
                        except (ValueError, TypeError):
                            formatted_lines.append(f"StorageLimit: {storage_limit}")
                
                if 'LicenseSettings' in company:
                    formatted_lines.append("\nLICENSE INFORMATION")
                    formatted_lines.append("-" * 20)
                    
                    license_settings = company.get('LicenseSettings')
                    license_explanation = ""
                    if license_settings == 0:
                        license_explanation = " (Inherit from Parent Company)"
                    elif license_settings == 1:
                        license_explanation = " (Define license types for this company)"
                    elif license_settings == 2:
                        license_explanation = " (Inherit from parent and define own license types)"
                    formatted_lines.append(f"LicenseSettings: {license_settings}{license_explanation}")
                
                # Get company name for user lookup
                company_name = company.get('Name')
                
                # Get users in this company first
                company_users = []
                try:
                    users_response = await self.client.get_users(params={"take": 50})
                    
                    if isinstance(users_response, list):
                        for user in users_response:
                            if user.get('Company') == company_name:
                                company_users.append(user)
                    elif isinstance(users_response, dict) and 'items' in users_response:
                        for user in users_response.get('items', []):
                            if user.get('Company') == company_name:
                                company_users.append(user)
                    
                    if company_users:
                        # Add user information
                        formatted_lines.append("\nUSER INFORMATION")
                        formatted_lines.append("-" * 20)
                        formatted_lines.append(f"Total Users: {len(company_users)}")
                        user_emails = [user.get('Email', 'N/A') for user in company_users]
                        formatted_lines.append(f"Users: {', '.join(user_emails)}")
                        
                        # Now get all destinations for each user and include them regardless of ID matching
                        all_destinations = []
                        
                        for user in company_users:
                            if 'Email' in user:
                                user_email = user['Email']
                                try:
                                    user_destinations = await self.client.get_user_destinations(user_email=user_email)
                                    
                                    if isinstance(user_destinations, list) and user_destinations:
                                        for dest in user_destinations:
                                            all_destinations.append({
                                                'user_email': user_email,
                                                'details': dest
                                            })
                                    elif isinstance(user_destinations, dict) and 'items' in user_destinations and user_destinations['items']:
                                        for dest in user_destinations.get('items', []):
                                            all_destinations.append({
                                                'user_email': user_email,
                                                'details': dest
                                            })
                                except Exception as e:
                                    logger.warning(f"Error retrieving destinations for user {user_email}: {str(e)}")
                        
                        # Now display all destinations found
                        if all_destinations:
                            formatted_lines.append("\nSTORAGE DESTINATIONS")
                            formatted_lines.append("-" * 20)
                            formatted_lines.append(f"Total Storage Destinations: {len(all_destinations)}")
                            
                            for idx, dest_data in enumerate(all_destinations, 1):
                                dest = dest_data['details']
                                user_email = dest_data['user_email']
                                
                                formatted_lines.append(f"\nDestination #{idx}")
                                formatted_lines.append("-" * 15)
                                
                                # Display user that owns this destination
                                formatted_lines.append(f"Associated User: {user_email}")
                                
                                # Display key destination properties
                                # Get ID from multiple possible fields
                                dest_id = dest.get('Id', dest.get('ID', 'N/A'))
                                formatted_lines.append(f"ID: {dest_id}")
                                
                                if 'AccountDisplayName' in dest:
                                    formatted_lines.append(f"Account: {dest.get('AccountDisplayName')}")
                                if 'DestinationDisplayName' in dest:
                                    formatted_lines.append(f"Display Name: {dest.get('DestinationDisplayName')}")
                                if 'Type' in dest:
                                    formatted_lines.append(f"Type: {dest.get('Type')}")
                                if 'Destination' in dest:
                                    formatted_lines.append(f"Path: {dest.get('Destination')}")
                                
                                # Format size information
                                if 'CurrentVolume' in dest:
                                    size_bytes = dest['CurrentVolume']
                                    if isinstance(size_bytes, int):
                                        if size_bytes == 0:
                                            formatted_lines.append(f"Storage Used: 0 B (Empty)")
                                        else:
                                            formatted_size = self._format_storage_size(size_bytes)
                                            formatted_lines.append(f"Storage Used: {formatted_size}")
                                    else:
                                        formatted_lines.append(f"Storage Used: {size_bytes}")
                                
                                # Add PackageID information and retrieve package details if available
                                if 'PackageID' in dest:
                                    package_id = dest.get('PackageID')
                                    package_explanation = ""
                                    
                                    if package_id == -2:
                                        package_explanation = " (Default package - unlimited)"
                                    elif package_id == -1:
                                        package_explanation = " (None)"
                                    
                                    formatted_lines.append(f"Package ID: {package_id}{package_explanation}")
                                    
                                    # Try to get package information if it's a custom package
                                    if package_id not in [-1, -2] and package_id is not None:
                                        try:
                                            package_info = await self.client.get_package(package_id=str(package_id))
                                            if package_info:
                                                if 'Name' in package_info:
                                                    formatted_lines.append(f"Package Name: {package_info.get('Name')}")
                                                if 'Description' in package_info:
                                                    formatted_lines.append(f"Package Description: {package_info.get('Description')}")
                                        except Exception as e:
                                            logger.warning(f"Could not get package details for ID {package_id}: {str(e)}")
                        else:
                            formatted_lines.append("\nNo storage destinations found for any users in this company.")
                    
                    # Special handling for Destinations field from the company object
                    if 'Destinations' in company and not all_destinations:
                        destinations = company.get('Destinations')
                        
                        # Handle case where Destinations is a list
                        if isinstance(destinations, list):
                            if destinations:
                                formatted_lines.append("\nCOMPANY DESTINATIONS")
                                formatted_lines.append("-" * 20)
                                formatted_lines.append(f"Total Destinations: {len(destinations)}")
                                
                                for idx, dest in enumerate(destinations, 1):
                                    formatted_lines.append(f"\nDestination #{idx}")
                                    formatted_lines.append("-" * 15)
                                    
                                    if isinstance(dest, dict):
                                        for k, v in dest.items():
                                            formatted_lines.append(f"{k}: {v}")
                                    else:
                                        formatted_lines.append(f"ID: {dest}")
                                        formatted_lines.append(f"(No detailed information available - try using get_user_destinations with a specific user email)")
                            else:
                                formatted_lines.append("\nDestinations: []")
                        
                        # Handle case where Destinations is a string that looks like JSON
                        elif isinstance(destinations, str) and destinations.strip().startswith('['):
                            try:
                                # Try to parse JSON string
                                destinations_list = json.loads(destinations)
                                if destinations_list:
                                    formatted_lines.append("\nCOMPANY DESTINATIONS")
                                    formatted_lines.append("-" * 20)
                                    formatted_lines.append(f"Total Destinations: {len(destinations_list)}")
                                    
                                    for idx, dest in enumerate(destinations_list, 1):
                                        formatted_lines.append(f"\nDestination #{idx}")
                                        formatted_lines.append("-" * 15)
                                        
                                        if isinstance(dest, dict):
                                            for k, v in dest.items():
                                                formatted_lines.append(f"{k}: {v}")
                                        else:
                                            formatted_lines.append(f"ID: {dest}")
                                            formatted_lines.append(f"(No detailed information available - try using get_user_destinations with a specific user email)")
                                else:
                                    formatted_lines.append("\nDestinations: []")
                            except json.JSONDecodeError:
                                # If parsing fails, output as is
                                formatted_lines.append(f"\nDestinations (raw): {destinations}")
                        else:
                            # Not a JSON string or list, output as is
                            formatted_lines.append(f"\nDestinations (raw): {destinations}")
                
                except Exception as e:
                    logger.error(f"Error fetching user information: {str(e)}")
                    formatted_lines.append(f"\nError fetching additional information: {str(e)}")
                
                # Add other fields
                other_fields = []
                for key, value in company.items():
                    if key not in ['Id', 'Name', 'Description', 'ParentCompany', 'Destinations', 'StorageLimit', 'LicenseSettings']:
                        other_fields.append(f"{key}: {value}")
                
                if other_fields:
                    formatted_lines.append("\nADDITIONAL INFORMATION")
                    formatted_lines.append("-" * 20)
                    formatted_lines.extend(other_fields)
                
                formatted_text = "\n".join(formatted_lines)
                return {"content": [{"type": "text", "text": formatted_text}]}
            elif isinstance(company, str):
                # Handle string response
                logger.warning(f"Unexpected string response for company {company_id}: {company}")
                return {"content": [{"type": "text", "text": company}]}
            else:
                # Handle unexpected response type
                logger.warning(f"Unexpected response type: {type(company)}")
                return {"content": [], "error": f"Unexpected response format for company {company_id}"}
        except Exception as e:
            logger.error(f"Error retrieving company {company_id}: {str(e)}", exc_info=True)
            return {"content": [], "error": f"Error retrieving company {company_id}: {str(e)}"}

    def _format_storage_size(self, size_bytes: int) -> str:
        """Format bytes into a human-readable string with appropriate unit.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string with appropriate unit (B, KB, MB, GB, TB)
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        
        return f"{size:.2f} {units[i]}"
            
    def close(self) -> None:
        """Close any resources."""
        pass

# No singleton instance here - let MCPServer create it 