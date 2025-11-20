"""MCP Tool Definitions.

All tool schemas defined here to keep the main server file clean.
"""
from mcp.types import Tool
from typing import List


def get_project_tools() -> List[Tool]:
    """Get all project-related tool definitions."""
    return [
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
            description="Get a specific Cway planner project by ID",
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
            name="search_projects",
            description="Search for projects with optional query and limit",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_project_by_id",
            description="Get a regular project by ID (not planner project)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="create_project",
            description="Create a new project",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Project description (optional)"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="update_project",
            description="Update an existing project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "New project name (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New project description (optional)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="close_projects",
            description="Close one or more projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project UUIDs to close"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force close even if artworks are incomplete",
                        "default": False
                    }
                },
                "required": ["project_ids"]
            }
        ),
        Tool(
            name="reopen_projects",
            description="Reopen closed projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project UUIDs to reopen"
                    }
                },
                "required": ["project_ids"]
            }
        ),
        Tool(
            name="delete_projects",
            description="Delete one or more projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project UUIDs to delete"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force delete even if not empty",
                        "default": False
                    }
                },
                "required": ["project_ids"]
            }
        ),
        Tool(
            name="get_project_status_summary",
            description="Get aggregate project statistics and status distribution across all projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="compare_projects",
            description="Compare multiple projects side-by-side with normalized metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project UUIDs to compare (2 or more)"
                    }
                },
                "required": ["project_ids"]
            }
        ),
        Tool(
            name="get_project_history",
            description="Get detailed event history timeline for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    }
                },
                "required": ["project_id"]
            }
        ),
    ]


def get_user_tools() -> List[Tool]:
    """Get all user-related tool definitions."""
    return [
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
            name="search_users",
            description="Search for users by username",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for username (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="create_user",
            description="Create a new user",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "User email address"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username"
                    },
                    "first_name": {
                        "type": "string",
                        "description": "First name (optional)"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name (optional)"
                    }
                },
                "required": ["email", "username"]
            }
        ),
        Tool(
            name="update_user_name",
            description="Update user's real name",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username"
                    },
                    "first_name": {
                        "type": "string",
                        "description": "First name (optional)"
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name (optional)"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="delete_user",
            description="Delete a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username of user to delete"
                    }
                },
                "required": ["username"]
            }
        ),
    ]


def get_artwork_tools() -> List[Tool]:
    """Get all artwork-related tool definitions."""
    return [
        Tool(
            name="get_artwork",
            description="Get a single artwork by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="create_artwork",
            description="Create a new artwork in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "name": {
                        "type": "string",
                        "description": "Artwork name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Artwork description (optional)"
                    }
                },
                "required": ["project_id", "name"]
            }
        ),
        Tool(
            name="approve_artwork",
            description="Approve an artwork",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to approve"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="reject_artwork",
            description="Reject an artwork with optional reason",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to reject"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rejection (optional)"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="get_my_artworks",
            description="Get all artworks relevant to the current user (artworks to approve, artworks to upload)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_artworks_to_approve",
            description="Get all artworks awaiting approval by the current user",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_artworks_to_upload",
            description="Get all artworks where the current user needs to upload a revision",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="download_artworks",
            description="Create a download job for artwork files (latest revisions). Returns job ID for downloading from file service.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of artwork UUIDs to download"
                    },
                    "zip_name": {
                        "type": "string",
                        "description": "Name for the zip file (optional, default: 'artworks')"
                    }
                },
                "required": ["artwork_ids"]
            }
        ),
        Tool(
            name="get_artwork_preview",
            description="Get artwork preview file information including URL for display",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
    ]


def get_folder_tools() -> List[Tool]:
    """Get all folder/media center tool definitions."""
    return [
        Tool(
            name="get_folder_tree",
            description="Get the complete folder tree structure",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_folder",
            description="Get a specific folder by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "The UUID of the folder"
                    }
                },
                "required": ["folder_id"]
            }
        ),
        Tool(
            name="get_folder_items",
            description="Get items in a specific folder with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "The UUID of the folder"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (0-based)",
                        "default": 0
                    },
                    "size": {
                        "type": "integer",
                        "description": "Page size",
                        "default": 20
                    }
                },
                "required": ["folder_id"]
            }
        ),
        Tool(
            name="search_media_center",
            description="Search media center with full-text search and filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text (optional)"
                    },
                    "folder_id": {
                        "type": "string",
                        "description": "Limit search to specific folder (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_media_center_stats",
            description="Get media center storage and usage statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="download_folder_contents",
            description="Download all files in a folder as a zip archive. Returns job ID for download tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "The UUID of the folder to download"
                    },
                    "zip_name": {
                        "type": "string",
                        "description": "Name for the zip file (optional, default: 'folder')"
                    }
                },
                "required": ["folder_id"]
            }
        ),
        Tool(
            name="download_project_media",
            description="Download all media files associated with a project. Returns job ID for download tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "zip_name": {
                        "type": "string",
                        "description": "Name for the zip file (optional)"
                    }
                },
                "required": ["project_id"]
            }
        ),
    ]


def get_file_tools() -> List[Tool]:
    """Get all file-related tool definitions."""
    return [
        Tool(
            name="get_file",
            description="Get a file by UUID",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The UUID of the file"
                    }
                },
                "required": ["file_id"]
            }
        ),
    ]


def get_system_tools() -> List[Tool]:
    """Get all system-related tool definitions."""
    return [
        Tool(
            name="get_system_status",
            description="Get Cway system connection status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_login_info",
            description="Get current user login information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


def get_analytics_tools() -> List[Tool]:
    """Get all analytics and KPI tool definitions."""
    return [
        Tool(
            name="analyze_project_velocity",
            description="Analyze velocity trends and patterns for a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project to analyze"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_temporal_dashboard",
            description="Get comprehensive temporal KPI dashboard with velocity and stagnation analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "analysis_period_days": {
                        "type": "integer",
                        "description": "Number of days to analyze (default: 90)",
                        "default": 90
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_stagnation_alerts",
            description="Get projects at risk of stagnation with urgency scores and recommendations",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_urgency_score": {
                        "type": "integer",
                        "description": "Minimum urgency score (1-10, default: 5)",
                        "default": 5
                    }
                },
                "required": []
            }
        ),
    ]


def get_indexing_tools() -> List[Tool]:
    """Get all indexing-related tool definitions."""
    return [
        Tool(
            name="index_all_content",
            description="Index all documents and site pages to configured targets",
            inputSchema={
                "type": "object",
                "properties": {
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific target names to index to (default: all enabled)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="quick_backup",
            description="Quick backup of all content to local files",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="index_project_content",
            description="Index documents and pages for a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project to index"
                    },
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific target names to index to (optional)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="configure_indexing_target",
            description="Add or update an indexing target configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the indexing target"
                    },
                    "platform": {
                        "type": "string",
                        "description": "Platform type (elasticsearch, file, algolia, etc.)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this target is for"
                    },
                    "config": {
                        "type": "object",
                        "description": "Platform-specific configuration"
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether this target is enabled",
                        "default": True
                    }
                },
                "required": ["name", "platform", "description"]
            }
        ),
        Tool(
            name="get_indexing_job_status",
            description="Get status of a specific indexing job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The ID of the indexing job to check"
                    }
                },
                "required": ["job_id"]
            }
        ),
    ]


def get_all_tools() -> List[Tool]:
    """Get all tool definitions."""
    return (
        get_project_tools() +
        get_user_tools() +
        get_artwork_tools() +
        get_folder_tools() +
        get_file_tools() +
        get_system_tools() +
        get_analytics_tools() +
        get_indexing_tools()
    )
