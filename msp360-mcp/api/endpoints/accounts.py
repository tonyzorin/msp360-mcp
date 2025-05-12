from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from typing import Dict, Any, Optional, List

from tools.accounts import AccountTools

router = APIRouter(
    tags=["accounts"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_account_tools(request: Request) -> AccountTools:
    """Get the account tools from the application state."""
    return request.app.state.mcp_server.account_tools

@router.get("/")
async def get_accounts(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter by account name"),
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Get list of accounts with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **name**: Filter by account name (optional)
    """
    params = AccountTools.AccountParams(
        page=page,
        limit=limit,
        name=name
    )
    
    return await tools.get_accounts(params=params)

@router.get("/{account_id}")
async def get_account(
    account_id: str, 
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Get a specific account by ID.
    
    - **account_id**: The ID of the account to retrieve
    """
    return await tools.get_account(account_id=account_id)

@router.post("/")
async def create_account(
    account_data: Dict[str, Any] = Body(...),
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Create a new account.
    
    The request body should contain the account data.
    """
    return await tools.create_account(account_data=account_data)

@router.put("/")
async def update_account(
    account_data: Dict[str, Any] = Body(...),
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Update an existing account.
    
    The request body should contain the account data.
    """
    return await tools.update_account(account_data=account_data)

@router.get("/destinations/{user_email}")
async def get_user_destinations(
    user_email: str,
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Get destinations of a specific user.
    
    - **user_email**: The email of the user
    """
    return await tools.get_user_destinations(user_email=user_email)

@router.post("/destinations")
async def add_user_destination(
    destination_data: Dict[str, Any] = Body(...),
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Add a destination to a user.
    
    The request body should contain the destination data.
    """
    return await tools.add_user_destination(destination_data=destination_data)

@router.put("/destinations")
async def edit_user_destination(
    destination_data: Dict[str, Any] = Body(...),
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Edit a destination of a user.
    
    The request body should contain the destination data.
    """
    return await tools.edit_user_destination(destination_data=destination_data)

@router.delete("/destinations/{destination_id}")
async def delete_user_destination(
    destination_id: str,
    tools: AccountTools = Depends(get_account_tools)
) -> Dict[str, Any]:
    """
    Delete a destination of a user.
    
    - **destination_id**: The ID of the destination to delete
    """
    return await tools.delete_user_destination(destination_id=destination_id) 