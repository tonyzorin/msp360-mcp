"""Utility functions for MSP360 MCP Server tools."""
import logging
from typing import Dict, Any, List, Union
import datetime
import json

logger = logging.getLogger("msp360_mcp.utils")

def format_size(size_bytes: Union[int, float, str]) -> str:
    """Format bytes into human-readable size string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    # Handle non-numeric input
    if not isinstance(size_bytes, (int, float)):
        try:
            size_bytes = float(size_bytes)
        except (ValueError, TypeError):
            return f"{size_bytes}"
            
    if size_bytes == 0:
        return "0 B (Empty)"
        
    # Define size units
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Calculate appropriate unit
    i = 0
    size_value = size_bytes
    while size_value >= 1024 and i < len(units) - 1:
        size_value /= 1024
        i += 1
        
    # Format with appropriate precision
    if i == 0:  # bytes
        return f"{size_value:.0f} {units[i]}"
    else:
        return f"{size_value:.2f} {units[i]}"

def humanize_time(timestamp_str: str) -> str:
    """
    Convert a timestamp string to a human-readable format (e.g., "2 days ago")
    
    Args:
        timestamp_str: ISO 8601 timestamp string
        
    Returns:
        Human-readable time string
    """
    # Check for None or empty string
    if timestamp_str is None or timestamp_str == 'N/A':
        return "Never"
    if not timestamp_str or not isinstance(timestamp_str, str):
        return timestamp_str
    
    # Handle API-specific date formats
    if 'Z' in timestamp_str:
        # Convert from API format to ISO format
        timestamp_str = timestamp_str.replace('Z', '+00:00')
        
    try:
        # Try parsing the timestamp as ISO format
        try:
            timestamp = datetime.datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Try parsing with different formats
            try:
                # Try standard API format
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    # Try without microseconds
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    # Return the original if we can't parse it
                    return timestamp_str
        
        # For future dates relative to now, just show the formatted date
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Add UTC timezone if the timestamp doesn't have one
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=datetime.timezone.utc)
            
        # Make now timezone-aware if it isn't already
        if now.tzinfo is None:
            now = now.replace(tzinfo=datetime.timezone.utc)
            
        # Format future dates or dates beyond the current year
        if timestamp > now or timestamp.year > now.year:
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate the difference
        diff = now - timestamp
        
        # Format the difference in a human-readable way
        if diff.days < 0:
            # Future date
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        elif diff.days == 0:
            # Today
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                if minutes == 0:
                    return "Just now"
                elif minutes == 1:
                    return "1 minute ago"
                else:
                    return f"{minutes} minutes ago"
            elif hours == 1:
                return "1 hour ago"
            else:
                return f"{hours} hours ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            if weeks == 1:
                return "1 week ago"
            else:
                return f"{weeks} weeks ago"
        elif diff.days < 365:
            months = diff.days // 30
            if months == 1:
                return "1 month ago"
            else:
                return f"{months} months ago"
        else:
            years = diff.days // 365
            if years == 1:
                return "1 year ago"
            else:
                return f"{years} years ago"
    except Exception:
        # Just return the original string without logging warnings
        return timestamp_str

def format_json_field(field_name: str, value: Any) -> str:
    """Format a JSON field with appropriate representation based on type.
    
    Args:
        field_name: The name of the field
        value: The field value
        
    Returns:
        Formatted string representation of the field
    """
    if value is None:
        return f"{field_name}: None"
        
    if isinstance(value, bool):
        return f"{field_name}: {'Yes' if value else 'No'}"
        
    if isinstance(value, (int, float)) and field_name.lower().endswith(('size', 'bytes', 'limit', 'usage')):
        # Format as size if it seems to be a size-related field
        return f"{field_name}: {format_size(value)}"
        
    if isinstance(value, list):
        if not value:
            return f"{field_name}: []"
        elif len(value) == 1:
            return f"{field_name}: {value[0]}"
        else:
            return f"{field_name}: {len(value)} items"
            
    if isinstance(value, dict):
        return f"{field_name}: {len(value.keys())} properties"
        
    # Default case: return as string
    return f"{field_name}: {value}"

def parse_params_json(params_str: str, default_params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse a JSON string into a dictionary of parameters.
    
    Args:
        params_str: JSON string with parameters
        default_params: Default parameters to use if parsing fails
        
    Returns:
        Dictionary of parameters
    """
    if default_params is None:
        default_params = {}
        
    try:
        if params_str and params_str.strip():
            return json.loads(params_str)
        else:
            return default_params.copy()
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing parameters JSON: {str(e)}")
        return default_params.copy()

def convert_pagination(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert page/limit pagination to skip/take used by some MSP360 APIs.
    
    Args:
        params: Parameters dictionary with page and limit
        
    Returns:
        Updated parameters with skip and take
    """
    result = params.copy()
    
    if 'page' in result and 'limit' in result:
        page = result.pop('page')
        limit = result.pop('limit')
        result['skip'] = (page - 1) * limit
        result['take'] = limit
        
    return result

def normalize_field_names(data: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Normalize field names using a mapping dictionary.
    
    Args:
        data: Input data dictionary
        field_mapping: Mapping of input field names (lowercase) to output field names
        
    Returns:
        Dictionary with normalized field names
    """
    normalized = {}
    
    for key, value in data.items():
        # Find the standard key name, defaulting to the original key if not in mapping
        standard_key = field_mapping.get(key.lower(), key)
        normalized[standard_key] = value
        
    return normalized 