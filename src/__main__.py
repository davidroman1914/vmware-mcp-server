"""
Main entry point for ESXi MCP Server.
"""
import asyncio
import logging
import sys
from pathlib import Path

from .config import Config
from .mcp_server import create_server


def setup_logging(config: Config) -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, config.server.log_level.upper())
    
    if config.server.log_file:
        # Create log directory if it doesn't exist
        log_path = Path(config.server.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.server.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


async def main() -> None:
    """Main function."""
    try:
        # Load configuration
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
            config = Config.from_file(config_path)
        else:
            # Try to load from environment variables
            config = Config.from_env()
        
        # Setup logging
        setup_logging(config)
        
        logging.info("Starting ESXi MCP Server")
        
        # Create and run server
        server = await create_server(config)
        
        # Run the server using stdio transport
        from mcp.server.stdio import stdio_server
        try:
            # Try the context manager approach first
            async with stdio_server(server) as stdio:
                await stdio.run()
        except TypeError:
            # Fallback to direct await if context manager doesn't work
            await stdio_server(server)
        
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 