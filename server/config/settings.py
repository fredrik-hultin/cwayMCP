"""Configuration settings for the Cway MCP server."""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with type validation and environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Cway API Configuration
    cway_api_token: str = Field(..., description="Bearer token for Cway GraphQL API")
    cway_api_url: str = Field(
        default="https://app.cway.se/graphql", 
        description="GraphQL endpoint URL"
    )
    
    # MCP Server Configuration
    mcp_server_host: str = Field(default="localhost", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    
    # Development Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Request Configuration
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of API retries")
        

# Global settings instance
settings = Settings()