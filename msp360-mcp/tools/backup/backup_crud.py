"""CRUD operations for backup management."""
from typing import Dict, Any, Optional, List
import logging
import json
import httpx
import re
from datetime import datetime
from services.msp360 import msp360_client
from tools.utils import parse_params_json
from .backup_helpers import format_monitoring_item, format_report_content

logger = logging.getLogger("msp360_mcp.tools")

async def get_monitoring_data_list(client, params_str: str) -> Dict[str, Any]:
    """Get monitoring data with filtering options.
    
    Args:
        client: MSP360 API client
        params_str: JSON string with filter parameters
        
    Returns:
        Dictionary with monitoring data for MCP
    """
    # Parse params if it's a string
    if isinstance(params_str, str):
        try:
            params_dict = parse_params_json(params_str, {})
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON params: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Invalid JSON in params: {str(e)}"
                }],
                "error": f"Invalid JSON in params: {str(e)}"
            }
    else:
        params_dict = params_str
    
    query_params = {}
    
    # Add pagination - extract and pass directly, client will convert to skip/take
    if 'page' in params_dict:
        query_params["page"] = params_dict.get('page', 1)
    
    if 'limit' in params_dict:
        query_params["limit"] = params_dict.get('limit', 10)
    
    # Add filters
    user_id = params_dict.get('user_id')
    if user_id:
        query_params["userId"] = user_id
        
    company_id = params_dict.get('company_id')
    if company_id:
        query_params["companyId"] = company_id
        
    from_date = params_dict.get('from_date')
    if from_date:
        if isinstance(from_date, datetime):
            query_params["fromDate"] = from_date.isoformat()
        else:
            query_params["fromDate"] = from_date
        
    to_date = params_dict.get('to_date')
    if to_date:
        if isinstance(to_date, datetime):
            query_params["toDate"] = to_date.isoformat()
        else:
            query_params["toDate"] = to_date
        
    status = params_dict.get('status')
    if status:
        query_params["status"] = status
    
    logger.debug(f"Calling get_monitoring with query_params: {query_params}")
    
    try:
        response = await client.get_monitoring(params=query_params)
        
        # Format the response for Cursor MCP client compatibility
        result_content = []
        
        # Check if the response is a list or has a specific structure
        if isinstance(response, list):
            monitoring_data = response
        elif isinstance(response, dict):
            # Extract the monitoring data based on the response structure
            if 'items' in response and isinstance(response['items'], list):
                monitoring_data = response['items']
            elif 'content' in response and isinstance(response['content'], list):
                monitoring_data = response['content']
            else:
                monitoring_data = []
        else:
            monitoring_data = []
        
        logger.info(f"Retrieved {len(monitoring_data)} monitoring items")
        
        # Extract pagination parameters
        page = int(params_dict.get('page', 1))
        limit = int(params_dict.get('limit', 10))
        
        # Apply client-side pagination 
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        # Slice the array to get only the items for the requested page
        if monitoring_data and start_index < len(monitoring_data):
            page_items = monitoring_data[start_index:end_index]
            logger.info(f"Applied pagination: page {page}, limit {limit}, showing items {start_index+1}-{min(end_index, len(monitoring_data))} of {len(monitoring_data)}")
            
            # Format each monitoring item as a text item
            for item in page_items:
                item_text = format_monitoring_item(item)
                result_content.append({
                    "type": "text",
                    "text": item_text
                })
        else:
            if len(monitoring_data) == 0:
                message = "No monitoring data found matching the specified criteria"
            else:
                message = f"No data available for page {page} (total items: {len(monitoring_data)})"
                
            result_content.append({
                "type": "text",
                "text": message
            })
        
        return {
            "content": result_content
        }
        
    except Exception as e:
        logger.error(f"Error retrieving monitoring data: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error retrieving monitoring data: {str(e)}"
            }],
            "error": str(e)
        }

async def get_monitoring_item_detail(client, item_id: str) -> Dict[str, Any]:
    """Get a specific monitoring item by ID.
    
    Args:
        client: MSP360 API client
        item_id: Monitoring item ID
        
    Returns:
        Dictionary with monitoring item data for MCP
    """
    if not item_id:
        return {
            "content": [{
                "type": "text",
                "text": "No monitoring item ID provided."
            }],
            "error": "Missing item ID"
        }
        
    try:
        item = await client.get_monitoring_item(item_id=item_id)
        
        if not item:
            return {
                "content": [{
                    "type": "text",
                    "text": f"No monitoring item found with ID: {item_id}"
                }]
            }
        
        # Format the item
        item_text = format_monitoring_item(item)
        
        return {
            "content": [{
                "type": "text",
                "text": item_text
            }]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving monitoring item {item_id}: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error retrieving monitoring item: {str(e)}"
            }],
            "error": str(e)
        }

async def get_user_monitoring_data(client, user_id: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """Get monitoring data for a specific user.
    
    Args:
        client: MSP360 API client
        user_id: User ID
        page: Page number (default: 1)
        limit: Number of items per page (default: 10)
        
    Returns:
        Dictionary with monitoring data for MCP
    """
    if not user_id:
        return {
            "content": [{
                "type": "text",
                "text": "No user ID provided."
            }],
            "error": "Missing user ID"
        }
        
    # Create params dictionary for reuse
    params = {
        "page": page,
        "limit": limit,
        "user_id": user_id
    }
    
    return await get_monitoring_data_list(client, params)

async def get_detailed_report_data(client, report_url: str) -> Dict[str, Any]:
    """Get a detailed report from a URL.
    
    Args:
        client: MSP360 API client
        report_url: URL for the detailed report
        
    Returns:
        Dictionary with report data for MCP
    """
    if not report_url or report_url == "N/A":
        return {
            "content": [{
                "type": "text",
                "text": "No report URL provided or URL is not available."
            }],
            "error": "Invalid report URL"
        }
    
    try:
        # Handle URL redirects - if the URL contains 'ws.mspbackups.com', 
        # replace with 'mspbackups.com' to avoid redirect issues
        if 'ws.mspbackups.com' in report_url:
            report_url = report_url.replace('ws.mspbackups.com', 'mspbackups.com')
            logger.info(f"Updated report URL to: {report_url}")
        
        # Add https:// if it's missing
        if not report_url.startswith('http'):
            report_url = f"https://{report_url}"
            logger.info(f"Added protocol to URL: {report_url}")
            
        # Create a custom httpx client that follows redirects
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            response = await client.get(report_url, headers=headers)
            logger.info(f"Report URL response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"HTTP error retrieving detailed report: {response.status_code} - {response.reason_phrase}")
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Failed to retrieve report: HTTP {response.status_code} - {response.reason_phrase}"
                    }],
                    "error": f"Failed to retrieve report: HTTP {response.status_code} - {response.reason_phrase}"
                }
            
            # Parse the HTML response
            html_content = response.text
            
            if not html_content:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Retrieved empty report content."
                    }],
                    "error": "Empty report content"
                }
            
            # Format the HTML content as plain text
            formatted_text = format_report_content(html_content)
            
            # Format the response
            result_content = [{
                "type": "text",
                "text": f"Detailed Report:\n\n{formatted_text}"
            }]
            
            return {"content": result_content}
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error retrieving detailed report: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to retrieve report: {str(e)}"
            }],
            "error": f"Failed to retrieve report: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error retrieving detailed report: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Failed to retrieve report: {str(e)}"
            }],
            "error": f"Failed to retrieve report: {str(e)}"
        } 