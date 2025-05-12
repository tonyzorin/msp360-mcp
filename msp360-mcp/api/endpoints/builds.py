"""Builds endpoints for MSP360 MCP Server."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Body, Request

from tools.builds import BuildsTools

router = APIRouter(
    tags=["builds"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_builds_tools(request: Request) -> BuildsTools:
    """Get the builds tools from the application state."""
    return request.app.state.mcp_server.builds_tools

@router.get("/")
async def get_builds(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    edition: Optional[str] = Query(None, description="Filter by software edition"),
    tools: BuildsTools = Depends(get_builds_tools)
) -> Dict[str, Any]:
    """
    Returns a list of build structures that are available to users.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **edition**: Filter by software edition (optional)
    """
    params = BuildsTools.BuildsParams(
        page=page,
        limit=limit,
        edition=edition
    )
    
    return await tools.get_builds(params=params)

@router.post("/RequestCustomBuilds")
async def request_custom_builds(
    build_data: Dict[str, Any] = Body(...),
    tools: BuildsTools = Depends(get_builds_tools)
) -> Dict[str, Any]:
    """
    Request custom builds with specified editions.
    
    The request body should contain the build specifications.
    """
    return await tools.request_custom_builds(build_data=build_data)

@router.get("/AvailableVersions")
async def get_available_versions(
    tools: BuildsTools = Depends(get_builds_tools)
) -> Dict[str, Any]:
    """
    Returns the latest available versions of build.
    """
    return await tools.get_available_versions() 