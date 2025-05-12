"""Helper functions for administrator management tools."""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from tools.utils import format_json_field, humanize_time, format_size

logger = logging.getLogger("msp360_mcp.tools")

def format_admin_data(admin: Dict[str, Any]) -> str:
    """Format administrator data into a readable text string.
    
    Args:
        admin: Administrator data dictionary
        
    Returns:
        Formatted string representation of the administrator
    """
    # Start with essential information
    formatted_text = []
    
    # Extract ID
    admin_id = admin.get('AdminID', 'N/A')
    formatted_text.append(f"Administrator ID: {admin_id}")
    
    # Extract name using FirstName and LastName
    first_name = admin.get('FirstName', '')
    last_name = admin.get('LastName', '')
    name = f"{first_name} {last_name}".strip() if first_name or last_name else 'N/A'
    formatted_text.append(f"Name: {name}")
    
    # Extract email
    email = admin.get('Email', 'N/A')
    formatted_text.append(f"Email: {email}")
    
    # Extract role based on AccountType
    account_type = admin.get('AccountType', 2)  # Default to regular admin
    role = 'Super Admin' if account_type == 1 else 'Regular Admin'
    formatted_text.append(f"Role: {role}")
    
    # Extract and format last login time
    last_login = admin.get('LastLogin')
    if last_login is None or last_login == '':
        formatted_text.append("Last Login: N/A")
    else:
        # Format future dates directly
        try:
            # Try to parse the date
            timestamp = last_login.replace('Z', '+00:00')
            login_date = datetime.fromisoformat(timestamp)
            formatted_date = login_date.strftime("%Y-%m-%d %H:%M:%S")
            formatted_text.append(f"Last Login: {formatted_date}")
        except (ValueError, TypeError):
            # If there's an error parsing, just show the original
            formatted_text.append(f"Last Login: {last_login}")
    
    # Join all parts with newlines
    return "\n".join(formatted_text)

def format_permissions(permissions: Dict[str, Any]) -> List[str]:
    """Format permissions data into a list of readable strings.
    
    Args:
        permissions: Permissions dictionary
        
    Returns:
        List of formatted permission strings
    """
    if not permissions or not isinstance(permissions, dict):
        return []
    
    result = []
    
    # Common permission sections to check
    sections = [
        "Users", "Companies", "Builds", "Licenses", 
        "Admin", "Settings", "Reports", "Accounts", 
        "Computers", "Billing", "Monitoring"
    ]
    
    # Format for different permission structures
    for section in sections:
        # Check for exact section name
        if section in permissions:
            section_perms = permissions[section]
            if isinstance(section_perms, dict):
                # Dictionary format with specific permissions
                perm_list = []
                for perm_name, value in section_perms.items():
                    if isinstance(value, bool) and value:
                        perm_list.append(perm_name)
                if perm_list:
                    result.append(f"{section}: {', '.join(perm_list)}")
            elif isinstance(section_perms, bool) and section_perms:
                # Simple boolean format
                result.append(f"{section}: Full Access")
        
        # Check for lowercase section name
        lowercase_section = section.lower()
        if lowercase_section in permissions and lowercase_section != section:
            section_perms = permissions[lowercase_section]
            if isinstance(section_perms, dict):
                # Dictionary format with specific permissions
                perm_list = []
                for perm_name, value in section_perms.items():
                    if isinstance(value, bool) and value:
                        perm_list.append(perm_name)
                if perm_list:
                    result.append(f"{section}: {', '.join(perm_list)}")
            elif isinstance(section_perms, bool) and section_perms:
                # Simple boolean format
                result.append(f"{section}: Full Access")
    
    # Check for any additional permissions not in the common sections
    for key, value in permissions.items():
        if key not in sections and key.lower() not in [s.lower() for s in sections]:
            if isinstance(value, bool) and value:
                result.append(f"{key}: Enabled")
            elif isinstance(value, dict):
                perm_list = []
                for perm_name, perm_value in value.items():
                    if isinstance(perm_value, bool) and perm_value:
                        perm_list.append(perm_name)
                if perm_list:
                    result.append(f"{key}: {', '.join(perm_list)}")
    
    return result 