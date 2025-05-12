from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from services.msp360 import msp360_client

router = APIRouter()

@router.get("/backup-summary")
async def get_backup_summary_report(
    days: int = Query(7, description="Number of days to include in the report"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    include_successful: bool = Query(True, description="Include successful backups"),
    include_warnings: bool = Query(True, description="Include backups with warnings"),
    include_errors: bool = Query(True, description="Include failed backups")
) -> Dict[str, Any]:
    """
    Generate a summary report of backup activities across companies and users.
    """
    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    # Prepare API parameters
    params = {
        "page": 1,
        "limit": 1000,  # Get a large number of records
        "fromDate": from_date.strftime("%Y-%m-%d"),
        "toDate": to_date.strftime("%Y-%m-%d")
    }
    
    if company_id:
        params["companyId"] = company_id
        
    # Get backup history from API
    backup_history = await msp360_client.get_backup_history(params=params)
    
    # Initialize counters
    total_backups = 0
    successful_backups = 0
    warning_backups = 0
    error_backups = 0
    
    # Process backup history
    backup_items = backup_history.get("items", [])
    
    # Count backups by status
    for backup in backup_items:
        status = backup.get("status", "")
        total_backups += 1
        
        if status.lower() == "success":
            successful_backups += 1
        elif status.lower() == "warning":
            warning_backups += 1
        elif status.lower() == "error":
            error_backups += 1
            
    # Prepare the detailed items list based on filters
    detailed_items = []
    for backup in backup_items:
        status = backup.get("status", "").lower()
        
        # Apply filters
        if (status == "success" and include_successful) or \
           (status == "warning" and include_warnings) or \
           (status == "error" and include_errors):
            detailed_items.append(backup)
            
    # Prepare the summary report
    report = {
        "report_period": {
            "from_date": from_date.strftime("%Y-%m-%d"),
            "to_date": to_date.strftime("%Y-%m-%d"),
            "days": days
        },
        "summary": {
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "warning_backups": warning_backups,
            "error_backups": error_backups,
            "success_rate": (successful_backups / total_backups * 100) if total_backups > 0 else 0
        },
        "details": detailed_items
    }
    
    return report

@router.get("/company-usage")
async def get_company_usage_report(
    page: int = Query(1, description="Page number"),
    limit: int = Query(100, description="Number of items per page")
) -> Dict[str, Any]:
    """
    Generate a storage usage report by company.
    """
    # Get companies
    params = {
        "page": page,
        "limit": limit
    }
    companies = await msp360_client.get_companies(params=params)
    
    # Initialize report data
    report_data = {
        "total_companies": companies.get("total", 0),
        "companies": []
    }
    
    # Process each company
    for company in companies.get("items", []):
        company_id = company.get("id", "")
        company_name = company.get("name", "")
        
        # Get users for the company
        user_params = {
            "page": 1,
            "limit": 1000,
            "companyId": company_id
        }
        users = await msp360_client.get_users(params=user_params)
        
        # Get backup plans for the company
        plan_params = {
            "page": 1,
            "limit": 1000,
            "companyId": company_id
        }
        plans = await msp360_client.get_backup_plans(params=plan_params)
        
        # Add company data to report
        company_data = {
            "id": company_id,
            "name": company_name,
            "user_count": users.get("total", 0),
            "backup_plan_count": plans.get("total", 0),
            "users": users.get("items", []),
            "backup_plans": plans.get("items", [])
        }
        
        report_data["companies"].append(company_data)
        
    return report_data 