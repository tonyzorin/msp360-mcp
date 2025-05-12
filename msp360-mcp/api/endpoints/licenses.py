"""Licenses endpoints for MSP360 MCP Server."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, Request

from tools.licenses import LicensesTools

router = APIRouter(
    tags=["licenses"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_licenses_tools(request: Request) -> LicensesTools:
    """Get the licenses tools from the application state."""
    return request.app.state.mcp_server.licenses_tools

@router.get("/")
async def get_licenses(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    edition: Optional[str] = Query(None, description="Filter by software edition"),
    license_type: Optional[str] = Query(None, description="Filter by license type"),
    status: Optional[str] = Query(None, description="Filter by license status"),
    tools: LicensesTools = Depends(get_licenses_tools)
) -> Dict[str, Any]:
    """
    Get a list of licenses with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **user_id**: Filter by user ID (optional)
    - **company_id**: Filter by company ID (optional)
    - **edition**: Filter by software edition (optional)
    - **license_type**: Filter by license type (optional)
    - **status**: Filter by license status (optional)
    """
    params = LicensesTools.LicenseParams(
        page=page,
        limit=limit,
        user_id=user_id,
        company_id=company_id,
        edition=edition,
        license_type=license_type,
        status=status
    )
    
    return await tools.get_licenses(params=params)

@router.get("/{license_id}")
async def get_license(
    license_id: str = Path(..., description="License ID"),
    tools: LicensesTools = Depends(get_licenses_tools)
) -> Dict[str, Any]:
    """
    Get a specific license by ID.
    
    - **license_id**: The ID of the license to retrieve
    """
    return await tools.get_license(license_id=license_id)

@router.post("/Grant")
async def grant_license(
    license_data: Dict[str, Any] = Body(...),
    tools: LicensesTools = Depends(get_licenses_tools)
) -> Dict[str, Any]:
    """
    Grant a license to a user.
    
    The request body should contain the license and user information.
    """
    return await tools.grant_license(license_data=license_data)

@router.post("/Release")
async def release_license(
    license_data: Dict[str, Any] = Body(...),
    tools: LicensesTools = Depends(get_licenses_tools)
) -> Dict[str, Any]:
    """
    Release a license from a user.
    
    The request body should contain the license information.
    """
    return await tools.release_license(license_data=license_data)

@router.post("/Revoke")
async def revoke_license(
    license_data: Dict[str, Any] = Body(...),
    tools: LicensesTools = Depends(get_licenses_tools)
) -> Dict[str, Any]:
    """
    Revoke a license from a user.
    
    The request body should contain the license information.
    """
    return await tools.revoke_license(license_data=license_data) 