"""Updated MCP server implementation with real Cway API integration."""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
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
from ..infrastructure.cway_repositories import (
    CwayUserRepository, 
    CwayProjectRepository, 
    CwaySystemRepository
)
from ..domain.cway_entities import ProjectState


# Set up logging
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
logger = logging.getLogger(__name__)


class CwayMCPServer:
    """MCP server for real Cway API integration."""
    
    def __init__(self) -> None:
        """Initialize the MCP server."""
        self.server = Server("cway-mcp-server")
        self.graphql_client: Optional[CwayGraphQLClient] = None
        self.user_repo: Optional[CwayUserRepository] = None
        self.project_repo: Optional[CwayProjectRepository] = None
        self.system_repo: Optional[CwaySystemRepository] = None
        
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
                    description="Access to all Cway planner projects",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://users", 
                    name="Cway Users",
                    description="Access to all Cway users",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://projects/active",
                    name="Active Projects",
                    description="Currently active projects only",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://projects/completed",
                    name="Completed Projects", 
                    description="Completed projects only",
                    mimeType="application/json"
                ),
                Resource(
                    uri="cway://system/status",
                    name="System Status",
                    description="Cway system connection status",
                    mimeType="application/json"
                )
            ]
            return ListResourcesResult(resources=resources)
            
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Get a specific resource."""
            await self._ensure_initialized()
            
            try:
                if uri == "cway://projects":
                    projects = await self.project_repo.get_planner_projects()
                    content = "\n".join([
                        f"Project: {p.name} (ID: {p.id})\n"
                        f"  State: {p.state.value}\n"
                        f"  Progress: {p.percentageDone:.1%}\n"
                        f"  Dates: {p.startDate} to {p.endDate}\n"
                        for p in projects
                    ])
                    
                elif uri == "cway://users":
                    users = await self.user_repo.find_all_users()
                    content = "\n".join([
                        f"User: {u.full_name} (ID: {u.id})\n"
                        f"  Email: {u.email}\n"
                        f"  Username: {u.username}\n"
                        f"  Enabled: {u.enabled}\n"
                        for u in users
                    ])
                    
                elif uri == "cway://projects/active":
                    projects = await self.project_repo.get_active_projects()
                    content = f"Active Projects ({len(projects)}):\n\n" + "\n".join([
                        f"• {p.name} - {p.percentageDone:.1%} complete"
                        for p in projects
                    ])
                    
                elif uri == "cway://projects/completed":
                    projects = await self.project_repo.get_completed_projects()
                    content = f"Completed Projects ({len(projects)}):\n\n" + "\n".join([
                        f"• {p.name} - completed"
                        for p in projects
                    ])
                    
                elif uri == "cway://system/status":
                    is_connected = await self.system_repo.validate_connection()
                    login_info = await self.system_repo.get_login_info()
                    content = f"Cway System Status:\n"
                    content += f"  Connection: {'✅ Connected' if is_connected else '❌ Disconnected'}\n"
                    content += f"  Login Info: {json.dumps(login_info, indent=2) if login_info else 'Not available'}\n"
                    content += f"  API URL: {settings.cway_api_url}\n"
                    
                else:
                    content = f"Resource not found: {uri}"
                    
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=content)]
                )
                
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=f"Error: {e}")]
                )
                
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available tools."""
            tools = [
                Tool(
                    name="list_projects",
                    description="List all Cway planner projects",
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
                                "description": "The UUID of the project to retrieve"
                            }
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="get_active_projects",
                    description="Get all active (in progress) projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_completed_projects", 
                    description="Get all completed projects",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
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
                                "description": "The UUID of the user to retrieve"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="find_user_by_email",
                    description="Find a Cway user by email address",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "The email address of the user to find"
                            }
                        },
                        "required": ["email"]
                    }
                ),
                Tool(
                    name="get_users_page",
                    description="Get users with pagination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page": {
                                "type": "integer",
                                "description": "Page number (0-based)",
                                "default": 0
                            },
                            "size": {
                                "type": "integer",
                                "description": "Page size",
                                "default": 10
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_system_status",
                    description="Get Cway system connection status",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
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
                    content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))],
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
            self.user_repo = CwayUserRepository(self.graphql_client)
            self.project_repo = CwayProjectRepository(self.graphql_client)
            self.system_repo = CwaySystemRepository(self.graphql_client)
            
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool."""
        if name == "list_projects":
            projects = await self.project_repo.get_planner_projects()
            return {
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "state": p.state.value,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None,
                        "isActive": p.is_active,
                        "isCompleted": p.is_completed
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_project":
            project = await self.project_repo.find_project_by_id(arguments["project_id"])
            if project:
                return {
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "state": project.state.value,
                        "percentageDone": project.percentageDone,
                        "startDate": str(project.startDate) if project.startDate else None,
                        "endDate": str(project.endDate) if project.endDate else None,
                        "isActive": project.is_active,
                        "isCompleted": project.is_completed
                    }
                }
            return {"project": None, "message": "Project not found"}
            
        elif name == "get_active_projects":
            projects = await self.project_repo.get_active_projects()
            return {
                "active_projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "percentageDone": p.percentageDone,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "get_completed_projects":
            projects = await self.project_repo.get_completed_projects()
            return {
                "completed_projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "startDate": str(p.startDate) if p.startDate else None,
                        "endDate": str(p.endDate) if p.endDate else None
                    }
                    for p in projects
                ]
            }
            
        elif name == "list_users":
            users = await self.user_repo.find_all_users()
            return {
                "users": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "fullName": u.full_name,
                        "email": u.email,
                        "username": u.username,
                        "firstName": u.firstName,
                        "lastName": u.lastName,
                        "enabled": u.enabled,
                        "avatar": u.avatar,
                        "isSSO": u.isSSO
                    }
                    for u in users
                ]
            }
            
        elif name == "get_user":
            user = await self.user_repo.find_user_by_id(arguments["user_id"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "fullName": user.full_name,
                        "email": user.email,
                        "username": user.username,
                        "firstName": user.firstName,
                        "lastName": user.lastName,
                        "enabled": user.enabled,
                        "avatar": user.avatar,
                        "isSSO": user.isSSO,
                        "acceptedTerms": user.acceptedTerms,
                        "earlyAccessProgram": user.earlyAccessProgram
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "find_user_by_email":
            user = await self.user_repo.find_user_by_email(arguments["email"])
            if user:
                return {
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "fullName": user.full_name,
                        "email": user.email,
                        "username": user.username,
                        "enabled": user.enabled
                    }
                }
            return {"user": None, "message": "User not found"}
            
        elif name == "get_users_page":
            page_data = await self.user_repo.find_users_page(
                page=arguments.get("page", 0),
                size=arguments.get("size", 10)
            )
            return {
                "users": [
                    {
                        "id": u.id,
                        "name": u.name,
                        "fullName": u.full_name,
                        "email": u.email,
                        "username": u.username,
                        "enabled": u.enabled
                    }
                    for u in page_data["users"]
                ],
                "page": page_data["page"],
                "totalHits": page_data["totalHits"]
            }
            
        elif name == "get_system_status":
            is_connected = await self.system_repo.validate_connection()
            login_info = await self.system_repo.get_login_info()
            
            return {
                "system_status": {
                    "connected": is_connected,
                    "api_url": settings.cway_api_url,
                    "login_info": login_info
                }
            }
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    async def initialize(self) -> None:
        """Initialize the MCP server."""
        logger.info("Starting Cway MCP Server...")
        
        try:
            await self._ensure_initialized()
            logger.info(f"Server initialized and ready")
            logger.info(f"Connected to Cway API at {settings.cway_api_url}")
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Public cleanup method."""
        await self._cleanup()
            
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self.graphql_client:
            await self.graphql_client.disconnect()
            logger.info("GraphQL client disconnected")


def main() -> None:
    """Main entry point."""
    server = CwayMCPServer()
    asyncio.run(server.initialize())


if __name__ == "__main__":
    main()
