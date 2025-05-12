"""Helper functions for backup and monitoring data formatting."""
from typing import Dict, Any, List
import logging
import json
from tools.utils import format_size, humanize_time

logger = logging.getLogger("msp360_mcp.tools")

def format_monitoring_item(item: Dict[str, Any]) -> str:
    """
    Format a monitoring item into a readable string.
    
    Args:
        item: The monitoring item data
        
    Returns:
        Formatted monitoring item text
    """
    # Try to parse ErrorMessage as JSON if it's a string
    error_message = item.get('ErrorMessage', 'N/A')
    error_message_text = "ErrorMessage: "
    
    if isinstance(error_message, str) and error_message.strip().startswith('['):
        try:
            # Try to parse it as JSON
            error_message_list = json.loads(error_message)
            # Format JSON error messages nicely
            formatted_errors = []
            for err in error_message_list:
                formatted_error = (
                    f"  - {err.get('title', 'Unknown error')}\n"
                    f"    Code: {err.get('code', 'N/A')}\n"
                    f"    Detail: {err.get('detail', 'N/A')}\n"
                    f"    Priority: {err.get('priority', 'N/A')}"
                )
                if err.get('kbid'):
                    formatted_error += f"\n    KB Article: {err.get('kbid')}"
                formatted_errors.append(formatted_error)
            
            if formatted_errors:
                error_message_text += "\n" + "\n".join(formatted_errors)
            else:
                error_message_text += "No details available in JSON error"
        except json.JSONDecodeError:
            # If it fails, try to make it more readable
            error_message_text += error_message.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
    else:
        error_message_text += str(error_message)
    
    # Format each monitoring item as a text item
    formatted_text = (
        f"PlanName: {item.get('PlanName', 'N/A')}\n"
        f"CompanyName: {item.get('CompanyName', 'N/A')}\n"
        f"UserName: {item.get('UserName', 'N/A')}\n"
        f"UserID: {item.get('UserID', 'N/A')}\n"
        f"ComputerName: {item.get('ComputerName', 'N/A')}\n"
        f"ComputerHid: {item.get('ComputerHid', 'N/A')}\n"
        f"BuildVersion: {item.get('BuildVersion', 'N/A')}\n"
        f"StorageType: {item.get('StorageType', 'N/A')}\n"
        f"LastStart: {item.get('LastStart', 'N/A')}\n"
        f"NextStart: {item.get('NextStart', 'N/A')}\n"
        f"Status: {item.get('Status', 'N/A')}\n"
        f"{error_message_text}\n"
        f"FilesCopied: {item.get('FilesCopied', 'N/A')}\n"
        f"FilesFailed: {item.get('FilesFailed', 'N/A')}\n"
        f"DataCopied: {item.get('DataCopied', 'N/A')}\n"
        f"Duration: {item.get('Duration', 'N/A')}\n"
        f"DataToBackup: {item.get('DataToBackup', 'N/A')}\n"
        f"TotalData: {item.get('TotalData', 'N/A')}\n"
        f"FilesScanned: {item.get('FilesScanned', 'N/A')}\n"
        f"FilesToBackup: {item.get('FilesToBackup', 'N/A')}\n"
        f"PlanId: {item.get('PlanId', 'N/A')}\n"
        f"PlanType: {item.get('PlanType', 'N/A')}\n"
        f"DetailedReportLink: {item.get('DetailedReportLink', 'N/A')}"
    )
    
    return formatted_text

def format_backup_summary(items: List[Dict[str, Any]]) -> str:
    """
    Format a summary of backup monitoring items.
    
    Args:
        items: List of monitoring items
        
    Returns:
        Formatted summary text
    """
    if not items:
        return "No backup data available."
    
    # Count items by status
    status_counts = {}
    for item in items:
        status = item.get('Status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Format the summary
    summary_lines = ["Backup Summary:"]
    summary_lines.append(f"Total backup items: {len(items)}")
    
    for status, count in status_counts.items():
        summary_lines.append(f"{status}: {count}")
    
    # Add more detailed summary if needed
    companies = set()
    users = set()
    for item in items:
        company = item.get('CompanyName')
        if company and company != 'N/A':
            companies.add(company)
        
        user = item.get('UserName')
        if user and user != 'N/A':
            users.add(user)
    
    summary_lines.append(f"\nUnique companies: {len(companies)}")
    summary_lines.append(f"Unique users: {len(users)}")
    
    return "\n".join(summary_lines)

def format_report_content(html_content: str, max_lines: int = 100) -> str:
    """
    Format HTML report content into plain text.
    
    Args:
        html_content: HTML content of the report
        max_lines: Maximum number of lines to include
        
    Returns:
        Formatted text representation of the report
    """
    import re
    
    if not html_content:
        return "Empty report content."
    
    # Extract the report data from HTML - simple approach
    lines = html_content.split('\n')
    text_lines = []
    
    for line in lines:
        clean_line = re.sub(r'<[^>]+>', '', line).strip()
        if clean_line:
            text_lines.append(clean_line)
    
    # Limit the number of lines
    if len(text_lines) > max_lines:
        text_lines = text_lines[:max_lines]
        text_lines.append(f"\n... (truncated, showing {max_lines} of {len(text_lines)} lines)")
    
    return "\n".join(text_lines) 