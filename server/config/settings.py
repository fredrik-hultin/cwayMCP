"""Configuration settings for the Cway MCP server."""

from typing import Optional
from pathlib import Path
from pydantic import Field, ConfigDict
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
    
    # Static Token Configuration (legacy)
    cway_api_token: Optional[str] = Field(default=None, description="Bearer token for Cway GraphQL API")
    
    # OAuth2 Configuration
    azure_tenant_id: Optional[str] = Field(default=None, description="Azure AD tenant ID")
    azure_client_id: Optional[str] = Field(default=None, description="Azure AD application (client) ID")
    azure_client_secret: Optional[str] = Field(default=None, description="Azure AD client secret")
    oauth2_scope: str = Field(
        default="https://graph.microsoft.com/.default",
        description="OAuth2 scope"
    )
    use_device_code_flow: bool = Field(
        default=False,
        description="Use device code flow for OAuth2 (interactive)"
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
        

# Global settings instance
settings = Settings()