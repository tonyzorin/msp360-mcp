"""
MSP360/CloudBerry MCP Server - Main Entry Point

This file serves as the main entry point for the MSP360/CloudBerry API MCP Server.
It handles STDIO communication mode only.
"""
import os
import sys
import signal
import logging
import argparse
import asyncio
from typing import Dict, Any

# Set up robust path handling
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)

# Add both the project root and the current directory to sys.path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("msp360_mcp")
logger.info(f"Starting MSP360 MCP Server, Python version: {sys.version}")
logger.info(f"Current directory: {current_dir}")
logger.info(f"Python path: {sys.path}")

# Import FastAPI components (minimal imports for STDIO-only mode)
from fastapi import FastAPI

# Import our components
from core.config import settings
from services.msp360 import msp360_client
from mcp_server import MCPServer
from server.stdio_handler import handle_stdio_mode_async

def handle_stdio_mode():
    """Main entry point for STDIO mode."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(handle_stdio_mode_async())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal, exiting STDIO mode")
    except Exception as e:
        logger.error(f"Error in STDIO mode: {e}", exc_info=True)
    finally:
        loop.close()
    return True

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MSP360 MCP Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Configure debug logging if needed
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Register signal handlers for clean container shutdown.
    # When running as PID 1 inside Docker, SIGTERM is NOT delivered
    # unless the process explicitly registers a handler. Without this,
    # 'docker stop' and MCP server reloads cannot terminate the container.
    def shutdown_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, shutting down")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Only run in STDIO mode
    logger.info("Starting server in STDIO-only mode")
    handle_stdio_mode()
    return

# Entry point for running the server directly
if __name__ == "__main__":
    main() 