"""Billing tools for MSP360 MCP Server."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
from services.msp360 import msp360_client
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from tools import register_tool

logger = logging.getLogger("msp360_mcp.tools")

class BillingTools:
    """Tools for interacting with MSP360/CloudBerry billing data."""
    
    class BillingParams(BaseModel):
        """Parameters model for filtering billing data."""
        page: Optional[int] = Field(1, description="Page number starting from 1")
        limit: Optional[int] = Field(10, description="Number of items per page")
        from_date: Optional[datetime] = Field(None, description="Filter by start date")
        to_date: Optional[datetime] = Field(None, description="Filter by end date")
        company_id: Optional[str] = Field(None, description="Filter by company ID")
        user_id: Optional[str] = Field(None, description="Filter by user ID")
    
    def __init__(self):
        """Initialize the billing tools."""
        self.client = msp360_client
        self._tool_definitions = {}
        self._register_tools()
        
    def _register_tools(self):
        """Define all billing tools but don't register them globally."""
        self._tool_definitions["get_billing"] = {
            "description": "Get billing information for the current month",
            "function": self.get_billing,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters"
            }
        }
        
        self._tool_definitions["get_filtered_billing"] = {
            "description": "Get filtered billing records",
            "function": self.get_filtered_billing,
            "parameter_descriptions": {
                "params": "JSON string with filter parameters"
            }
        }
        
        self._tool_definitions["get_billing_details"] = {
            "description": "Get detailed billing information for backup/restore operations",
            "function": self.get_billing_details,
            "parameter_descriptions": {
                "details_data": "JSON data with billing detail filters"
            }
        }
            
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get definitions of all billing tools.
        
        Returns:
            Dictionary of tool definitions
        """
        return self._tool_definitions
        
    async def get_billing(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get billing information for the current month.
        
        Args:
            params: Filter parameters as a JSON string
            
        Returns:
            Dictionary with billing data
        """
        logger.info(f"Getting billing information with params: {params}")
        
        # Parse the JSON string to get parameters
        try:
            if params and params.strip():
                param_dict = json.loads(params)
            else:
                param_dict = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            return {"content": [], "error": f"Invalid JSON parameters: {str(e)}"}
        
        query_params = {}
        
        # Add pagination
        page = param_dict.get('page', 1)
        limit = param_dict.get('limit', None)
        
        # Add any additional filters
        if 'company_id' in param_dict:
            query_params['companyId'] = param_dict['company_id']
        
        try:
            # Call the API
            billing_data = await self.client.get_billing(params=query_params)
            
            if not billing_data:
                return {"content": [{"type": "text", "text": "No billing data found"}]}
            
            # Format the response for MCP
            result_content = []
            
            # Process general billing information
            if isinstance(billing_data, dict):
                # Add summary information
                summary_info = []
                
                if 'CurrentSpaceUsed' in billing_data:
                    current_space = self._format_bytes(billing_data['CurrentSpaceUsed'])
                    summary_info.append(f"Current Space Used: {current_space}")
                    
                if 'AverageSpaceUsed' in billing_data:
                    avg_space = self._format_bytes(billing_data['AverageSpaceUsed'])
                    summary_info.append(f"Average Space Used: {avg_space}")
                    
                if 'TotalRestore' in billing_data:
                    total_restore = self._format_bytes(billing_data['TotalRestore'])
                    summary_info.append(f"Total Restore: {total_restore}")
                    
                if summary_info:
                    result_content.append({
                        "type": "text",
                        "text": "\n".join(summary_info)
                    })
                
                # Process user billing statistics
                if 'StatisticBilling' in billing_data and isinstance(billing_data['StatisticBilling'], list):
                    stats = billing_data['StatisticBilling']
                    
                    # Apply limit if specified
                    if limit is not None and isinstance(limit, int) and limit > 0:
                        stats = stats[:limit]
                    
                    for user_stat in stats:
                        user_info = []
                        
                        # User identification
                        email = user_stat.get('Email', 'N/A')
                        user_id = user_stat.get('UserId', 'N/A')
                        user_info.append(f"User: {email}")
                        user_info.append(f"User ID: {user_id}")
                        
                        # User details
                        if user_stat.get('FirstName') or user_stat.get('LastName'):
                            name_parts = []
                            if user_stat.get('FirstName'):
                                name_parts.append(user_stat['FirstName'])
                            if user_stat.get('LastName'):
                                name_parts.append(user_stat['LastName'])
                            name = " ".join(name_parts)
                            if name:
                                user_info.append(f"Name: {name}")
                        
                        # Company info
                        if user_stat.get('CompanyName'):
                            user_info.append(f"Company: {user_stat['CompanyName']}")
                        
                        # Usage statistics
                        avg_space = self._format_bytes(user_stat.get('AverageSpace', 0))
                        user_info.append(f"Average Space: {avg_space}")
                        
                        restore_volume = self._format_bytes(user_stat.get('TotalVolumeRestore', 0))
                        user_info.append(f"Total Restore Volume: {restore_volume}")
                        
                        # Cost information
                        plan_cost = f"${user_stat.get('PlanCost', 0):.2f}"
                        user_info.append(f"Plan Cost: {plan_cost}")
                        
                        storage_cost = f"${user_stat.get('StorageCost', 0):.4f}"
                        user_info.append(f"Storage Cost: {storage_cost}")
                        
                        restore_cost = f"${user_stat.get('RestoreCost', 0):.4f}"
                        user_info.append(f"Restore Cost: {restore_cost}")
                        
                        total_cost = f"${user_stat.get('TotalCost', 0):.4f}"
                        user_info.append(f"Total Cost: {total_cost}")
                        
                        # Add the formatted user billing info to the results
                        result_content.append({
                            "type": "text",
                            "text": "\n".join(user_info)
                        })
            else:
                # For unexpected response formats
                result_content.append({
                    "type": "text",
                    "text": f"Billing data: {json.dumps(billing_data, indent=2)}"
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving billing information: {str(e)}")
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error retrieving billing information: {str(e)}"
                }],
                "error": f"Failed to retrieve billing information: {str(e)}"
            }
            
    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes into a human-readable string."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
            
    async def get_filtered_billing(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get filtered billing records.
        
        Args:
            params: Filter parameters as a JSON string
            
        Returns:
            Dictionary with filtered billing data
        """
        logger.info(f"Getting filtered billing with params: {params}")
        
        # Parse the JSON string to get parameters
        try:
            if params and params.strip():
                param_dict = json.loads(params)
            else:
                param_dict = {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing parameters JSON: {str(e)}")
            return {"content": [], "error": f"Invalid JSON parameters: {str(e)}"}
        
        filter_data = {}
        
        # Add pagination
        page = param_dict.get('page', 1)
        limit = param_dict.get('limit', 10)
        
        # Add pagination
        if page:
            filter_data["skip"] = (page - 1) * limit if limit else 0
        
        if limit:
            filter_data["take"] = limit
            
        # Add filters
        from_date = param_dict.get('from_date')
        if from_date:
            if isinstance(from_date, datetime):
                filter_data["fromDate"] = from_date.isoformat()
            else:
                filter_data["fromDate"] = from_date
            
        to_date = param_dict.get('to_date')
        if to_date:
            if isinstance(to_date, datetime):
                filter_data["toDate"] = to_date.isoformat()
            else:
                filter_data["toDate"] = to_date
            
        company_id = param_dict.get('company_id')
        if company_id:
            filter_data["companyId"] = company_id
            
        user_id = param_dict.get('user_id')
        if user_id:
            filter_data["userId"] = user_id
        
        try:
            # Call the API
            billing_data = await self.client.get_filtered_billing(filter_data=filter_data)
            logger.debug(f"Filtered billing data type: {type(billing_data)}")
            
            # Process filtered billing data for MCP format
            result_content = []
            
            # Extract billing records
            billing_records = []
            
            if isinstance(billing_data, list):
                # Direct list of billing records
                billing_records = billing_data
            elif isinstance(billing_data, dict):
                # Dictionary with items or content field
                if 'items' in billing_data and isinstance(billing_data['items'], list):
                    billing_records = billing_data['items']
                elif 'content' in billing_data and isinstance(billing_data['content'], list):
                    billing_records = billing_data['content']
                elif 'Records' in billing_data and isinstance(billing_data['Records'], list):
                    billing_records = billing_data['Records']
            
            logger.info(f"Retrieved {len(billing_records)} filtered billing records")
            
            # Format each billing record as text
            for record in billing_records:
                # Convert record to MCP-compatible text item
                formatted_text = "\n".join([f"{key}: {value}" for key, value in record.items()])
                result_content.append({
                    "type": "text",
                    "text": formatted_text
                })
            
            # If no records were processed but the response seems valid, include a summary
            if not result_content and billing_data:
                summary_text = f"Filtered billing summary: {json.dumps(billing_data)}"
                result_content.append({
                    "type": "text",
                    "text": summary_text
                })
            
            return {"content": result_content}
        except Exception as e:
            logger.error(f"Error retrieving filtered billing data: {str(e)}")
            return {"content": [], "error": str(e)}
            
    async def get_billing_details(self, details_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed billing information for backup/restore operations.
        
        Args:
            details_data: JSON data with billing detail filters
            
        Returns:
            Dictionary with billing details
        """
        logger.info(f"Getting billing details with data: {details_data}")
        
        try:
            return await self.client.get_billing_details(details_data=details_data)
        except Exception as e:
            logger.error(f"Error retrieving billing details: {str(e)}")
            raise
            
    async def get_billing_pdf(self, params: str = '{}') -> Dict[str, Any]:
        """
        Get billing information as a PDF report.
        
        Args:
            params: Filter parameters as a JSON string
            
        Returns:
            Dictionary with PDF data or an error message
        """
        logger.info(f"Generating billing PDF with params: {params}")
        
        try:
            # First get the billing data using the existing method
            billing_data_response = await self.get_billing(params)
            
            if 'error' in billing_data_response:
                return billing_data_response
            
            # Check if we have content to convert to PDF
            content_items = billing_data_response.get('content', [])
            if not content_items:
                return {
                    "content": [{
                        "type": "text",
                        "text": "No billing data available to generate PDF"
                    }],
                    "error": "No billing data available"
                }
            
            # Install required packages if not already installed
            try:
                import reportlab
            except ImportError:
                logger.info("Installing reportlab package for PDF generation")
                import subprocess
                subprocess.check_call(["pip", "install", "reportlab"])
                
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from io import BytesIO
            import base64
            from datetime import datetime
            
            # Create a BytesIO buffer to store the PDF
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter,
                title="MSP360 Billing Report",
                author="MSP360 MCP Server"
            )
            
            # Get the styles
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Create a list to hold the document elements
            elements = []
            
            # Add title and date
            elements.append(Paragraph("MSP360 Billing Report", title_style))
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            elements.append(Spacer(1, 12))
            
            # Extract text content from each content item
            for item in content_items:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    if text:
                        # For items that look like billing summaries (first item)
                        if "Space Used" in text:
                            elements.append(Paragraph("Billing Summary", heading_style))
                            for line in text.split('\n'):
                                elements.append(Paragraph(line, normal_style))
                            elements.append(Spacer(1, 12))
                        # For user billing records
                        elif text.startswith("User:"):
                            # Process individual user billing records
                            user_data = {}
                            for line in text.split('\n'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    user_data[key.strip()] = value.strip()
                            
                            # Add user header
                            user_name = user_data.get("User", "Unknown User")
                            elements.append(Paragraph(f"Billing for: {user_name}", heading_style))
                            
                            # Create a table of key-value pairs for user data
                            data = []
                            for key, value in user_data.items():
                                data.append([key, value])
                            
                            # Create table
                            if data:
                                table = Table(data, colWidths=[150, 350])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ]))
                                elements.append(table)
                                elements.append(Spacer(1, 12))
            
            # Build the PDF document
            doc.build(elements)
            
            # Get the PDF data from the buffer
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Encode as base64 for return
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Return the PDF data
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "MSP360 Billing Report generated successfully."
                    },
                    {
                        "type": "base64_pdf",
                        "data": pdf_base64,
                        "filename": f"msp360_billing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error generating billing PDF: {str(e)}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error generating billing PDF: {str(e)}"
                }],
                "error": f"Failed to generate billing PDF: {str(e)}"
            }
            
    def close(self) -> None:
        """Close any resources."""
        pass 