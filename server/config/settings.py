"""Configuration settings for the Cway MCP server."""

import os
from typing import Optional, Dict
from pathlib import Path
from pydantic import Field, ConfigDict, model_validator
from pydantic_settings import BaseSettings

# Get the server directory (parent of config directory)
_CONFIG_DIR = Path(__file__).parent
_SERVER_DIR = _CONFIG_DIR.parent
_ENV_FILE = _SERVER_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with type validation and environment variable support."""
    
    model_config = ConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Authentication Configuration
    auth_method: str = Field(default="static", description="Authentication method: 'static' or 'oauth2'")
    
    # Static Token Configuration (for backward compatibility - single-user mode)
    cway_api_token: Optional[str] = Field(default=None, description="Primary bearer token for Cway GraphQL API")
    
    # Token Storage Configuration (for multi-user mode)
    token_encryption_key: Optional[str] = Field(
        default=None, 
        description="Fernet encryption key for token storage (base64-encoded)"
    )
    token_db_path: str = Field(
        default="data/tokens.db", 
        description="Path to SQLite database for token storage"
    )
    
    
    # Cway API Configuration
    cway_api_url: str = Field(
        default="https://app.cway.se/graphql", 
        description="GraphQL endpoint URL"
    )
    
    # MCP Server Configuration
    mcp_server_host: str = Field(default="localhost", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    
    # Development Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: Path = Field(default=Path("logs"), description="Directory for log files")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Request Configuration
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of API retries")
    
    def validate_auth_config(self) -> None:
        """Validate that authentication configuration is complete."""
        # In multi-user mode, tokens are stored in database, not .env
        # So we only validate for single-user/development mode
        if not self.cway_api_token:
            raise ValueError(
                "No API token configured. Set CWAY_API_TOKEN environment variable for single-user mode."
            )

# Global settings instance
settings = Settings()
