"""MCP server implementation for Cway integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ReadResourceResult,
    ListToolsResult,
    CallToolResult,
    ListResourcesResult,
)

from config.settings import settings
from ..infrastructure.graphql_client import CwayGraphQLClient, CwayAPIError
from ..infrastructure.repositories import GraphQLProjectRepository, GraphQLUserRepository
from ..application.use_cases import ProjectUseCases, UserUseCases
from .formatters import ResourceFormatter


# Set up logging - redirect to file to avoid interfering with stdio protocol
import sys
from pathlib import Path

# Ensure log directory exists
log_dir = Path(settings.log_dir)
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "mcp_server.log"

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Log to stderr, not stdout
    ]
)
logger = logging.getLogger(__name__)


class CwayMCPServer:
    """MCP server for Cway integration."""
    
    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.server = Server("cway-mcp-server")
        self.graphql_client: Optional[CwayGraphQLClient] = None
        self.project_use_cases: Optional[ProjectUseCases] = None
        self.user_use_cases: Optional[UserUseCases] = None
        
        # Register handlers
        self._register_handlers()
        
    def _register_handlers(self) -> None:
        """Register MCP handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            resources = [
                Resource(
                    uri="cway://projects",
                    name="Cway Projects",
                    description="Access to all Cway projects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://users", 
                    name="Cway Users",
                    description="Access to all Cway users",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://schema",
                    name="GraphQL Schema",
                    description="Cway GraphQL API schema",
                    mimeType="application/graphql"
                )
            ]
            return ListResourcesResult(resources=resources)
            
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Get a specific resource."""
            await self._ensure_initialized()
            
            try:
                if uri == "cway://projects":
                    projects = await self.project_use_cases.list_projects()
                    content = ResourceFormatter.format_projects(projects)
                    
                elif uri == "cway://users":
                    users = await self.user_use_cases.list_users()
                    content = ResourceFormatter.format_users(users)
                    
                elif uri == "cway://schema":
                    schema = await self.graphql_client.get_schema()
                    content = ResourceFormatter.format_schema(schema)
                    
                else:
                    content = ResourceFormatter.format_not_found(uri)
                    
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=content)]
                )
                
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=ResourceFormatter.format_error(e, f"reading resource {uri}"))]
                )
                
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            tools = [
                Tool(
                    name="list_projects",
                    description="List all Cway projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_project",
                    description="Get a specific Cway project by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The ID of the project to retrieve"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="create_project",
                    description="Create a new Cway project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the project"
                            },
                            "description": {
                                "type": "string",
                                "description": "The description of the project"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["ACTIVE", "INACTIVE", "COMPLETED", "CANCELLED", "PLANNED", "IN_PROGRESS", "DELIVERED", "ARCHIVED"],
                                "description": "The status of the project",
                                "default": "ACTIVE"
                            }
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="update_project",
                    description="Update an existing Cway project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "The ID of the project to update"
                            },
                            "name": {
                                "type": "string",
                                "description": "The new name of the project"
                            },
                            "description": {
                                "type": "string",
                                "description": "The new description of the project"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["ACTIVE", "INACTIVE", "COMPLETED", "CANCELLED", "PLANNED", "IN_PROGRESS", "DELIVERED", "ARCHIVED"],
                                "description": "The new status of the project"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="list_users",
                    description="List all Cway users",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_user",
                    description="Get a specific Cway user by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user to retrieve"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="get_user_by_email",
                    description="Get a Cway user by email address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "The email address of the user to retrieve"
                            }
                        },
                        "required": ["email"]
                    }
                ),
                Tool(
                    name="create_user",
                    description="Create a new Cway user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "The email address of the user"
                            },
                            "name": {
                                "type": "string",
                                "description": "The name of the user"
                            },
                            "role": {
                                "type": "string",
                                "enum": ["admin", "user", "viewer"],
                                "description": "The role of the user",
                                "default": "user"
                            }
                        },
                        "required": ["email"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
            
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> CallToolResult:
            """Call a specific tool."""
            await self._ensure_initialized()
            
            if arguments is None:
                arguments = {}
                
            try:
                result = await self._execute_tool(name, arguments)
                return CallToolResult(
                    content=[TextContent(type="text", text=str(result))],
                    isError=False
                )
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {e}")],
                    isError=True
                )
                
    async def _ensure_initialized(self) -> None:
        """Ensure the server is initialized with all dependencies."""
        if not self.graphql_client:
            self.graphql_client = CwayGraphQLClient()
            await self.graphql_client.connect()
            
            # Initialize repositories
            project_repo = GraphQLProjectRepository(self.graphql_client)
            user_repo = GraphQLUserRepository(self.graphql_client)
            
            # Initialize use cases
            self.project_use_cases = ProjectUseCases(project_repo)
            self.user_use_cases = UserUseCases(user_repo)
            
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool."""
        if name == "list_projects":
            projects = await self.project_use_cases.list_projects()
            return {
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "status": p.status,
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat()
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_project":
            project = await self.project_use_cases.get_project(arguments["project_id"])
            if project:
                return {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat()
                    }
                }
            return {"project": None, "message": "Project not found"}
            
        elif name == "create_project":
            project = await self.project_use_cases.create_project(
                name=arguments["name"],
                description=arguments.get("description"),
                status=arguments.get("status", "active")
            )
            return {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat()
                },
                "message": "Project created successfully"
            }
            
        elif name == "update_project":
            project = await self.project_use_cases.update_project(
                project_id=arguments["project_id"],
                name=arguments.get("name"),
                description=arguments.get("description"),
                status=arguments.get("status")
            )
            if project:
                return {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "status": project.status,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat()
                    },
                    "message": "Project updated successfully"
                }
            return {"project": None, "message": "Project not found"}
            
        elif name == "list_users":
            users = await self.user_use_cases.list_users()
            return {
                "users": [
                    {
                        "id": u.id,
                        "email": u.email,
                        "name": u.name,
                        "role": u.role,
                        "created_at": u.created_at.isoformat(),
                        "updated_at": u.updated_at.isoformat()
                    }
                    for u in users
                ]
            }
            
        elif name == "get_user":
            user = await self.user_use_cases.get_user(arguments["user_id"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "role": user.role,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "get_user_by_email":
            user = await self.user_use_cases.get_user_by_email(arguments["email"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "role": user.role,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "create_user":
            user = await self.user_use_cases.create_user(
                email=arguments["email"],
                name=arguments.get("name"),
                role=arguments.get("role", "user")
            )
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat()
                },
                "message": "User created successfully"
            }
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Cway MCP Server...")
        
        try:
            await self._ensure_initialized()
            logger.info(f"Server initialized and ready")
            
            # Run the MCP server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self._cleanup()
            
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self.graphql_client:
            await self.graphql_client.disconnect()
            logger.info("GraphQL client disconnected")


def main() -> None:
    """Main entry point."""
    server = CwayMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()