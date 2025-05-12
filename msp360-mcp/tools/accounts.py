"""Account management tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool
from tools.utils import format_size
from core.config import settings

logger = logging.getLogger("msp360_mcp.tools")

def get_curl_example(endpoint: str, method: str = "GET", data: str = None) -> str:
    """Generate a curl example for API testing.
    
    Args:
        endpoint: API endpoint to call
        method: HTTP method (GET, POST, PUT)
        data: JSON data payload for POST/PUT requests
        
    Returns:
        Formatted curl command example
    """
    base_cmd = f"""
curl -X {method} https://api.mspbackups.com{endpoint} \\
  -H "Authorization: Bearer $(curl -s -X POST https://api.mspbackups.com/api/Provider/Login \\
    -H 'Content-Type: application/json' \\
    -d '{{\\\"UserName\\\":\\\"{settings.MSP360_API_LOGIN}\\\",\\\"Password\\\":\\\"{settings.MSP360_API_PASSWORD}\\\"}}' | \\
    grep -o '\\\"access_token\\\":\\\"[^\\\"]*' | cut -d'\\\"' -f4)" \\
  -H 'Content-Type: application/json'"""
    
    # Add data payload for POST/PUT requests
    if data and method in ["POST", "PUT"]:
        base_cmd += f" \\\n  -d '{data}'"
    
    base_cmd += """

# Note: This API may return a 403 Forbidden error if the credentials are invalid or have insufficient permissions.
# You may need to check your MSP360/CloudBerry API credentials or contact their support for assistance.
"""
    return base_cmd

class AccountTools:
    """Tools for interacting with MSP360/CloudBerry accounts."""
    
    class AccountParams(BaseModel):
        """Parameters model for filtering accounts."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        name: Optional[str] = Field(None, description="Filter by account name")
        
    def __init__(self):
        """Initialize the account tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        logger.info("AccountTools initialized")
        
    def _register_tools(self):
        """Define all account tools but don't register them globally."""
        self._tool_definitions["get_accounts"] = {
            "description": "Get a list of MSP360 accounts with optional filtering",
            "function": self.get_accounts,
            "parameter_descriptions": {
                "params": "params parameter"
            }
        }
        
        self._tool_definitions["get_account"] = {
            "description": "Get a specific MSP360 account by ID",
            "function": self.get_account,
            "parameter_descriptions": {
                "account_id": "Account ID"
            }
        }
        
        self._tool_definitions["create_account"] = {
            "description": "Create a new MSP360 account",
            "function": self.create_account,
            "parameter_descriptions": {
                "account_data": "Account data in JSON format"
            }
        }
        
        self._tool_definitions["update_account"] = {
            "description": "Update an existing MSP360 account",
            "function": self.update_account,
            "parameter_descriptions": {
                "account_data": "Account data in JSON format"
            }
        }
        
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all account tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_accounts(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of accounts with optional filtering.
        
        Args:
            params: JSON string with filter parameters
            
        Returns:
            Dictionary with accounts data
        """
        logger.info(f"Getting accounts with params: {params}")
        
        # Parse the JSON string to get parameters
        query_params = {}
        try:
            if params and params.strip():
                query_params = json.loads(params)
            else:
                # Default to empty dict if no params provided
                query_params = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            example_params = """
{
  "page": 1,
  "limit": 10,
  "name": "Example Account"
}"""
            curl_example = get_curl_example("/api/Accounts", "GET")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error parsing parameters: {str(e)}\n\nExample valid parameters JSON:\n```json\n{example_params}\n```\n\nExample curl command to get accounts:\n```bash\n{curl_example}\n```"
                }],
                "error": f"Invalid JSON parameters: {str(e)}"
            }
        
        # Make a copy of the original parameters for logging
        original_params = query_params.copy()
        api_params = {}
        
        # Keep track of client-side filtering needed
        client_filters = {}
        
        # Convert pagination parameters
        if 'page' in query_params:
            page = int(query_params.pop('page'))
            api_params['skip'] = (page - 1) * int(query_params.get('limit', 10))
        
        if 'limit' in query_params:
            api_params['take'] = int(query_params.pop('limit'))
            # Store limit for client-side limit if API doesn't respect it
            client_filters['limit'] = int(original_params.get('limit', 10))
        
        # Map filter parameters to API expected names
        if 'name' in query_params:
            # Try both name and displayName since documentation isn't clear
            api_params['name'] = query_params.pop('name')
            # Store name filter for client-side filtering if API doesn't handle it
            client_filters['name'] = original_params.get('name', '').lower()
        
        if 'company_id' in query_params:
            api_params['companyId'] = query_params.pop('company_id')
        
        if 'product_id' in query_params:
            api_params['productId'] = query_params.pop('product_id')
        
        # Add any remaining parameters
        for key, value in query_params.items():
            api_params[key] = value
        
        logger.info(f"Transformed params: {original_params} -> {api_params}, client filters: {client_filters}")
        
        try:
            # Call the API with the transformed parameters
            logger.info(f"Calling MSP360 API with parameters: {api_params}")
            accounts = await self.client.get_accounts(params=api_params)
            logger.info(f"API response received, type: {type(accounts).__name__}")
            logger.debug(f"Retrieved accounts response: {json.dumps(accounts)[:500] if accounts else 'None'}")
            
            # If we received items and pagination parameters were used, log that information
            if isinstance(accounts, dict) and ('limit' in original_params or 'page' in original_params):
                total_count = accounts.get('TotalCount', accounts.get('totalCount', None))
                if total_count is not None:
                    logger.info(f"Total accounts available: {total_count}, requested page: {original_params.get('page', 1)}, limit: {original_params.get('limit', 'default')}")
            
            # Process the response for MCP
            result_content = []
            
            # If we received an array directly, use it as is
            if isinstance(accounts, list):
                account_list = accounts
                logger.info(f"Received direct list of {len(account_list)} accounts")
            elif isinstance(accounts, dict) and 'Accounts' in accounts:
                # Extract accounts from the 'Accounts' key if it exists
                account_list = accounts.get('Accounts', [])
                logger.info(f"Extracted list of {len(account_list)} accounts from 'Accounts' key")
            elif isinstance(accounts, dict) and 'Items' in accounts:
                # Extract accounts from the 'Items' key if it exists (alternative API format)
                account_list = accounts.get('Items', [])
                logger.info(f"Extracted list of {len(account_list)} accounts from 'Items' key")
            elif isinstance(accounts, dict) and 'AccountList' in accounts:
                # Extract accounts from the 'AccountList' key if it exists (alternative API format)
                account_list = accounts.get('AccountList', [])
                logger.info(f"Extracted list of {len(account_list)} accounts from 'AccountList' key")
            else:
                # If it's a single account (dict) or other non-list type, wrap it in a list
                logger.warning(f"Received non-list response: {type(accounts)}")
                
                # Try to convert to list if it's something else
                if isinstance(accounts, dict) and len(accounts) > 0:
                    # It might be a single account
                    account_list = [accounts]
                    logger.info("Treating response as a single account")
                else:
                    account_list = []
                    logger.warning("Couldn't extract accounts from the response")
            
            # Apply client-side filtering if needed
            if client_filters and account_list:
                # Filter by name if specified
                if 'name' in client_filters and client_filters['name']:
                    name_filter = client_filters['name'].lower()
                    logger.info(f"Applying client-side name filter: '{name_filter}'")
                    
                    # Create a new filtered list
                    filtered_list = []
                    for account in account_list:
                        account_name = account.get('DisplayName', 
                                     account.get('Name', 
                                     account.get('name', ''))).lower()
                        
                        if name_filter in account_name:
                            filtered_list.append(account)
                    
                    logger.info(f"Name filter reduced accounts from {len(account_list)} to {len(filtered_list)}")
                    account_list = filtered_list
                
                # Apply limit if specified
                if 'limit' in client_filters and isinstance(client_filters['limit'], int):
                    limit = client_filters['limit']
                    logger.info(f"Applying client-side limit: {limit}")
                    account_list = account_list[:limit]
            
            # Format and return the accounts we found
            if not account_list:
                example_params_str = json.dumps(original_params, indent=2) if original_params else "{}"
                curl_example = get_curl_example("/api/Accounts", "GET")
                result_content.append({
                    "type": "text",
                    "text": f"No accounts found. Please check that your MSP360 account has accounts configured or try different search parameters.\n\nParameters used:\n```json\n{example_params_str}\n```\n\nYou can test the API directly using:\n```bash\n{curl_example}\n```"
                })
            else:
                # Process each account
                for account in account_list:
                    # Extract the account fields based on the expected response format
                    account_id = account.get('AccountID', account.get('Id', account.get('ID', 'N/A')))
                    name = account.get('DisplayName', account.get('Name', 'N/A'))
                    storage_type = account.get('StorageType', 'N/A')
                    date_created = account.get('DateCreated', 'N/A')
                    
                    # Check if the account is valid and has useful data
                    has_minimal_data = (account_id == 'N/A' and name == 'N/A')
                    if has_minimal_data:
                        # Log available keys to help debug
                        available_keys = list(account.keys()) if isinstance(account, dict) else []
                        logger.warning(f"Account has minimal data. Available keys: {available_keys}")
                        
                        # If there are some keys available, try to extract whatever we can
                        if available_keys:
                            # Build a more informative account text showing all available fields
                            account_text = "Account with limited information:\n"
                            for key, value in account.items():
                                if isinstance(value, (str, int, float, bool)) or value is None:
                                    account_text += f"{key}: {value}\n"
                                else:
                                    # For complex objects (dicts, lists), just show the type
                                    account_text += f"{key}: [{type(value).__name__}]\n"
                        else:
                            account_text = "Account with no useful information available.\n"
                    else:
                        # Normal account with valid data
                        account_text = f"Account ID: {account_id}\nName: {name}\n"
                        
                        if storage_type != 'N/A':
                            account_text += f"Storage Type: {storage_type}\n"
                        
                        if date_created != 'N/A':
                            account_text += f"Created: {date_created}\n"
                    
                    # Add destinations if available
                    destinations = account.get('Destinations', [])
                    if destinations:
                        account_text += f"Destinations: {len(destinations)}\n"
                        for dest in destinations[:3]:  # Show only first 3 destinations to avoid clutter
                            dest_name = dest.get('DestinationDisplayName', dest.get('Destination', 'N/A'))
                            account_text += f"- {dest_name}\n"
                        if len(destinations) > 3:
                            account_text += f"...and {len(destinations) - 3} more\n"
                    
                    result_content.append({
                        "type": "text",
                        "text": account_text
                    })
                
                # Add summary
                result_content.append({
                    "type": "text",
                    "text": f"\nFound {len(account_list)} account(s)."
                })
                
                # Add a warning about accounts with minimal data if needed
                if any(account.get('AccountID', account.get('Id', account.get('ID', 'N/A'))) == 'N/A' 
                      for account in account_list):
                    result_content.append({
                        "type": "text",
                        "text": "\nWarning: Some accounts have minimal data. This might indicate a mismatch in expected API response format."
                    })
            
            return {"content": result_content}
        except HTTPException as api_error:
            logger.error(f"API error when retrieving accounts: {str(api_error)}")
            curl_example = get_curl_example("/api/Accounts", "GET")
            error_details = str(api_error)
            if hasattr(api_error, 'detail'):
                error_details = str(api_error.detail)
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"API Error: {error_details}\n\nThere was an error retrieving accounts.\n\nParameters used:\n```json\n{json.dumps(original_params, indent=2)}\n```\n\nTransformed to API parameters:\n```json\n{json.dumps(api_params, indent=2)}\n```\n\nYou can test the API directly using:\n```bash\n{curl_example}\n```"
                }],
                "error": f"API Error: {error_details}"
            }
        except Exception as e:
            logger.error(f"Error retrieving accounts: {str(e)}")
            curl_example = get_curl_example("/api/Accounts", "GET")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving accounts: {str(e)}.\n\nPlease verify your MSP360 API credentials and connection.\n\nParameters used:\n```json\n{json.dumps(original_params, indent=2)}\n```\n\nTransformed to API parameters:\n```json\n{json.dumps(api_params, indent=2)}\n```\n\nYou can test the API directly using:\n```bash\n{curl_example}\n```"
                }],
                "error": str(e)
            }
    
    def _format_account_data(self, account: Dict[str, Any]) -> str:
        """Format account data for display.
        
        Args:
            account: Account data dictionary
            
        Returns:
            Formatted account data string
        """
        # Log the raw account data to understand what's available
        logger.info(f"Raw account data: {json.dumps(account, indent=2)}")
        
        lines = []
        
        # Extract basic information with fallbacks
        account_id = account.get('ID', account.get('Id', account.get('id', 'N/A')))
        name = account.get('Name', account.get('name', 'N/A'))
        company = account.get('CompanyName', account.get('companyName', 'N/A'))
        
        lines.append(f"Account ID: {account_id}")
        lines.append(f"Name: {name}")
        if company != 'N/A':
            lines.append(f"Company: {company}")
        
        # Add other fields that may be present
        email = account.get('Email', account.get('email', None))
        if email:
            lines.append(f"Email: {email}")
        
        storage = account.get('StorageLimit', account.get('storageLimit', None))
        if storage:
            lines.append(f"Storage Limit: {format_size(storage)}")
        
        used_storage = account.get('UsedStorage', account.get('usedStorage', None))
        if used_storage:
            lines.append(f"Used Storage: {format_size(used_storage)}")
        
        # If we have an empty or minimal account, add a debug line with available keys
        if account_id == 'N/A' and name == 'N/A':
            if account:
                lines.append(f"Available fields: {', '.join(account.keys())}")
        
        return "\n".join(lines)
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get a specific account by ID.
        
        Args:
            account_id: Account ID
            
        Returns:
            Dictionary with account data
        """
        logger.info(f"Getting account with ID: {account_id}")
        
        # Check if account_id is empty or None
        if not account_id or not account_id.strip():
            example_data = {
                "AccountID": "your-account-id-here",
                "Name": "Example Account",
                "StorageType": "Amazon S3"
            }
            example_curl = get_curl_example("/api/Accounts/{account_id}", "GET")
            return {
                "content": [{
                    "type": "text",
                    "text": f"🤦‍♂️ No account ID provided. Please provide a valid account ID.\n\nExample account data structure:\n```json\n{json.dumps(example_data, indent=2)}\n```\n\nExample curl command to get an account (replace {account_id} with an actual ID):\n```bash\n{example_curl}\n```"
                }],
                "error": "Account ID is required"
            }
        
        try:
            account = await self.client.get_account(account_id=account_id)
            
            
            if not account:
                example_curl = get_curl_example(f"/api/Accounts/{account_id}", "GET")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"🤦‍♂️ No account found with ID: {account_id}\n\nYou can verify this by testing the API directly:\n```bash\n{example_curl}\n```"
                    }]
                }
            
            # Handle case where response might be a list
            if isinstance(account, list):
                if not account:
                    example_curl = get_curl_example(f"/api/Accounts/{account_id}", "GET")
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"No account found with ID: {account_id}\n\nYou can verify this by testing the API directly:\n```bash\n{example_curl}\n```"
                        }]
                    }
                # Use the first item if API returned a list
                account = account[0]
                
                # Additional check if the account item is valid
                if not isinstance(account, dict):
                    logger.warning(f"API returned an unexpected data type in the list: {type(account)}")
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"API returned unexpected data format for account ID {account_id}. Expected a dictionary but received a {type(account)} inside a list.\n\nRaw data: {str(account)[:1000]}"
                        }],
                        "error": "Unexpected API response format"
                    }
            
            # Verify that account is a dictionary
            if not isinstance(account, dict):
                logger.warning(f"API returned an unexpected data type: {type(account)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"API returned unexpected data format for account ID {account_id}. Expected a dictionary but received a {type(account)}.\n\nRaw data: {str(account)[:1000]}"
                    }],
                    "error": "Unexpected API response format"
                }
            
            # Extract the account fields based on the expected response format
            account_id = account.get('AccountID', account.get('Id', account.get('ID', 'N/A')))
            name = account.get('DisplayName', account.get('Name', 'N/A'))
            storage_type = account.get('StorageType', 'N/A')
            date_created = account.get('DateCreated', 'N/A')
            
            # Format the account for display
            account_text = f"Account ID: {account_id}\nName: {name}\n"
            
            if storage_type != 'N/A':
                account_text += f"Storage Type: {storage_type}\n"
            
            if date_created != 'N/A':
                account_text += f"Created: {date_created}\n"
            
            # Add destinations if available
            destinations = account.get('Destinations', [])
            if destinations:
                account_text += f"Destinations: {len(destinations)}\n"
                for dest in destinations:
                    dest_name = dest.get('DestinationDisplayName', dest.get('Destination', 'N/A'))
                    account_text += f"- {dest_name}\n"
            
            return {
                "content": [{
                    "type": "text",
                    "text": account_text
                }]
            }
        except HTTPException as api_error:
            logger.error(f"API error when retrieving account: {str(api_error)}")
            example_curl = get_curl_example(f"/api/Accounts/{account_id}", "GET")
            error_details = str(api_error)
            if hasattr(api_error, 'detail'):
                error_details = str(api_error.detail)
                
            return {
                "content": [{
                    "type": "text",
                    "text": f"API Error: {error_details}\n\nThere was an error retrieving the account with ID: {account_id}\n\nYou can try testing the API directly using this curl command:\n```bash\n{example_curl}\n```"
                }],
                "error": f"API Error: {error_details}"
            }
        except Exception as e:
            logger.error(f"Error retrieving account: {str(e)}")
            example_curl = get_curl_example(f"/api/Accounts/{account_id}", "GET")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving account: {str(e)}\n\nPlease verify that the account ID is valid and that your API credentials have sufficient permissions.\n\nYou can try testing the API directly using this curl command:\n```bash\n{example_curl}\n```"
                }],
                "error": str(e)
            }
    
    async def create_account(self, account_data: str) -> Dict[str, Any]:
        """
        Create a new account.
        
        Args:
            account_data: Account data in JSON format
            
        Returns:
            Dictionary with created account data
        """
        logger.info("Creating a new account")
        
        # Validate account_data isn't empty
        if not account_data or not account_data.strip():
            example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
            curl_example = get_curl_example("/api/Accounts", "POST", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"No account data provided. Please provide valid account data in JSON format.\n\nExample valid account data:\n```json\n{example_json}\n```\n\nExample curl command to create an account:\n```bash\n{curl_example}\n```"
                }],
                "error": "Account data is required"
            }
        
        try:
            # Parse the account data JSON
            account_dict = json.loads(account_data)
            
            # Basic validation: check for required fields
            required_fields = ["Name", "Email"]
            missing_fields = [field for field in required_fields if field not in account_dict]
            
            if missing_fields:
                example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
                curl_example = get_curl_example("/api/Accounts", "POST", example_json)
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Missing required fields: {', '.join(missing_fields)}. Required fields are: {', '.join(required_fields)}.\n\nExample valid account data:\n```json\n{example_json}\n```\n\nExample curl command to create an account:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Empty JSON object validation
            if len(account_dict) == 0:
                example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
                curl_example = get_curl_example("/api/Accounts", "POST", example_json)
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Empty JSON object provided. An account requires at minimum 'Name' and 'Email' fields.\n\nExample valid account data:\n```json\n{example_json}\n```\n\nExample curl command to create an account:\n```bash\n{curl_example}\n```"
                    }],
                    "error": "Empty account data"
                }
            
            # Call the API to create the account
            try:
                result = await self.client.create_account(account_data=account_dict)
                
                # Format the result for display
                if isinstance(result, dict):
                    created_id = result.get('ID', result.get('Id', result.get('id', 'Unknown')))
                    if created_id != 'Unknown':
                        return {
                            "content": [{
                                "type": "text",
                                "text": f"Account created successfully with ID: {created_id}\n\nFull response: {json.dumps(result, indent=2)}"
                            }]
                        }
                
                # If we couldn't extract an ID or the result is not a dict, just return the raw result
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Account created successfully: {json.dumps(result, indent=2)}"
                    }]
                }
            except HTTPException as api_error:
                logger.error(f"API error when creating account: {str(api_error)}")
                example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
                curl_example = get_curl_example("/api/Accounts", "POST", example_json)
                # Show the actual JSON sent in the error message
                error_details = str(api_error)
                if hasattr(api_error, 'detail'):
                    error_details = str(api_error.detail)
                
                return {
                    "content": [{
                        "type": "text",
                        "text": f"API Error: {error_details}\n\nThe following JSON data was sent:\n```json\n{json.dumps(account_dict, indent=2)}\n```\n\nPlease check that your account data format matches the API requirements. Note that the MSP360 API may expect specific field formats or have additional validation requirements.\n\nExample valid account data format:\n```json\n{example_json}\n```\n\nYou can try testing the API directly using this curl command:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"API Error: {error_details}"
                }
            except Exception as api_error:
                logger.error(f"API error when creating account: {str(api_error)}")
                example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
                curl_example = get_curl_example("/api/Accounts", "POST", example_json)
                # Show the actual JSON sent in the error message
                error_details = str(api_error)
                
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error: {error_details}\n\nThe following JSON data was sent:\n```json\n{json.dumps(account_dict, indent=2)}\n```\n\nPlease check that your account data format matches the API requirements and that your credentials have sufficient permissions.\n\nExample valid account data format:\n```json\n{example_json}\n```\n\nYou can try testing the API directly using this curl command:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"API Error: {error_details}"
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing account data JSON: {str(e)}")
            example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
            curl_example = get_curl_example("/api/Accounts", "POST", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error parsing account data: {str(e)}. Please provide valid JSON data.\n\nExample valid account data:\n```json\n{example_json}\n```\n\nExample curl command to create an account:\n```bash\n{curl_example}\n```"
                }],
                "error": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            example_json = """
{
  "Name": "Test Account",
  "Email": "test@example.com",
  "StorageLimit": 1000000000,
  "CompanyName": "Test Company"
}"""
            curl_example = get_curl_example("/api/Accounts", "POST", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error creating account: {str(e)}. Please ensure you're providing valid account data and that your API credentials have sufficient permissions.\n\nExample valid account data:\n```json\n{example_json}\n```\n\nExample curl command to create an account:\n```bash\n{curl_example}\n```"
                }],
                "error": str(e)
            }
    
    async def update_account(self, account_data: str) -> Dict[str, Any]:
        """
        Update an existing account.
        
        Args:
            account_data: Account data in JSON format
            
        Returns:
            Dictionary with updated account data
        """
        logger.info("Updating account")
        
        # Validate account_data isn't empty
        if not account_data or not account_data.strip():
            example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
            curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"No account data provided. Please provide valid account data in JSON format.\n\nExample valid account data for updating:\n```json\n{example_json}\n```\n\nExample curl command to update an account:\n```bash\n{curl_example}\n```"
                }],
                "error": "Account data is required"
            }
        
        try:
            # Parse the account data JSON
            account_dict = json.loads(account_data)
            
            # Basic validation: check for required fields
            # For updating, we need at minimum the ID field
            required_fields = ["ID"]
            missing_fields = [field for field in required_fields if field not in account_dict]
            
            if missing_fields:
                example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
                curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Missing required fields: {', '.join(missing_fields)}. When updating an account, you must include the account ID.\n\nExample valid account data for updating:\n```json\n{example_json}\n```\n\nExample curl command to update an account:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Call the API to update the account
            try:
                result = await self.client.update_account(account_data=account_dict)
                
                # Format the result for display
                if isinstance(result, dict):
                    updated_id = result.get('ID', result.get('Id', account_dict.get('ID', 'Unknown')))
                    if updated_id != 'Unknown':
                        return {
                            "content": [{
                                "type": "text",
                                "text": f"Account with ID '{updated_id}' updated successfully\n\nFull response: {json.dumps(result, indent=2)}"
                            }]
                        }
                
                # If we couldn't extract an ID or the result is not a dict, just return the raw result
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Account updated successfully: {json.dumps(result, indent=2)}"
                    }]
                }
            except HTTPException as api_error:
                logger.error(f"API error when updating account: {str(api_error)}")
                example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
                curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
                # Show the actual JSON sent in the error message
                error_details = str(api_error)
                if hasattr(api_error, 'detail'):
                    error_details = str(api_error.detail)
                
                return {
                    "content": [{
                        "type": "text",
                        "text": f"API Error: {error_details}\n\nThe following JSON data was sent:\n```json\n{json.dumps(account_dict, indent=2)}\n```\n\nPlease check that your account data format matches the API requirements. Note that the MSP360 API may expect specific field formats or have additional validation requirements.\n\nExample valid account data format:\n```json\n{example_json}\n```\n\nYou can try testing the API directly using this curl command:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"API Error: {error_details}"
                }
            except Exception as api_error:
                logger.error(f"API error when updating account: {str(api_error)}")
                example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
                curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
                # Show the actual JSON sent in the error message
                error_details = str(api_error)
                
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error: {error_details}\n\nThe following JSON data was sent:\n```json\n{json.dumps(account_dict, indent=2)}\n```\n\nPlease check that your account data format matches the API requirements and that your credentials have sufficient permissions.\n\nExample valid account data format:\n```json\n{example_json}\n```\n\nYou can try testing the API directly using this curl command:\n```bash\n{curl_example}\n```"
                    }],
                    "error": f"API Error: {error_details}"
                }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing account data JSON: {str(e)}")
            example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
            curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error parsing account data: {str(e)}. Please provide valid JSON data.\n\nExample valid account data for updating:\n```json\n{example_json}\n```\n\nExample curl command to update an account:\n```bash\n{curl_example}\n```"
                }],
                "error": f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error updating account: {str(e)}")
            example_json = """
{
  "ID": "account-id-here",
  "Name": "Updated Account Name",
  "Email": "updated@example.com"
}"""
            curl_example = get_curl_example("/api/Accounts", "PUT", example_json)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error updating account: {str(e)}. Please ensure you're providing valid account data with the correct ID and that your API credentials have sufficient permissions.\n\nExample valid account data for updating:\n```json\n{example_json}\n```\n\nExample curl command to update an account:\n```bash\n{curl_example}\n```"
                }],
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close resources."""
        logger.info("Closing account tools resources")

# Create instance for dependency injectionaccount_tools = AccountTools() 
