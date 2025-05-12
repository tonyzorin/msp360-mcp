"""Computer management tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
import logging
from services.msp360_client import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool
import json
from datetime import datetime

logger = logging.getLogger("msp360_mcp.tools")

class ComputerTools:
    """Tools for interacting with MSP360/CloudBerry computers (endpoints)."""
    
    class ComputerParams(BaseModel):
        """Parameters model for retrieving computers."""
        offset: Optional[int] = Field(0, description="Offset for pagination")
        count: Optional[int] = Field(10, description="Number of items to retrieve")
        computer_name: Optional[str] = Field(None, description="Filter by computer name")
        user_id: Optional[str] = Field(None, description="Filter by user ID")
        company_id: Optional[str] = Field(None, description="Filter by company ID")
        
    def __init__(self):
        """Initialize the computer tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Define all computer tools but don't register them globally."""
        self._tool_definitions["get_computers"] = {
            "description": "Get a list of MSP360 managed computers/endpoints",
            "function": self.get_computers,
            "parameter_descriptions": {
                "params": "Filter parameters as a JSON string"
            }
        }
        
        self._tool_definitions["get_computer"] = {
            "description": "Get a specific MSP360 computer by hardware ID (HID)",
            "function": self.get_computer,
            "parameter_descriptions": {
                "hid": "Hardware ID of the computer"
            }
        }
        
        self._tool_definitions["get_computer_plans"] = {
            "description": "Get backup/restore plans of a specific MSP360 computer",
            "function": self.get_computer_plans,
            "parameter_descriptions": {
                "hid": "Hardware ID of the computer"
            }
        }
        
        self._tool_definitions["remove_computer_authorization"] = {
            "description": "Remove authorization from a MSP360 computer",
            "function": self.remove_computer_authorization,
            "parameter_descriptions": {
                "hid": "Hardware ID of the computer"
            }
        }
        
        self._tool_definitions["update_computer_authorization"] = {
            "description": "Create/update authorization for a MSP360 computer",
            "function": self.update_computer_authorization,
            "parameter_descriptions": {
                "hid": "Hardware ID of the computer",
                "auth_data": "Optional authorization data in JSON format (can be omitted)"
            },
            "required_parameters": ["hid"]
        }
        
        self._tool_definitions["get_user_computers"] = {
            "description": "Get computers of a specific MSP360 user",
            "function": self.get_user_computers,
            "parameter_descriptions": {
                "user_id": "User ID"
            }
        }
        
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all computer tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_computers(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get a list of managed computers with optional filtering.
        
        Args:
            params: Filter parameters as a JSON string or a ComputerParams object
            
        Returns:
            Dictionary with computers data
        """
        logger.info(f"Getting computers with params: {params}")
        
        # Handle different types of params input
        if isinstance(params, self.ComputerParams):
            # Already a ComputerParams object from API endpoint
            param_dict = {
                'page': 1,  # Default page if offset is used directly
                'limit': params.count,
                'company_id': params.company_id,
                'user_id': params.user_id
            }
            
            # Convert offset back to page if needed
            if params.offset > 0 and params.count > 0:
                param_dict['page'] = (params.offset // params.count) + 1
            
            logger.info(f"Using params from ComputerParams object: offset={params.offset} count={params.count} computer_name={params.computer_name} user_id={params.user_id} company_id={params.company_id}")
            
        else:
            # Parse the JSON string to get parameters
            try:
                if params and isinstance(params, str) and params.strip():
                    param_dict = json.loads(params)
                else:
                    param_dict = {}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing parameters JSON: {str(e)}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error parsing parameters: {str(e)}"
                    }],
                    "error": f"Invalid JSON parameters: {str(e)}"
                }
        
        # Extract pagination parameters with defaults
        page = param_dict.get('page', 1)
        limit = param_dict.get('limit', 10)
        
        # Prepare query parameters including pagination
        query_params = {
            'page': page,
            'limit': limit
        }
        
        # Add filters if present
        if 'company_id' in param_dict and param_dict['company_id']:
            query_params['company_id'] = param_dict['company_id']
        if 'user_id' in param_dict and param_dict['user_id']:
            query_params['user_id'] = param_dict['user_id']
        if 'search' in param_dict:
            query_params['search'] = param_dict['search']
        if 'online' in param_dict:
            query_params['online'] = param_dict['online']
        
        # Debug log for query parameters
        logger.debug(f"Query parameters: {query_params}")
        
        try:
            # Call the API with params parameter
            computers = await self.client.get_computers(params=query_params)
            logger.debug(f"Retrieved computers response type: {type(computers)}")
            if computers:
                # Get the first 500 chars of the response for debugging
                logger.debug(f"Retrieved computers response preview: {json.dumps(computers)[:500] if computers else 'None'}")
                # Log keys if it's a dictionary
                if isinstance(computers, dict):
                    logger.debug(f"Response keys: {list(computers.keys())}")
            
            # Process the response for MCP
            result_content = []
            
            # Check if the response has the correct structure with Computers array
            if isinstance(computers, dict) and 'Computers' in computers:
                computer_list = computers['Computers']
                logger.debug(f"Found Computers list with {len(computer_list)} items")
                
                if not computer_list:
                    result_content.append({
                        "type": "text",
                        "text": "No computers found matching the criteria"
                    })
                else:
                    for computer in computer_list:
                        computer_text = []
                        # Format key properties for better readability
                        computer_text.append(f"HID: {computer.get('ComputerHID', 'N/A')}")
                        computer_text.append(f"Name: {computer.get('ComputerName', 'N/A')}")
                        computer_text.append(f"Display Name: {computer.get('ComputerDisplayName', 'N/A')}")
                        computer_text.append(f"Company: {computer.get('CompanyName', 'N/A')}")
                        computer_text.append(f"User: {computer.get('UserEmail', 'N/A')}")
                        computer_text.append(f"OS: {computer.get('OSTypeString', 'N/A')}")
                        
                        # Add backup status if available
                        if 'BackupStats' in computer and isinstance(computer['BackupStats'], dict):
                            backup_stats = computer['BackupStats']
                            computer_text.append(f"\nBackup Statistics:")
                            computer_text.append(f"  Plans: {backup_stats.get('PlansCount', 0)}")
                            computer_text.append(f"  Success: {backup_stats.get('TotalSuccessCount', 0)}")
                            computer_text.append(f"  Failed: {backup_stats.get('TotalFailedCount', 0)}")
                            computer_text.append(f"  Warning: {backup_stats.get('TotalWarningCount', 0)}")
                            computer_text.append(f"  Running: {backup_stats.get('TotalRunningCount', 0)}")
                        
                        # Add last activity if available
                        if 'LastActivity' in computer:
                            computer_text.append(f"\nLast Activity: {computer.get('LastActivity', 'N/A')}")
                        
                        result_content.append({
                            "type": "text",
                            "text": "\n".join(computer_text)
                        })
                    
                    # Add summary information
                    if 'Count' in computers:
                        result_content.append({
                            "type": "text",
                            "text": f"\nTotal computers: {computers.get('Count', 0)}"
                        })
            # Handle legacy format responses
            elif isinstance(computers, list):
                for computer in computers:
                    computer_text = []
                    for key, value in computer.items():
                        computer_text.append(f"{key}: {value}")
                    
                    result_content.append({
                        "type": "text",
                        "text": "\n".join(computer_text)
                    })
            else:
                # For empty or unexpected responses
                result_content.append({
                    "type": "text",
                    "text": f"No computers found or unexpected response format"
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving computers: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving computers: {str(e)}"
                }],
                "error": f"Failed to retrieve computers: {str(e)}"
            }
            
    async def get_computer(self, hid: str) -> Dict[str, Any]:
        """
        Get a specific computer by hardware ID (HID) with enhanced formatting.
        
        Args:
            hid: Hardware ID of the computer
            
        Returns:
            Dictionary with formatted computer data
        """
        logger.info(f"Getting computer with HID: {hid}")
        
        try:
            computer = await self.client.get_computer(hid=hid)
            
            if not computer:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"No computer found with HID: {hid}"
                    }],
                    "error": f"Computer with HID {hid} not found"
                }
            
            # Format computer data with better organization and nested field handling
            computer_text = []
            computer_text.append(f"ComputerHID: {computer.get('ComputerHID', 'N/A')}")
            
            # Basic information section
            basic_props = ['OSTypeString', 'BuildTypeString', 'RemoteManagementAvailable', 'ComputerName', 
                           'ComputerDisplayName', 'CompanyName', 'UserEmail', 'ProfileName', 'UserID', 'ProfileDisplayName']
            
            for prop in basic_props:
                if prop in computer:
                    computer_text.append(f"{prop}: {computer.get(prop, 'N/A')}")
            
            # Format build version info
            if 'BackupBuildVersion' in computer:
                build_version = computer.get('BackupBuildVersion')
                if isinstance(build_version, dict):
                    version_str = f"{build_version.get('_Major', '?')}.{build_version.get('_Minor', '?')}."
                    version_str += f"{build_version.get('_Build', '?')}.{build_version.get('_Revision', '?')}"
                    computer_text.append(f"Backup Version: {version_str}")
                else:
                    computer_text.append(f"BackupBuildVersion: {build_version}")
            
            # Format license information
            if 'License' in computer:
                license_info = computer.get('License')
                if isinstance(license_info, dict):
                    license_text = []
                    license_text.append("License Information:")
                    if 'Granted' in license_info:
                        license_text.append(f"  Status: {'Active' if license_info.get('Granted') else 'Inactive'}")
                    if 'IsTrial' in license_info:
                        license_text.append(f"  Type: {'Trial' if license_info.get('IsTrial') else 'Full'}")
                    if 'DisplayExpiresDate' in license_info:
                        license_text.append(f"  Expires: {license_info.get('DisplayExpiresDate')}")
                    computer_text.append("\n".join(license_text))
                else:
                    computer_text.append(f"License: {license_info}")
            
            # Format backup statistics
            if 'BackupStats' in computer:
                stats = computer.get('BackupStats')
                if isinstance(stats, dict):
                    stats_text = []
                    stats_text.append("Backup Statistics:")
                    stats_text.append(f"  Total Plans: {stats.get('PlansCount', 0)}")
                    stats_text.append(f"  Successful: {stats.get('TotalSuccessCount', 0)}")
                    stats_text.append(f"  Failed: {stats.get('TotalFailedCount', 0)}")
                    stats_text.append(f"  Warnings: {stats.get('TotalWarningCount', 0)}")
                    stats_text.append(f"  Running: {stats.get('TotalRunningCount', 0)}")
                    stats_text.append(f"  Not Run: {stats.get('TotalNotRunCount', 0)}")
                    stats_text.append(f"  Interrupted: {stats.get('TotalInterruptedCount', 0)}")
                    stats_text.append(f"  Overdue: {stats.get('TotalOverdueCount', 0)}")
                    computer_text.append("\n".join(stats_text))
                else:
                    computer_text.append(f"BackupStats: {stats}")
            
            # Time fields
            time_fields = ['LastActivity', 'LostAuthChangeDate']
            for field in time_fields:
                if field in computer:
                    computer_text.append(f"{field}: {computer.get(field)}")
            
            # Status fields
            status_fields = ['InstanceType', 'HasBackupApp', 'LostAuth', 'BackupStatus']
            for field in status_fields:
                if field in computer:
                    computer_text.append(f"{field}: {computer.get(field)}")
            
            # Format hardware usage info
            hw_fields = ['DiskInfoUsagePercent', 'MemoryInfoUsagePercent', 'CPUInfoUsagePercent']
            hw_info = []
            for field in hw_fields:
                if field in computer and computer.get(field, 0) > 0:
                    hw_info.append(f"  {field}: {computer.get(field)}%")
            
            if hw_info:
                computer_text.append("Hardware Usage:")
                computer_text.extend(hw_info)
            
            # Format installed applications
            if 'Apps' in computer:
                apps = computer.get('Apps')
                if isinstance(apps, list) and apps:
                    apps_text = []
                    apps_text.append("\nInstalled Applications:")
                    for app in apps:
                        if isinstance(app, dict):
                            app_id = app.get('ApplicationId', 'Unknown')
                            version = app.get('Version', 'Unknown')
                            status = app.get('VersionStatus', 'Unknown')
                            state = app.get('ApplicationState', 'Unknown')
                            online = 'Online' if app.get('Online', False) else 'Offline'
                            
                            app_line = f"  {app_id} (v{version}): {status}, {state}, {online}"
                            
                            # Add error information if present
                            if app.get('ErrorCode') or app.get('ErrorMessage'):
                                error_msg = app.get('ErrorMessage', 'Unknown error')
                                app_line += f" - Error: {error_msg}"
                                
                            apps_text.append(app_line)
                        else:
                            apps_text.append(f"  {app}")
                            
                    computer_text.append("\n".join(apps_text))
                elif isinstance(apps, list):
                    computer_text.append("Applications: None installed")
                else:
                    computer_text.append(f"Apps: {apps}")
            
            # Add any diagnostic events if present
            if 'DiagnosticEvents' in computer:
                events = computer.get('DiagnosticEvents')
                if isinstance(events, list) and events:
                    events_text = []
                    events_text.append("\nDiagnostic Events:")
                    for event in events:
                        if isinstance(event, dict):
                            event_text = []
                            for k, v in event.items():
                                event_text.append(f"  {k}: {v}")
                            events_text.append("\n".join(event_text))
                        else:
                            events_text.append(f"  {event}")
                    computer_text.append("\n".join(events_text))
                elif isinstance(events, list):
                    computer_text.append("Diagnostic Events: None")
            
            # Add any fields we didn't specifically handle
            processed_fields = set(basic_props + ['ComputerHID', 'BackupBuildVersion', 'License', 'BackupStats'] + 
                                  time_fields + status_fields + hw_fields + ['Apps', 'DiagnosticEvents'])
            
            remaining_fields = []
            for key, value in computer.items():
                if key not in processed_fields:
                    remaining_fields.append(f"{key}: {value}")
            
            if remaining_fields:
                computer_text.append("\nAdditional Information:")
                computer_text.extend(remaining_fields)
            
            return {
                "content": [{
                    "type": "text",
                    "text": "\n".join(computer_text)
                }]
            }
        except Exception as e:
            logger.error(f"Error retrieving computer {hid}: {str(e)}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving computer {hid}: {str(e)}"
                }],
                "error": f"Error retrieving computer {hid}: {str(e)}"
            }
            
    async def get_computer_plans(self, hid: str) -> Dict[str, Any]:
        """
        Get backup/restore plans of a specific computer.
        
        Args:
            hid: Hardware ID of the computer
            
        Returns:
            Dictionary with plan data in readable format
        """
        logger.info(f"Getting plans for computer with HID: {hid}")
        
        try:
            # Call the API to get the computer plans
            result = await self.client.get_computer_plans(hid=hid)
            
            # Format the plans data for better readability
            formatted_plans = self._format_plans_data(result)
            
            return {
                "content": [{
                    "type": "text",
                    "text": formatted_plans
                }]
            }
        except Exception as e:
            logger.error(f"Error retrieving plans for computer {hid}: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving plans for computer {hid}: {str(e)}"
                }]
            }
            
    def _format_plans_data(self, plans_data) -> str:
        """
        Format plans data into readable text.
        
        Args:
            plans_data: Plans data from API response
            
        Returns:
            Formatted string with plans information
        """
        if not plans_data:
            return "No plans found for this computer."
            
        # If the response is a string (possibly JSON), try to parse it
        if isinstance(plans_data, str):
            try:
                plans_data = json.loads(plans_data)
            except json.JSONDecodeError:
                # Try to clean up the string - sometimes there are escape characters
                try:
                    # Replace escaped quotes and other potential issues
                    cleaned_str = plans_data.replace('\\"', '"').replace('\\\\', '\\')
                    # Try again with the cleaned string
                    plans_data = json.loads(cleaned_str)
                    logger.info("Successfully parsed JSON after cleaning the string")
                except json.JSONDecodeError:
                    return f"Unable to parse plans data as JSON. Raw data: {plans_data[:200]}..."
                    
        # Helper function to format any value with appropriate indentation
        def format_value(value, indent_level=0, key=None):
            indent = "  " * indent_level
            
            if isinstance(value, dict):
                if not value:
                    return f"{indent}{key + ': ' if key else ''}Empty object"
                    
                lines = [f"{indent}{key + ':' if key else ''}"]
                for k, v in value.items():
                    lines.append(format_value(v, indent_level + 1, k))
                return "\n".join(lines)
                
            elif isinstance(value, list):
                if not value:
                    return f"{indent}{key + ': ' if key else ''}[]"
                    
                # If it's a list of simple values (strings, numbers)
                if all(not isinstance(item, (dict, list)) for item in value):
                    return f"{indent}{key + ': ' if key else ''}[{', '.join(repr(item) for item in value)}]"
                    
                # If it's a list of complex objects
                lines = [f"{indent}{key + ':' if key else ''}"]
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        # For dictionaries in a list, show a more compact representation with key identifiers
                        item_name = item.get('Name', item.get('VMName', item.get('ID', f'Item {i+1}')))
                        lines.append(f"{indent}[{i+1}] {item_name}:")
                        for k, v in item.items():
                            if k not in ('Name', 'VMName', 'ID') or k == 'Name' and item_name == f'Item {i+1}':
                                lines.append(format_value(v, indent_level + 2, k))
                    else:
                        lines.append(format_value(item, indent_level + 1, f"[{i+1}]"))
                return "\n".join(lines)
                
            else:
                # For simple values
                return f"{indent}{key}: {value}"

        # Process the plans data
        if isinstance(plans_data, list):
            if not plans_data:
                return "No plans found for this computer."
                
            plans_text = []
            for idx, plan in enumerate(plans_data, 1):
                if isinstance(plan, dict):
                    # Get the plan type if available
                    plan_type = plan.get('PlanType', 'Unknown')
                    plan_xsi_type = plan.get('PlanXsiType', '')
                    
                    plan_text = [f"Plan #{idx}:"]
                    plan_text.append(f"  PlanType: {plan_type}")
                    if plan_xsi_type:
                        plan_text.append(f"  PlanXsiType: {plan_xsi_type}")
                    
                    # Special handling for the Plan object which contains all the details
                    if 'Plan' in plan and isinstance(plan['Plan'], dict):
                        plan_text.append("  Plan:")
                        plan_obj = plan['Plan']
                        for key, value in plan_obj.items():
                            formatted = format_value(value, 2, key)
                            plan_text.append(formatted)
                    else:
                        # For other plan fields
                        for key, value in plan.items():
                            if key not in ('PlanType', 'PlanXsiType', 'Plan'):
                                formatted = format_value(value, 2, key)
                                plan_text.append(formatted)
                else:
                    # If plan is not a dict, just convert to string
                    plan_text = [f"Plan #{idx}: {str(plan)}"]
                
                plans_text.append("\n".join(plan_text))
            
            return "\n\n".join(plans_text)
        
        # If we have a dictionary with plans
        elif isinstance(plans_data, dict):
            # Try different possible keys for plans
            for plans_key in ['Plans', 'plans', 'PlanList']:
                if plans_key in plans_data and isinstance(plans_data[plans_key], list):
                    return self._format_plans_data(plans_data[plans_key])
            
            # If no plans list was found, just format the dictionary
            formatted = format_value(plans_data, 0, "Plan data")
            return formatted
            
        # For other types of responses
        return f"Unexpected plans data format: {str(plans_data)[:500]}..."
            
    async def remove_computer_authorization(self, hid: str) -> Dict[str, Any]:
        """
        Remove authorization from a computer.
        
        Args:
            hid: Hardware ID of the computer
            
        Returns:
            Dictionary with result
        """
        logger.info(f"Removing authorization for computer with HID: {hid}")
        
        try:
            result = await self.client.remove_computer_authorization(hid=hid)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Authorization successfully removed for computer with HID: {hid}"
                }]
            }
        except Exception as e:
            logger.error(f"Error removing authorization for computer {hid}: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error removing authorization for computer {hid}: {str(e)}"
                }],
                "error": f"Error removing authorization for computer {hid}: {str(e)}"
            }
            
    async def update_computer_authorization(self, hid: str, auth_data: str = "{}") -> Dict[str, Any]:
        """
        Create/update authorization for a computer.
        
        Args:
            hid: Hardware ID of the computer
            auth_data: Optional authorization data in JSON format
            
        Returns:
            Dictionary with result
        """
        logger.info(f"Updating authorization for computer with HID: {hid}")
        
        try:
            # Parse the JSON string if provided
            parsed_data = {}
            if auth_data and auth_data.strip() != "{}":
                try:
                    parsed_data = json.loads(auth_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON auth data: {str(e)}")
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"Invalid JSON auth data: {str(e)}"
                        }],
                        "error": f"Invalid JSON auth data: {str(e)}"
                    }
                
            result = await self.client.update_computer_authorization(hid=hid, auth_data=parsed_data)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Authorization successfully updated for computer with HID: {hid}"
                }]
            }
        except Exception as e:
            logger.error(f"Error updating authorization for computer {hid}: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error updating authorization for computer {hid}: {str(e)}"
                }],
                "error": f"Error updating authorization for computer {hid}: {str(e)}"
            }
            
    async def get_user_computers(self, user_id: str) -> Dict[str, Any]:
        """
        Get computers of a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user's computers data
        """
        logger.info(f"Getting computers for user with ID: {user_id}")
        
        try:
            # Reuse the get_computers method with user_id filter
            params_json = json.dumps({
                "user_id": user_id
            })
            
            return await self.get_computers(params=params_json)
        except Exception as e:
            logger.error(f"Error retrieving computers for user {user_id}: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving computers for user {user_id}: {str(e)}"
                }],
                "error": f"Error retrieving computers for user {user_id}: {str(e)}"
            }
            
    def close(self) -> None:
        """Close any resources."""
        pass

# Create instance for dependency injection
computer_tools = ComputerTools() 