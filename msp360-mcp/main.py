"""
MSP360 MCP Server v2 — FastMCP entry point.

Default transport: STDIO (Cursor, Claude Desktop).
Optional: MCP_TRANSPORT=http for Streamable HTTP remote access.
"""
import argparse
import logging
import os
import signal
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("msp360_mcp")

from server.fastmcp_app import SERVER_VERSION, create_mcp_server  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="MSP360 MCP Server v2")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=None,
        help="MCP transport (default: stdio, or MCP_TRANSPORT env)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="HTTP host (default from HOST env or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP port (default from PORT env or 51817)",
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    def shutdown_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info("Received %s, shutting down", sig_name)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    mcp = create_mcp_server()
    transport = args.transport or os.getenv("MCP_TRANSPORT", "stdio")

    logger.info("Starting MSP360 MCP v%s (%s)", SERVER_VERSION, transport)

    if transport == "http":
        from core.config import settings

        host = args.host or settings.HOST
        port = args.port or settings.PORT
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
