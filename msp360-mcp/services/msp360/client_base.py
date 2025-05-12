"""Base client for MSP360 API."""
import httpx
import logging
import json
from typing import Dict, Any, Optional
import sys
import os

from fastapi import HTTPException

# Import settings using a more robust path manipulation
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(current_dir)
project_dir = os.path.dirname(services_dir)
msp360_mcp_dir = os.path.join(project_dir, 'msp360-mcp')

# Add the msp360-mcp directory to the path
if msp360_mcp_dir not in sys.path:
    sys.path.insert(0, msp360_mcp_dir)

# Now we can import from core
from core.config import settings

from .auth import TokenManager

logger = logging.getLogger("msp360_mcp.client")

class MSP360ClientBase:
    """Base client for interacting with MSP360/CloudBerry API."""
    
    def __init__(self):
        """Initialize the base client."""
        self.base_url = settings.MSP360_API_BASE_URL
        self.timeout = settings.API_TIMEOUT
        self.token_manager = TokenManager(
            login=settings.MSP360_API_LOGIN,
            password=settings.MSP360_API_PASSWORD,
            token_lifetime=settings.TOKEN_LIFETIME
        )
    
    def update_credentials(self, login: str, password: str):
        """Update the API credentials at runtime.
        
        Args:
            login: New API login
            password: New API password
        """
        logger.info(f"Updating MSP360 API credentials for login: {login}")
        # Update the token manager with new credentials
        self.token_manager.login = login
        self.token_manager.password = password
        # Reset token to force regeneration with new credentials
        self.token_manager.current_token = None
        self.token_manager.token_expiry = None
    
    def _client_session(self) -> httpx.AsyncClient:
        """Create a new client session.
        
        Returns:
            An httpx AsyncClient instance configured with the appropriate timeout
        """
        return httpx.AsyncClient(timeout=self.timeout)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a request to the MSP360 API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            data: Form data
            headers: Custom headers
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        # Force token refresh and header generation right before the call
        logger.debug("Forcing token check and header generation right before request...")
        try:
            # Get fresh auth headers directly
            auth_headers = await self.token_manager.get_auth_header()
            logger.debug(f"Fresh auth headers generated: {auth_headers}")
        except Exception as token_err:
            logger.error(f"Error getting auth header just before request: {token_err}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve authentication token before request: {str(token_err)}")

        # Start with default headers
        final_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add authentication headers
        final_headers.update(auth_headers)

        # Add any custom headers passed to the function
        if headers:
            final_headers.update(headers)
        
        # Basic Auth handling (shouldn't be active based on settings, but keep logic)
        auth = None
        if settings.USE_BASIC_AUTH:
            auth = (settings.MSP360_API_LOGIN, settings.MSP360_API_PASSWORD)
            # Remove bearer token if we're using basic auth
            if "Authorization" in final_headers:
                del final_headers["Authorization"]
        
        logger.info(f"Making request to {url}")
        # Debug Logging
        logger.debug(f"Request Method: {method}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Params: {params}")
        if json_data:
            logger.debug(f"Request JSON: {json.dumps(json_data)[:1000]}")
        logger.debug(f"Request Data: {data}")
        logger.debug(f"FINAL Request Headers sent to httpx: {final_headers}")
        logger.debug(f"Request Auth (basic): {auth}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=final_headers,
                    auth=auth
                )
                
                # Log detailed response information
                logger.debug(f"Response Status Code: {response.status_code}")
                logger.debug(f"Response Headers: {response.headers}")
                content_type = response.headers.get("content-type", "unknown")
                logger.debug(f"Response Content-Type: {content_type}")
                
                # Log the response text limited to the first 500 characters
                response_text_sample = response.text[:500]
                logger.debug(f"Response Text (first 500 chars): {response_text_sample}")
                
                # Check for common error status codes
                if response.status_code == 403:
                    error_msg = f"API access forbidden (403): The API rejected the request with Forbidden status. This usually means invalid credentials or insufficient permissions."
                    logger.error(error_msg)
                    try:
                        error_data = response.json()
                        logger.error(f"API 403 error details: {error_data}")
                    except:
                        logger.error(f"API 403 response text: {response.text[:500]}")
                    raise HTTPException(status_code=403, detail=error_msg)
                
                # Raise exception for other error status codes
                response.raise_for_status()
                
                # Return JSON response if available and parseable
                if content_type.startswith("application/json"):
                    try:
                        # Parse the JSON response
                        json_data = response.json()
                        logger.debug(f"JSON response parsed, type: {type(json_data)}")
                        
                        # Return the parsed data directly
                        return json_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {str(e)}")
                        # Check the length of the text response
                        if len(response.text) <= 500:
                            # Return the full text for reasonably sized responses
                            return {"status": "success", "status_code": response.status_code, "text": response.text}
                        else:
                            # Truncate long responses and indicate the total size
                            truncated_text = response.text[:200] + "..."
                            return {
                                "status": "success", 
                                "status_code": response.status_code, 
                                "text": truncated_text,
                                "text_length": len(response.text),
                                "note": f"Response truncated. Full length: {len(response.text)} characters."
                            }
                
                # For non-JSON responses, try to return a structured response
                return {
                    "status": "success", 
                    "status_code": response.status_code, 
                    "content_type": content_type,
                    "text": response.text[:500] if len(response.text) > 500 else response.text,
                    "text_length": len(response.text)
                }
                
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            error_msg = f"HTTP error {status_code}: {str(e)}"
            
            # Try to parse error response
            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    if "message" in error_data:
                        error_msg = f"HTTP error {status_code}: {error_data['message']}"
                    elif "error" in error_data:
                        error_msg = f"HTTP error {status_code}: {error_data['error']}"
                    elif "error_description" in error_data:
                        error_msg = f"HTTP error {status_code}: {error_data['error_description']}"
                # Log the full error data
                logger.error(f"API error response: {json.dumps(error_data)}")
            except:
                # If can't parse as JSON, try to use text
                if e.response.text:
                    error_msg = f"HTTP error {status_code}: {e.response.text[:200]}"
                    logger.error(f"API error response text: {e.response.text[:500]}")
            
            logger.error(error_msg)
            raise HTTPException(status_code=status_code, detail=error_msg)
            
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Convenience method for GET requests.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Custom headers
            
        Returns:
            API response as dictionary
        """
        return await self._make_request(method="GET", endpoint=endpoint, params=params, headers=headers)
    
    async def _post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Convenience method for POST requests.
        
        Args:
            endpoint: API endpoint path
            json: JSON body data
            data: Form data
            headers: Custom headers
            
        Returns:
            API response as dictionary
        """
        return await self._make_request(method="POST", endpoint=endpoint, json_data=json, data=data, headers=headers)
    
    async def _put(self, endpoint: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Convenience method for PUT requests.
        
        Args:
            endpoint: API endpoint path
            json: JSON body data
            data: Form data
            headers: Custom headers
            
        Returns:
            API response as dictionary
        """
        return await self._make_request(method="PUT", endpoint=endpoint, json_data=json, data=data, headers=headers)
    
    async def _delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Convenience method for DELETE requests.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Custom headers
            
        Returns:
            API response as dictionary
        """
        return await self._make_request(method="DELETE", endpoint=endpoint, params=params, headers=headers) 