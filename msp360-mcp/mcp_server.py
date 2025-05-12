"""MSP360 MCP Server implementation."""
from typing import Dict, Any, Callable, Optional
import inspect
import logging

# Import tools from new module structure
from tools.users import UserTools
from tools.companies import CompanyTools
from tools.packages import PackageTools
from tools.backup import BackupTools
from tools.reports import ReportTools
from tools.accounts import AccountTools
from tools.destinations import DestinationTools
from tools.computers import ComputerTools
from tools.billing import BillingTools
from tools.builds import BuildsTools
from tools.licenses import LicensesTools
from tools.admin import AdminTools

# Configure logging
logger = logging.getLogger("msp360_mcp.server")

class MCPServer:
    """MSP360 MCP Server."""
    
    def __init__(self):
        """Initialize the MCP server."""
        
        # Explicitly re-import the client after all tool modules are loaded
        # This might help ensure the client instance reflects the full class definition
        from services.msp360 import msp360_client
        
        self.user_tools = UserTools()
        self.company_tools = CompanyTools()
        self.package_tools = PackageTools()
        self.backup_tools = BackupTools()
        self.report_tools = ReportTools()
        self.account_tools = AccountTools()
        self.destination_tools = DestinationTools()
        self.computer_tools = ComputerTools()
        self.billing_tools = BillingTools()
        self.build_tools = BuildsTools()
        self.license_tools = LicensesTools()
        self.admin_tools = AdminTools()
        self.registered_tools = {}
        logger.info("MSP360 MCP Server initialized")
        
    def register_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        parameter_descriptions: Optional[Dict[str, str]] = None,
        streaming: bool = False
    ) -> None:
        """Register a tool with the MCP server.
        
        Args:
            name: The name of the tool
            description: The description of the tool
            function: The function that implements the tool
            parameter_descriptions: Descriptions of the function parameters
            streaming: Whether the tool supports streaming responses
        """
        if name in self.registered_tools:
            logger.warning(f"Tool {name} already registered, will be overwritten")
            
        # Get the function signature to determine parameters
        sig = inspect.signature(function)
        parameters = []
        
        # Skip 'self' parameter for instance methods
        param_items = list(sig.parameters.items())
        if param_items and param_items[0][0] == 'self':
            param_items = param_items[1:]
            
        for param_name, param in param_items:
            # Determine if the parameter is required based on whether it has a default value
            required = param.default == inspect.Parameter.empty
            
            # Determine parameter type
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                # Check for specific parameter names that should always be integers
                if param_name in ["limit", "page"] or param.annotation == int or (hasattr(param.annotation, "__origin__") and param.annotation.__origin__ == Optional and param.annotation.__args__[0] == int):
                    param_type = "integer"
                elif param.annotation == bool or (hasattr(param.annotation, "__origin__") and param.annotation.__origin__ == Optional and param.annotation.__args__[0] == bool):
                    param_type = "boolean"
            
            # Get the parameter description if available
            param_description = parameter_descriptions.get(param_name, f"{param_name} parameter") if parameter_descriptions else f"{param_name} parameter"
            
            # Create parameter definition (simplified for direct use)
            parameter_schema = {
                "description": param_description,
                "type": param_type
            }
            if not required and param.default is not None:
                parameter_schema["default"] = param.default

            parameters.append({
                "name": param_name,
                "schema": parameter_schema,
                "required": required
            })

        # Construct the inputSchema object following JSON Schema structure
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        for param_info in parameters:
            input_schema["properties"][param_info["name"]] = param_info["schema"]
            if param_info["required"]:
                input_schema["required"].append(param_info["name"])

        # Ensure 'required' list is not empty if there are required properties
        if not input_schema["required"]:
            del input_schema["required"]

        self.registered_tools[name] = {
            "description": description,
            "function": function,
            "inputSchema": input_schema,  # Store the schema object
            "streaming": streaming  # Add streaming flag
        }
        
        logger.info(f"Registered tool: {name} (streaming: {streaming})")
        # Add debug logging for the schema
        logger.debug(f"Registered tool '{name}' with schema: {input_schema}")
    
    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a registered tool with the given parameters.
        
        Args:
            tool_name: The name of the tool to invoke
            parameters: The parameters to pass to the tool
            
        Returns:
            The result of the tool invocation
            
        Raises:
            KeyError: If the tool is not registered
        """
        if tool_name not in self.registered_tools:
            error_message = f"Tool '{tool_name}' not registered"
            logger.error(error_message)
            return {"error": error_message, "content": []}
        
        tool = self.registered_tools[tool_name]
        function = tool["function"]
        
        try:
            logger.info(f"Invoking tool '{tool_name}' with parameters: {parameters}")
            result = await function(**parameters)
            return result
        except Exception as e:
            error_message = f"Error invoking tool '{tool_name}': {str(e)}"
            logger.error(error_message)
            return {"error": error_message, "content": []}
        
    def register_tools(self) -> None:
        """Register all MCP tools."""
        logger.info("Starting tool registration")
        
        # Register user tools
        user_tool_definitions = self.user_tools.get_tool_definitions()
        logger.info(f"Found {len(user_tool_definitions)} user tools")
        for tool_name, tool_config in user_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register company tools
        company_tool_definitions = self.company_tools.get_tool_definitions()
        logger.info(f"Found {len(company_tool_definitions)} company tools")
        for tool_name, tool_config in company_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register package tools
        package_tool_definitions = self.package_tools.get_tool_definitions()
        logger.info(f"Found {len(package_tool_definitions)} package tools")
        for tool_name, tool_config in package_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register backup tools
        backup_tool_definitions = self.backup_tools.get_tool_definitions()
        logger.info(f"Found {len(backup_tool_definitions)} backup tools")
        for tool_name, tool_config in backup_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register report tools
        report_tool_definitions = self.report_tools.get_tool_definitions()
        logger.info(f"Found {len(report_tool_definitions)} report tools")
        for tool_name, tool_config in report_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register account tools
        account_tool_definitions = self.account_tools.get_tool_definitions()
        logger.info(f"Found {len(account_tool_definitions)} account tools")
        for tool_name, tool_config in account_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register destination tools
        destination_tool_definitions = self.destination_tools.get_tool_definitions()
        logger.info(f"Found {len(destination_tool_definitions)} destination tools")
        for tool_name, tool_config in destination_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register computer tools
        computer_tool_definitions = self.computer_tools.get_tool_definitions()
        logger.info(f"Found {len(computer_tool_definitions)} computer tools")
        for tool_name, tool_config in computer_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register billing tools
        billing_tool_definitions = self.billing_tools.get_tool_definitions()
        logger.info(f"Found {len(billing_tool_definitions)} billing tools")
        for tool_name, tool_config in billing_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register build tools
        build_tool_definitions = self.build_tools.get_tool_definitions()
        logger.info(f"Found {len(build_tool_definitions)} build tools")
        for tool_name, tool_config in build_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register license tools
        license_tool_definitions = self.license_tools.get_tool_definitions()
        logger.info(f"Found {len(license_tool_definitions)} license tools")
        for tool_name, tool_config in license_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        # Register admin tools
        admin_tool_definitions = self.admin_tools.get_tool_definitions()
        logger.info(f"Found {len(admin_tool_definitions)} admin tools")
        for tool_name, tool_config in admin_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
                streaming=tool_config.get("streaming", False)
            )
            
        logger.info(f"Registered {len(self.registered_tools)} tools in total")
            
    def get_tools_definition(self) -> list[dict[str, Any]]:
        """
        Get the list of tools in a format suitable for MCP.
        
        Returns:
            List of tool definitions in MCP format
        """
        tool_definitions = []
        
        for tool_name, tool_info in self.registered_tools.items():
            tool_definition = {
                "name": tool_name,
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            }
            tool_definitions.append(tool_definition)
            
        return tool_definitions
    
    def close(self) -> None:
        """Close the MCP server and release any resources."""
        logger.info("Closing MSP360 MCP Server")
        
        # Close all tool instances
        self.user_tools.close()
        self.company_tools.close()
        self.package_tools.close()
        self.backup_tools.close()
        self.report_tools.close()
        self.account_tools.close()
        self.destination_tools.close()
        self.computer_tools.close()
        self.billing_tools.close()
        self.build_tools.close()
        self.license_tools.close()
        self.admin_tools.close() 