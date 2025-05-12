"""Packages endpoints for MSP360 MCP Server."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Request
from tools.packages import PackageTools

router = APIRouter(
    tags=["packages"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_package_tools(request: Request) -> PackageTools:
    """Get the package tools from the application state."""
    return request.app.state.mcp_server.package_tools

@router.get("/")
async def get_packages(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter by package name"),
    tools: PackageTools = Depends(get_package_tools)
) -> Dict[str, Any]:
    """
    Get a list of packages with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **name**: Filter by package name (optional)
    """
    params = PackageTools.PackageParams(
        page=page,
        limit=limit,
        name=name
    )
    
    return await tools.get_packages(params=params)

@router.get("/{package_id}")
async def get_package(
    package_id: str = Path(..., description="Package ID"),
    tools: PackageTools = Depends(get_package_tools)
) -> Dict[str, Any]:
    """
    Get a specific package by ID.
    
    - **package_id**: The ID of the package to retrieve
    """
    result = await tools.get_package(package_id=package_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Package with ID {package_id} not found")
    
    return result 