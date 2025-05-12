"""Backup endpoints for MSP360 MCP Server."""
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Request
from tools.backup import BackupTools

router = APIRouter(
    tags=["backup"],
    responses={404: {"description": "Not found"}}
)

# Dependency to get tools from app state
def get_backup_tools(request: Request) -> BackupTools:
    """Get the backup tools from the application state."""
    return request.app.state.mcp_server.backup_tools

@router.get("/monitoring")
async def get_monitoring(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    from_date: Optional[datetime] = Query(None, description="Filter by start date"),
    to_date: Optional[datetime] = Query(None, description="Filter by end date"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get monitoring data for backup/restore plans with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **user_id**: Filter by user ID (optional)
    - **company_id**: Filter by company ID (optional)
    - **from_date**: Filter by start date (optional)
    - **to_date**: Filter by end date (optional)
    - **status**: Filter by status (optional)
    """
    params = BackupTools.MonitoringParams(
        page=page,
        limit=limit,
        user_id=user_id,
        company_id=company_id,
        from_date=from_date,
        to_date=to_date,
        status=status
    )
    
    return await tools.get_monitoring_data(params=params)

@router.get("/monitoring/{item_id}")
async def get_monitoring_item(
    item_id: str = Path(..., description="Monitoring item ID"),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get a specific monitoring item by ID.
    
    - **item_id**: The ID of the monitoring item to retrieve
    """
    return await tools.get_monitoring_item(item_id=item_id)

@router.get("/monitoring/user/{user_id}")
async def get_user_monitoring(
    user_id: str = Path(..., description="User ID"),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get monitoring data for a specific user.
    
    - **user_id**: The ID of the user
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    """
    return await tools.get_user_monitoring(user_id=user_id, page=page, limit=limit)

@router.get("/plans")
async def get_backup_plans(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get a list of backup plans with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **user_id**: Filter by user ID (optional)
    - **company_id**: Filter by company ID (optional)
    """
    params = BackupTools.MonitoringParams(
        page=page,
        limit=limit,
        user_id=user_id,
        company_id=company_id
    )
    
    return await tools.get_backup_plans(params=params)

@router.get("/plans/{plan_id}")
async def get_backup_plan(
    plan_id: str = Path(..., description="Backup plan ID"),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get a specific backup plan by ID.
    
    - **plan_id**: The ID of the backup plan to retrieve
    """
    return await tools.get_monitoring_item(item_id=plan_id)

@router.get("/history")
async def get_backup_history(
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    from_date: Optional[datetime] = Query(None, description="Filter by start date"),
    to_date: Optional[datetime] = Query(None, description="Filter by end date"),
    status: Optional[str] = Query(None, description="Filter by backup status"),
    tools: BackupTools = Depends(get_backup_tools)
) -> Dict[str, Any]:
    """
    Get backup history with optional filtering.
    
    - **page**: Page number starting from 1
    - **limit**: Number of items per page (1-100)
    - **user_id**: Filter by user ID (optional)
    - **company_id**: Filter by company ID (optional)
    - **from_date**: Filter by start date (optional)
    - **to_date**: Filter by end date (optional)
    - **status**: Filter by backup status (optional)
    """
    params = BackupTools.MonitoringParams(
        page=page,
        limit=limit,
        user_id=user_id,
        company_id=company_id,
        from_date=from_date,
        to_date=to_date,
        status=status
    )
    
    return await tools.get_backup_history(params=params) 