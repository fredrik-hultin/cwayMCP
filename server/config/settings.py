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
    
    # Static Token Configuration
    cway_api_token: Optional[str] = Field(default=None, description="Primary bearer token for Cway GraphQL API")
    
    # Multi-org token support
    active_org: Optional[str] = Field(default=None, description="Currently active organization name")
    org_tokens: Dict[str, str] = Field(default_factory=dict, description="Organization-specific tokens")
    
    
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
    
    @model_validator(mode='after')
    def load_org_tokens(self):
        """Load organization tokens from environment variables with prefix CWAY_TOKEN_"""
        for key, value in os.environ.items():
            if key.startswith('CWAY_TOKEN_') and value:
                org_name = key.replace('CWAY_TOKEN_', '').lower()
                self.org_tokens[org_name] = value
        return self
    
    def get_active_token(self) -> Optional[str]:
        """Get the currently active token (org-specific or primary)."""
        if self.active_org and self.active_org in self.org_tokens:
            return self.org_tokens[self.active_org]
        return self.cway_api_token
    
    def list_organizations(self) -> list[str]:
        """List all configured organizations."""
        orgs = list(self.org_tokens.keys())
        if self.cway_api_token:
            orgs.insert(0, "default")
        return orgs
    
    def validate_auth_config(self) -> None:
        """Validate that authentication configuration is complete."""
        if not self.cway_api_token and not self.org_tokens:
            raise ValueError(
                "No API tokens configured. Set CWAY_API_TOKEN or CWAY_TOKEN_<ORG_NAME> environment variables."
            )

# Global settings instance
settings = Settings()
