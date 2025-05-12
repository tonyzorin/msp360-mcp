"""Billing endpoints for MSP360 MCP Server."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Body, Request
from datetime import datetime

from tools.billing import BillingTools

router = APIRouter(
    tags=["billing"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_billing_tools(request: Request) -> BillingTools:
    """Get the billing tools from the application state."""
    return request.app.state.mcp_server.billing_tools

@router.get("/")
async def get_billing(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    tools: BillingTools = Depends(get_billing_tools)
) -> Dict[str, Any]:
    """
    Get billing information for the current month.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    """
    params = BillingTools.BillingParams(
        page=page,
        limit=limit
    )
    
    return await tools.get_billing(params=params)

@router.put("/")
async def get_filtered_billing(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    from_date: Optional[datetime] = Query(None, description="Filter by start date"),
    to_date: Optional[datetime] = Query(None, description="Filter by end date"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    tools: BillingTools = Depends(get_billing_tools)
) -> Dict[str, Any]:
    """
    Get filtered billing records.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **from_date**: Filter by start date (optional)
    - **to_date**: Filter by end date (optional)
    - **company_id**: Filter by company ID (optional)
    - **user_id**: Filter by user ID (optional)
    """
    params = BillingTools.BillingParams(
        page=page,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        company_id=company_id,
        user_id=user_id
    )
    
    return await tools.get_filtered_billing(params=params)

@router.put("/Details")
async def get_billing_details(
    details_data: Dict[str, Any] = Body(...),
    tools: BillingTools = Depends(get_billing_tools)
) -> Dict[str, Any]:
    """
    Get detailed billing information for backup/restore operations.
    
    The request body should contain the filters for the billing details.
    """
    return await tools.get_billing_details(details_data=details_data) 