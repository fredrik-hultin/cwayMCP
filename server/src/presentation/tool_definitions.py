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
            name="prepare_close_projects",
            description="Preview projects before closing. Returns project details, warnings, and a confirmation token. Must be followed by confirm_close_projects to execute.",
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
            name="confirm_close_projects",
            description="Execute project closure after confirmation. Requires valid confirmation token from prepare_close_projects.",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_token": {
                        "type": "string",
                        "description": "Confirmation token from prepare_close_projects"
                    }
                },
                "required": ["confirmation_token"]
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
            name="prepare_delete_projects",
            description="Preview projects before deletion. Returns project details, warnings, and a confirmation token. Must be followed by confirm_delete_projects to execute. WARNING: This is a destructive operation that cannot be undone.",
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
            name="confirm_delete_projects",
            description="Execute project deletion after confirmation. Requires valid confirmation token from prepare_delete_projects. WARNING: This action cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_token": {
                        "type": "string",
                        "description": "Confirmation token from prepare_delete_projects"
                    }
                },
                "required": ["confirmation_token"]
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
        Tool(
            name="get_monthly_project_trends",
            description="Get month-over-month project statistics and trends",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_project_members",
            description="List project team members",
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
            name="add_project_member",
            description="Add user to project team",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user to add"
                    },
                    "role": {
                        "type": "string",
                        "description": "Role (e.g., MEMBER, MANAGER, VIEWER)",
                        "default": "MEMBER"
                    }
                },
                "required": ["project_id", "user_id"]
            }
        ),
        Tool(
            name="remove_project_member",
            description="Remove user from project team",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user to remove"
                    }
                },
                "required": ["project_id", "user_id"]
            }
        ),
        Tool(
            name="update_project_member_role",
            description="Change member permissions in project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user"
                    },
                    "role": {
                        "type": "string",
                        "description": "New role (e.g., MEMBER, MANAGER, VIEWER)"
                    }
                },
                "required": ["project_id", "user_id", "role"]
            }
        ),
        Tool(
            name="get_project_comments",
            description="Get project discussions and comments",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments (default: 50)",
                        "default": 50
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="add_project_comment",
            description="Post comment to project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "text": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["project_id", "text"]
            }
        ),
        Tool(
            name="get_project_attachments",
            description="List project file attachments",
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
            name="upload_project_attachment",
            description="Attach file to project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "file_id": {
                        "type": "string",
                        "description": "The UUID of the uploaded file"
                    },
                    "name": {
                        "type": "string",
                        "description": "Attachment name"
                    }
                },
                "required": ["project_id", "file_id", "name"]
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
            name="prepare_delete_user",
            description="Preview user before deletion. Returns user details, warnings, and a confirmation token. Must be followed by confirm_delete_user to execute. WARNING: This is a destructive operation that cannot be undone.",
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
        Tool(
            name="confirm_delete_user",
            description="Execute user deletion after confirmation. Requires valid confirmation token from prepare_delete_user. WARNING: This action cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirmation_token": {
                        "type": "string",
                        "description": "Confirmation token from prepare_delete_user"
                    }
                },
                "required": ["confirmation_token"]
            }
        ),
        Tool(
            name="find_users_and_teams",
            description="Search for both users and teams with pagination. Useful for assignment operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search query (optional)"
                    },
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
            name="get_permission_groups",
            description="Get all available permission groups for the current organisation. Admin only.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="set_user_permissions",
            description="Set permission group for multiple users. Admin only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "usernames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of usernames to update"
                    },
                    "permission_group_id": {
                        "type": "string",
                        "description": "UUID of the permission group to assign"
                    }
                },
                "required": ["usernames", "permission_group_id"]
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
        Tool(
            name="get_artwork_history",
            description="Get artwork revision history and state changes",
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
            name="analyze_artwork_ai",
            description="Trigger AI analysis on an artwork. Returns thread ID for tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to analyze"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="generate_project_summary_ai",
            description="Generate AI summary for a project tailored to specific audience",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "audience": {
                        "type": "string",
                        "enum": ["PROJECT_MANAGER", "ORDERER", "GRAPHICS_CREATOR"],
                        "description": "Target audience for the summary",
                        "default": "PROJECT_MANAGER"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="submit_artwork_for_review",
            description="Submit artwork for approval review",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to submit"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="request_artwork_changes",
            description="Request changes/revisions on an artwork",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for requesting changes"
                    }
                },
                "required": ["artwork_id", "reason"]
            }
        ),
        Tool(
            name="get_artwork_comments",
            description="Get artwork feedback thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments (default: 50)",
                        "default": 50
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="add_artwork_comment",
            description="Comment on artwork",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    },
                    "text": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["artwork_id", "text"]
            }
        ),
        Tool(
            name="get_artwork_versions",
            description="Get all revisions of artwork",
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
            name="restore_artwork_version",
            description="Rollback to previous version",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "The UUID of the version to restore"
                    }
                },
                "required": ["artwork_id", "version_id"]
            }
        ),
        Tool(
            name="assign_artwork",
            description="Assign artwork to a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user to assign"
                    }
                },
                "required": ["artwork_id", "user_id"]
            }
        ),
        Tool(
            name="duplicate_artwork",
            description="Duplicate an artwork with optional new name",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to duplicate"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New name for duplicated artwork (optional)"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="archive_artwork",
            description="Archive an artwork",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to archive"
                    }
                },
                "required": ["artwork_id"]
            }
        ),
        Tool(
            name="unarchive_artwork",
            description="Unarchive an artwork",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_id": {
                        "type": "string",
                        "description": "The UUID of the artwork to unarchive"
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


def get_share_tools() -> List[Tool]:
    """Get all share-related tool definitions."""
    return [
        Tool(
            name="find_shares",
            description="Find all file shares",
            inputSchema={
                "type": "object",
                "properties": {
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
            name="get_share",
            description="Get a specific share by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_id": {
                        "type": "string",
                        "description": "The UUID of the share"
                    }
                },
                "required": ["share_id"]
            }
        ),
        Tool(
            name="create_share",
            description="Create a new file share",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Share name"
                    },
                    "file_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file UUIDs to share"
                    },
                    "description": {
                        "type": "string",
                        "description": "Share description (optional)"
                    },
                    "expires_at": {
                        "type": "string",
                        "description": "Expiration date ISO format (optional)"
                    },
                    "max_downloads": {
                        "type": "integer",
                        "description": "Maximum downloads (optional)"
                    },
                    "password": {
                        "type": "string",
                        "description": "Password protection (optional)"
                    }
                },
                "required": ["name", "file_ids"]
            }
        ),
        Tool(
            name="delete_share",
            description="Delete a share",
            inputSchema={
                "type": "object",
                "properties": {
                    "share_id": {
                        "type": "string",
                        "description": "The UUID of the share to delete"
                    }
                },
                "required": ["share_id"]
            }
        ),
    ]


def get_category_tools() -> List[Tool]:
    """Get all category, brand, and specification tool definitions."""
    return [
        Tool(
            name="get_categories",
            description="Get all artwork categories",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_brands",
            description="Get all brands",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_print_specifications",
            description="Get all print specifications",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_category",
            description="Create a new category",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Category name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Category description (optional)"
                    },
                    "color": {
                        "type": "string",
                        "description": "Category color (hex code, optional)"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="create_brand",
            description="Create a new brand",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Brand name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brand description (optional)"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="create_print_specification",
            description="Create a new print specification",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Specification name"
                    },
                    "width": {
                        "type": "number",
                        "description": "Width value"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height value"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit (mm, cm, in, default: mm)",
                        "default": "mm"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description (optional)"
                    }
                },
                "required": ["name", "width", "height"]
            }
        ),
    ]


def get_media_management_tools() -> List[Tool]:
    """Get all media center management tool definitions."""
    return [
        Tool(
            name="create_folder",
            description="Create a new folder in media center",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Folder name"
                    },
                    "parent_folder_id": {
                        "type": "string",
                        "description": "Parent folder UUID (optional, null for root)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Folder description (optional)"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="rename_file",
            description="Rename a file in media center",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The UUID of the file to rename"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New file name"
                    }
                },
                "required": ["file_id", "new_name"]
            }
        ),
        Tool(
            name="rename_folder",
            description="Rename a folder in media center",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "The UUID of the folder to rename"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New folder name"
                    }
                },
                "required": ["folder_id", "new_name"]
            }
        ),
        Tool(
            name="move_files",
            description="Move files to a different folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file UUIDs to move"
                    },
                    "target_folder_id": {
                        "type": "string",
                        "description": "Destination folder UUID"
                    }
                },
                "required": ["file_ids", "target_folder_id"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file from media center",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The UUID of the file to delete"
                    }
                },
                "required": ["file_id"]
            }
        ),
        Tool(
            name="delete_folder",
            description="Delete a folder from media center",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {
                        "type": "string",
                        "description": "The UUID of the folder to delete"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force delete even if not empty (default: false)",
                        "default": False
                    }
                },
                "required": ["folder_id"]
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


def get_team_tools() -> List[Tool]:
    """Get all team management tool definitions."""
    return [
        Tool(
            name="get_team_members",
            description="Get all team members for a project",
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
            name="add_team_member",
            description="Add a user to project team",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user to add"
                    },
                    "role": {
                        "type": "string",
                        "description": "Role for the team member (optional)"
                    }
                },
                "required": ["project_id", "user_id"]
            }
        ),
        Tool(
            name="remove_team_member",
            description="Remove a user from project team",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user to remove"
                    }
                },
                "required": ["project_id", "user_id"]
            }
        ),
        Tool(
            name="update_team_member_role",
            description="Update a team member's role in project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user"
                    },
                    "role": {
                        "type": "string",
                        "description": "New role for the team member"
                    }
                },
                "required": ["project_id", "user_id", "role"]
            }
        ),
        Tool(
            name="get_user_roles",
            description="Get all available user roles and their permissions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="transfer_project_ownership",
            description="Transfer project ownership to another user",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "new_owner_id": {
                        "type": "string",
                        "description": "The UUID of the new owner"
                    }
                },
                "required": ["project_id", "new_owner_id"]
            }
        ),
    ]


def get_search_and_activity_tools() -> List[Tool]:
    """Get search and activity tracking tool definitions."""
    return [
        Tool(
            name="search_artworks",
            description="Search artworks with filters and pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text (optional)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Filter by project UUID (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by artwork status (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results per page (default: 50)",
                        "default": 50
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (0-based, default: 0)",
                        "default": 0
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_project_timeline",
            description="Get chronological event timeline for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The UUID of the project"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of events (default: 100)",
                        "default": 100
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_user_activity",
            description="Get user activity history",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "default": 30
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of activities (default: 100)",
                        "default": 100
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="bulk_update_artwork_status",
            description="Batch update status for multiple artworks",
            inputSchema={
                "type": "object",
                "properties": {
                    "artwork_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of artwork UUIDs to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status for all artworks"
                    }
                },
                "required": ["artwork_ids", "status"]
            }
        ),
    ]


def get_auth_tools() -> List[Tool]:
    """Get all authentication-related tool definitions."""
    return [
        Tool(
            name="login",
            description="Initiate user authentication flow with Entra ID. Returns authorization URL to open in browser. Only available when AUTH_METHOD=oauth2.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="complete_login",
            description="Complete login by exchanging authorization code for tokens. Call this after authenticating in browser. Only available when AUTH_METHOD=oauth2.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "User's email address"
                    },
                    "authorization_code": {
                        "type": "string",
                        "description": "Authorization code from Entra ID redirect"
                    },
                    "state": {
                        "type": "string",
                        "description": "State parameter from authorization response"
                    }
                },
                "required": ["username", "authorization_code", "state"]
            }
        ),
        Tool(
            name="logout",
            description="Logout user by removing stored tokens. Only available when AUTH_METHOD=oauth2.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="whoami",
            description="Get current user authentication status and token expiry information. Only available when AUTH_METHOD=oauth2.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="list_authenticated_users",
            description="List all users who have authenticated and have stored tokens. Only available when AUTH_METHOD=oauth2.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


def get_organization_tools() -> List[Tool]:
    """Get organization management tool definitions."""
    return [
        Tool(
            name="list_organizations",
            description="List all configured organizations with their tokens. Shows which organization is currently active.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="switch_organization",
            description="Switch to a different organization. Use 'default' for the primary token, or the name of a configured organization (from CWAY_TOKEN_<NAME> env vars).",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_name": {
                        "type": "string",
                        "description": "Organization name to switch to ('default' or a configured org name)"
                    }
                },
                "required": ["org_name"]
            }
        ),
        Tool(
            name="get_active_organization",
            description="Get the name of the currently active organization.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
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
        get_share_tools() +
        get_category_tools() +
        get_media_management_tools() +
        get_team_tools() +
        get_search_and_activity_tools() +
        get_system_tools() +
        get_analytics_tools() +
        get_indexing_tools() +
        get_auth_tools() +
        get_organization_tools()
    )
