from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from typing import Dict, Any, Optional, List
import json

from tools.computers import ComputerTools

router = APIRouter(
    tags=["computers"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_computer_tools(request: Request) -> ComputerTools:
    """Get the computer tools from the application state."""
    return request.app.state.mcp_server.computer_tools

@router.get("/")
async def get_computers(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    computer_name: Optional[str] = Query(None, description="Filter by computer name"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    tools: ComputerTools = Depends(get_computer_tools)
) -> Dict[str, Any]:
    """
    Get list of managed computers/endpoints with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **computer_name**: Filter by computer name (optional)
    - **user_id**: Filter by user ID (optional)
    - **company_id**: Filter by company ID (optional)
    """
    params = ComputerTools.ComputerParams(
        offset=(page-1)*limit,  # Convert page to offset
        count=limit,
        computer_name=computer_name,
        user_id=user_id,
        company_id=company_id
    )
    
    return await tools.get_computers(params=params)

@router.get("/{hid}")
async def get_computer(
    hid: str,
    tools: ComputerTools = Depends(get_computer_tools)
) -> Dict[str, Any]:
    """
    Get a specific computer by hardware ID.
    
    - **hid**: Hardware ID of the computer
    """
    return await tools.get_computer(hid=hid)

@router.get("/{hid}/plans")
async def get_computer_plans(
    hid: str,
    tools: ComputerTools = Depends(get_computer_tools)
) -> Dict[str, Any]:
    """
    Get backup/restore plans on a specific computer.
    
    - **hid**: Hardware ID of the computer
    """
    return await tools.get_computer_plans(hid=hid)

@router.delete("/{hid}/authorization")
async def remove_computer_authorization(
    hid: str,
    tools: ComputerTools = Depends(get_computer_tools)
) -> Dict[str, Any]:
    """
    Remove authorization from a computer.
    
    - **hid**: Hardware ID of the computer
    """
    return await tools.remove_computer_authorization(hid=hid)

@router.post("/{hid}/authorization")
async def update_computer_authorization(
    hid: str,
    auth_data: Dict[str, Any] = Body(default={}),
    tools: ComputerTools = Depends(get_computer_tools)
) -> Dict[str, Any]:
    """
    Create/update authorization for a computer.
    
    - **hid**: Hardware ID of the computer
    
    The request body can optionally contain authorization data with UserId and/or CompanyId.
    """
    # Convert dict to JSON string for the tool function
    auth_data_str = json.dumps(auth_data) if auth_data else "{}"
    return await tools.update_computer_authorization(hid=hid, auth_data=auth_data_str) 