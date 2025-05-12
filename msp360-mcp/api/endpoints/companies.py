"""Companies endpoints for MSP360 MCP Server."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from typing import Dict, Any, Optional, List

from tools.companies import CompanyTools

router = APIRouter(
    tags=["companies"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_company_tools(request: Request) -> CompanyTools:
    """Get the company tools from the application state."""
    return request.app.state.mcp_server.company_tools

@router.get("/")
async def get_companies(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    name: Optional[str] = Query(None, description="Filter by company name"),
    tools: CompanyTools = Depends(get_company_tools)
) -> Dict[str, Any]:
    """
    Get a list of companies with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **name**: Filter by company name (optional)
    """
    params = CompanyTools.CompanyParams(
        page=page,
        limit=limit,
        name=name
    )
    
    return await tools.get_companies(params=params)

@router.get("/{company_id}")
async def get_company(
    company_id: str = Path(..., description="Company ID"),
    tools: CompanyTools = Depends(get_company_tools)
) -> Dict[str, Any]:
    """
    Get a specific company by ID.
    
    - **company_id**: The ID of the company to retrieve
    """
    return await tools.get_company(company_id=company_id) 