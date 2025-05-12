"""Users endpoints for MSP360 MCP Server."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Request
from tools.users import UserTools

router = APIRouter(
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

# New dependency to get tools from app state
def get_user_tools(request: Request) -> UserTools:
    """Get the user tools from the application state."""
    return request.app.state.mcp_server.user_tools

@router.get("/")
async def get_users(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    tools: UserTools = Depends(get_user_tools)
) -> Dict[str, Any]:
    """
    Get a list of users with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **company_id**: Filter by company ID (optional)
    """
    params = UserTools.Params(
        page=page,
        limit=limit,
        company_id=company_id
    )
    
    return await tools.get_users(params=params)

@router.get("/{user_id}")
async def get_user(
    user_id: str = Path(..., description="User ID"),
    tools: UserTools = Depends(get_user_tools)
) -> Dict[str, Any]:
    """
    Get a specific user by ID.
    
    - **user_id**: The ID of the user to retrieve
    """
    result = await tools.get_user(user_id=user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    
    return result 