"""Resource formatters for MCP presentation layer."""

from typing import List
from ..domain.entities import Project, User, ProjectState


class ResourceFormatter:
    """Base class for resource formatters."""
    
    @staticmethod
    def format_projects(projects: List[Project]) -> str:
        """Format projects list as text content."""
        if not projects:
            return "No projects found."
        
        content_parts = []
        for project in projects:
            status_display = project.status.value if isinstance(project.status, ProjectState) else project.status
            part = (
                f"Project: {project.name} (ID: {project.id})\n"
                f"  Status: {status_display}\n"
                f"  Description: {project.description or 'N/A'}\n"
                f"  Created: {project.created_at}\n"
            )
            content_parts.append(part)
        
        return "\n".join(content_parts)
    
    @staticmethod
    def format_users(users: List[User]) -> str:
        """Format users list as text content."""
        if not users:
            return "No users found."
        
        content_parts = []
        for user in users:
            part = (
                f"User: {user.name or user.email} (ID: {user.id})\n"
                f"  Email: {user.email}\n"
                f"  Role: {user.role}\n"
                f"  Created: {user.created_at}\n"
            )
            content_parts.append(part)
        
        return "\n".join(content_parts)
    
    @staticmethod
    def format_schema(schema: str) -> str:
        """Format GraphQL schema as text content."""
        return str(schema) if schema else "Schema not available"
    
    @staticmethod
    def format_error(error: Exception, context: str = "") -> str:
        """Format error message for display."""
        context_prefix = f"{context}: " if context else ""
        return f"Error: {context_prefix}{str(error)}"
    
    @staticmethod
    def format_not_found(resource_uri: str) -> str:
        """Format not found message."""
        return f"Resource not found: {resource_uri}"
