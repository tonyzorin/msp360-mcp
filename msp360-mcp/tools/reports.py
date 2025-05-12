"""Reports tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import math
import json
import logging

from services.msp360 import msp360_client

logger = logging.getLogger(__name__)

class ReportTools:
    """Report generation tools for MSP360 API."""
    
    def __init__(self):
        """Initialize the report tools."""
        self.client = msp360_client
        
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Return the tool definitions for report tools."""
        return {
            "get_backup_summary_report": {
                "description": "Generate a summary report of backup activities across companies and users",
                "function": self.get_backup_summary_report,
                "parameter_descriptions": {
                    "days": "Number of days to include in the report (default: 7)",
                    "company_id": "Filter by company ID (optional)",
                    "include_successful": "Include successful backups in the report (default: True)",
                    "include_warnings": "Include backups with warnings in the report (default: True)",
                    "include_errors": "Include failed backups in the report (default: True)"
                }
            },
            "get_company_usage_report": {
                "description": "Generate a storage usage report by company",
                "function": self.get_company_usage_report,
                "parameter_descriptions": {
                    "page": "Page number (default: 1)",
                    "limit": "Number of items per page (default: 100)"
                }
            }
        }
        
    async def get_backup_summary_report(
        self, 
        days: int = 7, 
        include_successful: bool = True,
        include_warnings: bool = True,
        include_errors: bool = True,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a summary report of backup activities.
        
        Args:
            days: Number of days to include in the report
            include_successful: Include successful backups in the report
            include_warnings: Include backups with warnings in the report
            include_errors: Include failed backups in the report
            company_id: Filter by company ID (optional)
            
        Returns:
            Backup summary report
        """
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        # Set up params for API call
        params = {
            "page": 1,
            "limit": 1000,  # Large enough to get all relevant backups
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat()
        }
        
        # Add company filter if provided
        if company_id:
            params["company_id"] = company_id
            
        # Get backup data
        monitoring_data = await self.client.get_monitoring(params=params)
        
        # Initialize report data
        total_backups = 0
        successful_backups = 0
        warning_backups = 0
        failed_backups = 0
        
        # Process monitoring data
        if isinstance(monitoring_data, list):
            backup_items = monitoring_data
        elif isinstance(monitoring_data, dict) and 'items' in monitoring_data:
            backup_items = monitoring_data['items']
        else:
            backup_items = []
            
        # Initialize lists for each category
        successful_list = []
        warning_list = []
        failed_list = []
        
        # Process backup items
        for item in backup_items:
            # Only count backup plans (not restore)
            if item.get('PlanType') in [3, 5, 7, 11, 16]:  # Common backup plan types
                total_backups += 1
                
                # Categorize by status
                status = item.get('Status', -1)
                if status == 0:
                    successful_backups += 1
                    if include_successful:
                        successful_list.append(item)
                elif status in [6, 7]:  # Warning statuses
                    warning_backups += 1
                    if include_warnings:
                        warning_list.append(item)
                elif status in [1, 2, 5]:  # Error statuses
                    failed_backups += 1
                    if include_errors:
                        failed_list.append(item)
                        
        # Format report content
        result_content = []
        
        # Add summary
        success_percentage = (successful_backups / total_backups * 100) if total_backups > 0 else 0
        warning_percentage = (warning_backups / total_backups * 100) if total_backups > 0 else 0
        failed_percentage = (failed_backups / total_backups * 100) if total_backups > 0 else 0
        
        summary_text = f"""
Backup Summary Report for the past {days} days
=============================================
Total backups: {total_backups}
Successful backups: {successful_backups} ({success_percentage:.1f}%)
Backups with warnings: {warning_backups} ({warning_percentage:.1f}%)
Failed backups: {failed_backups} ({failed_percentage:.1f}%)
"""
        result_content.append({
            "type": "text",
            "text": summary_text
        })
        
        # Add detailed sections
        if include_successful and successful_list:
            successful_text = "Successful Backups\n==================\n"
            for item in successful_list:
                successful_text += f"\n- Plan: {item.get('PlanName', 'N/A')}\n"
                successful_text += f"  Computer: {item.get('ComputerName', 'N/A')}\n"
                successful_text += f"  Company: {item.get('CompanyName', 'N/A')}\n"
                successful_text += f"  Last Run: {item.get('LastStart', 'N/A')}\n"
                successful_text += f"  Duration: {item.get('Duration', 'N/A')}\n"
                successful_text += f"  Data Copied: {item.get('DataCopied', 0)} bytes\n"
            
            result_content.append({
                "type": "text",
                "text": successful_text
            })
            
        if include_warnings and warning_list:
            warning_text = "Backups with Warnings\n====================\n"
            for item in warning_list:
                warning_text += f"\n- Plan: {item.get('PlanName', 'N/A')}\n"
                warning_text += f"  Computer: {item.get('ComputerName', 'N/A')}\n"
                warning_text += f"  Company: {item.get('CompanyName', 'N/A')}\n"
                warning_text += f"  Last Run: {item.get('LastStart', 'N/A')}\n"
                warning_text += f"  Duration: {item.get('Duration', 'N/A')}\n"
                
                # Parse error message if it's JSON-formatted
                error_message = item.get('ErrorMessage', 'N/A')
                if isinstance(error_message, str) and error_message.strip().startswith('['):
                    try:
                        # Try to parse it as JSON
                        error_message_list = json.loads(error_message)
                        warning_text += "  Warning details:\n"
                        for err in error_message_list:
                            warning_text += f"    - {err.get('title', 'Unknown')}\n"
                            warning_text += f"      Code: {err.get('code', 'N/A')}\n"
                            warning_text += f"      Detail: {err.get('detail', 'N/A')}\n"
                            warning_text += f"      Priority: {err.get('priority', 'N/A')}\n"
                            if 'kbid' in err and err['kbid']:
                                warning_text += f"      KB Article: {err['kbid']}\n"
                    except json.JSONDecodeError:
                        warning_text += f"  Warning: {error_message}\n"
                else:
                    warning_text += f"  Warning: {error_message}\n"
            
            result_content.append({
                "type": "text",
                "text": warning_text
            })
            
        if include_errors and failed_list:
            error_text = "Failed Backups\n==============\n"
            for item in failed_list:
                error_text += f"\n- Plan: {item.get('PlanName', 'N/A')}\n"
                error_text += f"  Computer: {item.get('ComputerName', 'N/A')}\n"
                error_text += f"  Company: {item.get('CompanyName', 'N/A')}\n"
                error_text += f"  Last Run: {item.get('LastStart', 'N/A')}\n"
                error_text += f"  Duration: {item.get('Duration', 'N/A')}\n"
                
                # Parse error message if it's JSON-formatted
                error_message = item.get('ErrorMessage', 'N/A')
                if isinstance(error_message, str) and error_message.strip().startswith('['):
                    try:
                        # Try to parse it as JSON
                        error_message_list = json.loads(error_message)
                        error_text += "  Error details:\n"
                        for err in error_message_list:
                            error_text += f"    - {err.get('title', 'Unknown')}\n"
                            error_text += f"      Code: {err.get('code', 'N/A')}\n"
                            error_text += f"      Detail: {err.get('detail', 'N/A')}\n"
                            error_text += f"      Priority: {err.get('priority', 'N/A')}\n"
                            if 'kbid' in err and err['kbid']:
                                error_text += f"      KB Article: {err['kbid']}\n"
                    except json.JSONDecodeError:
                        error_text += f"  Error: {error_message}\n"
                else:
                    error_text += f"  Error: {error_message}\n"
            
            result_content.append({
                "type": "text",
                "text": error_text
            })
        
        return {"content": result_content}
        
    async def get_company_usage_report(self, page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Generate a storage usage report by company.
        
        Args:
            page: Page number
            limit: Number of items per page
            
        Returns:
            Storage usage report by company
        """
        logger.info(f"Generating company usage report with page={page}, limit={limit}")
        
        # Get companies
        params = {
            "page": page,
            "limit": limit
        }
        companies = await self.client.get_companies(params=params)
        
        # Initialize report content
        result_content = []
        
        # Add report header
        header_text = "Company Storage Usage Report\n==========================\n"
        result_content.append({
            "type": "text",
            "text": header_text
        })
        
        # Extract the companies list
        if isinstance(companies, list):
            company_items = companies
        elif isinstance(companies, dict) and 'items' in companies:
            company_items = companies.get('items', [])
        else:
            company_items = []
            
        # Log raw result
        logger.debug(f"Raw API response contains {len(company_items)} companies")
            
        # Apply limit to the company list before processing
        if limit and limit > 0 and len(company_items) > limit:
            company_items = company_items[:limit]
            logger.info(f"Limited companies to process to {len(company_items)}")
        
        # Initialize counters
        total_users = 0
        total_storage = 0
        companies_processed = 0
        
        # Process only the limited set of companies
        for company in company_items:
            company_id = company.get("Id", "")
            company_name = company.get("Name", "")
            
            try:
                # Get company details including users and storage info
                company_details = await self.client.get_company(company_id)
                companies_processed += 1
                
                if not company_details:
                    logger.warning(f"No details found for company {company_name} ({company_id})")
                    continue
                
                company_text = f"\nCompany: {company_name}\nID: {company_id}\n"
                
                # Extract users data
                users = []
                storage_usage = 0
                
                if 'Users' in company_details and isinstance(company_details['Users'], list):
                    users = company_details['Users']
                    
                # Count total users across all companies
                total_users += len(users)
                
                # Extract storage usage
                if 'TotalStorage' in company_details:
                    storage_usage = company_details.get('TotalStorage', 0)
                    
                    # Add to total storage
                    if isinstance(storage_usage, (int, float)):
                        total_storage += storage_usage
                
                company_text += f"Users: {len(users)}\n"
                company_text += f"Storage Usage: {storage_usage} bytes ({self._format_size(storage_usage)})\n"
                
                if users:
                    company_text += "\nUsers:\n"
                    
                    for user in users:
                        user_name = user.get('Name', 'N/A')
                        user_storage = user.get('Storage', 0)
                        company_text += f"- {user_name}: {user_storage} bytes ({self._format_size(user_storage)})\n"
                
                result_content.append({
                    "type": "text",
                    "text": company_text
                })
                
            except Exception as e:
                logger.error(f"Error processing company {company_name} ({company_id}): {str(e)}")
                result_content.append({
                    "type": "text",
                    "text": f"\nError processing company {company_name} ({company_id}): {str(e)}"
                })
        
        # Add summary with explicit string values to ensure consistency
        summary_text = "\nSummary\n=======\n"
        summary_text += f"Companies Processed: {str(companies_processed)}\n"
        summary_text += f"Total Users: {str(total_users)}\n"
        summary_text += f"Total Storage Usage: {str(total_storage)} bytes ({self._format_size(total_storage)})"
        
        logger.info(f"Company usage report generated, processed {companies_processed} companies, found {total_users} users, total storage {total_storage} bytes")
        logger.info(f"Summary text: {summary_text}")
        
        result_content.append({
            "type": "text",
            "text": summary_text
        })
        
        # Debug log the actual content being returned
        logger.info(f"Returning report content with {len(result_content)} items")
        for idx, item in enumerate(result_content):
            logger.info(f"Item {idx}: {item.get('text', '')[:50]}...")
        
        return {"content": result_content}
        
    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human-readable size string
        """
        if size_bytes == 0:
            return "0 B"
            
        size_names = ("B", "KB", "MB", "GB", "TB", "PB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
        
    def close(self) -> None:
        """Close any resources."""
        pass 