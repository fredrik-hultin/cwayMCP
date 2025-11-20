#!/usr/bin/env python3
"""
Standalone script to run the Cway REST API server.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from config.settings import settings


def main():
    """Run the REST API server."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Cway REST API server...")
    logger.info(f"API Documentation: http://{settings.mcp_server_host}:{settings.mcp_server_port}/docs")
    logger.info(f"OpenAPI Spec: http://{settings.mcp_server_host}:{settings.mcp_server_port}/openapi.json")
    
    # Run uvicorn server
    uvicorn.run(
        "src.presentation.rest_api:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
