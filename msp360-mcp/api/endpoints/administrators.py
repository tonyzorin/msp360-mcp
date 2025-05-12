"""API endpoints for MSP360 Administrators."""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from services.msp360 import msp360_client
from pydantic import BaseModel
import logging

logger = logging.getLogger("msp360_mcp.api.administrators")

router = APIRouter(
    prefix="/administrators",
    tags=["administrators"],
    responses={404: {"description": "Not found"}},
)

class AdminCreate(BaseModel):
    """Model for creating a new administrator."""
    Name: str
    Email: str
    Password: str
    Role: int
    CompanyID: Optional[str] = None
    Enabled: Optional[bool] = True

class AdminUpdate(BaseModel):
    """Model for updating an administrator."""
    ID: str
    Name: Optional[str] = None
    Email: Optional[str] = None
    Password: Optional[str] = None
    Role: Optional[int] = None
    CompanyID: Optional[str] = None
    Enabled: Optional[bool] = None

@router.get("/")
async def get_administrators(
    skip: int = Query(0, description="Number of records to skip"),
    take: int = Query(10, description="Number of records to take"),
    name: Optional[str] = Query(None, description="Filter by administrator name")
):
    """
    Get a list of administrators with optional filtering.
    """
    try:
        params = {}
        
        # Add pagination parameters
        params["skip"] = skip
        params["take"] = take
        
        # Add filter parameters if provided
        if name:
            params["name"] = name
        
        return await msp360_client.get_administrators(params=params)
    except Exception as e:
        logger.error(f"Error retrieving administrators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{admin_id}")
async def get_administrator(admin_id: str):
    """
    Get a specific administrator by ID.
    """
    try:
        return await msp360_client.get_administrator(admin_id=admin_id)
    except Exception as e:
        logger.error(f"Error retrieving administrator {admin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_administrator(admin: AdminCreate):
    """
    Create a new administrator.
    """
    try:
        return await msp360_client.create_administrator(admin.dict())
    except Exception as e:
        logger.error(f"Error creating administrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/")
async def update_administrator(admin: AdminUpdate):
    """
    Update an existing administrator.
    """
    try:
        return await msp360_client.update_administrator(admin.dict())
    except Exception as e:
        logger.error(f"Error updating administrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{admin_id}")
async def delete_administrator(admin_id: str):
    """
    Delete an administrator by ID.
    """
    try:
        return await msp360_client.delete_administrator(admin_id=admin_id)
    except Exception as e:
        logger.error(f"Error deleting administrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 