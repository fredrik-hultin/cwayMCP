# Cway MCP Server - Tool Catalog

**Version:** 1.0 (Phase 2.3)  
**Total Tools:** 80  
**GraphQL Coverage:** 31% (80/258 operations)

Complete reference for all MCP tools available in the Cway MCP Server.

---

## Table of Contents

- [Project Management](#project-management-15-tools) (15 tools)
- [User Management](#user-management-10-tools) (10 tools)
- [Artwork Operations](#artwork-operations-17-tools) (17 tools)
- [Media Center](#media-center-10-tools) (10 tools)
- [Categories & Setup](#categories--setup-6-tools) (6 tools)
- [Collaboration & Sharing](#collaboration--sharing-8-tools) (8 tools)
- [Analytics & KPIs](#analytics--kpis-8-tools) (8 tools)
- [AI Features](#ai-features-2-tools) (2 tools)
- [System](#system-4-tools) (4 tools)

---

## Project Management (15 tools)

### 1. `list_projects`
**Description:** List all Cway planner projects  
**Parameters:** None  
**Returns:** Array of all projects

**Example:**
```json
{
  "tool": "list_projects",
  "arguments": {}
}
```

### 2. `get_project`
**Description:** Get a specific Cway planner project by ID  
**Parameters:**
- `project_id` (string, required) - The UUID of the project

**Example:**
```json
{
  "tool": "get_project",
  "arguments": {
    "project_id": "abc-123-def"
  }
}
```

### 3. `get_active_projects`
**Description:** Get all active (in progress) projects  
**Parameters:** None  
**Returns:** Array of active projects

### 4. `get_completed_projects`
**Description:** Get all completed projects  
**Parameters:** None  
**Returns:** Array of completed projects

### 5. `search_projects`
**Description:** Search for projects with optional query and limit  
**Parameters:**
- `query` (string, optional) - Search query
- `limit` (integer, optional, default: 10) - Maximum results

**Example:**
```json
{
  "tool": "search_projects",
  "arguments": {
    "query": "marketing",
    "limit": 20
  }
}
```

### 6. `get_project_by_id`
**Description:** Get a regular project by ID (not planner project)  
**Parameters:**
- `project_id` (string, required) - The UUID of the project

### 7. `create_project`
**Description:** Create a new project  
**Parameters:**
- `name` (string, required) - Project name
- `description` (string, optional) - Project description

**Example:**
```json
{
  "tool": "create_project",
  "arguments": {
    "name": "Q4 Campaign",
    "description": "Marketing campaign for Q4 2024"
  }
}
```

### 8. `update_project`
**Description:** Update an existing project  
**Parameters:**
- `project_id` (string, required) - Project ID
- `name` (string, optional) - New name
- `description` (string, optional) - New description

### 9. `close_projects`
**Description:** Close one or more projects  
**Parameters:**
- `project_ids` (array[string], required) - Project UUIDs to close
- `force` (boolean, optional, default: false) - Force close incomplete projects

### 10. `reopen_projects`
**Description:** Reopen closed projects  
**Parameters:**
- `project_ids` (array[string], required) - Project UUIDs to reopen

### 11. `delete_projects`
**Description:** Delete one or more projects  
**Parameters:**
- `project_ids` (array[string], required) - Project UUIDs to delete
- `force` (boolean, optional, default: false) - Force delete non-empty projects

### 12. `get_project_status_summary`
**Description:** Get aggregate project statistics and status distribution  
**Parameters:** None  
**Returns:** Project counts by status, overall statistics

### 13. `compare_projects`
**Description:** Compare multiple projects side-by-side with normalized metrics  
**Parameters:**
- `project_ids` (array[string], required) - 2+ project UUIDs to compare

### 14. `get_project_history`
**Description:** Get detailed event history timeline for a project  
**Parameters:**
- `project_id` (string, required) - Project UUID

### 15. `get_monthly_project_trends`
**Description:** Get month-over-month project statistics and trends  
**Parameters:** None  
**Returns:** Monthly project count trends for analytics

---

## User Management (10 tools)

### 16. `list_users`
**Description:** List all Cway users  
**Parameters:** None  
**Returns:** Array of all users

### 17. `get_user`
**Description:** Get a specific Cway user by ID  
**Parameters:**
- `user_id` (string, required) - User UUID

### 18. `find_user_by_email`
**Description:** Find a Cway user by email address  
**Parameters:**
- `email` (string, required) - Email address to search

**Example:**
```json
{
  "tool": "find_user_by_email",
  "arguments": {
    "email": "john@example.com"
  }
}
```

### 19. `get_users_page`
**Description:** Get users with pagination  
**Parameters:**
- `page` (integer, optional, default: 0) - Page number (0-based)
- `size` (integer, optional, default: 10) - Page size

### 20. `search_users`
**Description:** Search for users by username  
**Parameters:**
- `query` (string, optional) - Username search query

### 21. `create_user`
**Description:** Create a new user  
**Parameters:**
- `email` (string, required) - User email
- `username` (string, required) - Username
- `first_name` (string, optional) - First name
- `last_name` (string, optional) - Last name

### 22. `update_user_name`
**Description:** Update user's real name  
**Parameters:**
- `username` (string, required) - Username
- `first_name` (string, optional) - New first name
- `last_name` (string, optional) - New last name

### 23. `delete_user`
**Description:** Delete a user  
**Parameters:**
- `username` (string, required) - Username to delete

### 24. `find_users_and_teams`
**Description:** Search for both users and teams with pagination  
**Parameters:**
- `search` (string, optional) - Search query
- `page` (integer, optional) - Page number
- `size` (integer, optional) - Page size

**Use case:** Finding users or teams to assign to projects

### 25. `get_permission_groups`
**Description:** Get all available permission groups (Admin only)  
**Parameters:** None  
**Returns:** List of permission groups with details

### 26. `set_user_permissions`
**Description:** Set permission group for multiple users (Admin only)  
**Parameters:**
- `user_ids` (array[string], required) - User UUIDs
- `permission_group_id` (string, required) - Permission group UUID

---

## Artwork Operations (17 tools)

### 27. `get_artwork`
**Description:** Get a single artwork by ID  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

### 28. `create_artwork`
**Description:** Create a new artwork in a project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `name` (string, required) - Artwork name
- `description` (string, optional) - Artwork description

### 29. `approve_artwork`
**Description:** Approve an artwork  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

### 30. `reject_artwork`
**Description:** Reject an artwork with optional reason  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID
- `reason` (string, optional) - Rejection reason

### 31. `get_my_artworks`
**Description:** Get all artworks relevant to current user  
**Parameters:** None  
**Returns:** Artworks to approve and artworks to upload

### 32. `get_artworks_to_approve`
**Description:** Get artworks awaiting approval by current user  
**Parameters:** None  
**Returns:** Array of artworks pending approval

### 33. `get_artworks_to_upload`
**Description:** Get artworks where current user needs to upload revision  
**Parameters:** None  
**Returns:** Array of artworks needing uploads

### 34. `download_artworks`
**Description:** Create download job for artwork files (latest revisions)  
**Parameters:**
- `artwork_ids` (array[string], required) - Artwork UUIDs
- `zip_name` (string, optional) - Name for zip file

**Returns:** Job ID for tracking download

### 35. `get_artwork_preview`
**Description:** Get artwork preview file information with URL  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

### 36. `get_artwork_history`
**Description:** Get artwork revision history and state changes  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

**Returns:** Complete timeline of artwork events

### 37. `analyze_artwork_ai`
**Description:** Trigger AI analysis on an artwork  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

**Returns:** Thread ID for tracking analysis progress

### 38. `generate_project_summary_ai`
**Description:** Generate AI summary for project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `audience` (string, required) - Target audience (PROJECT_MANAGER, ORDERER, GRAPHICS_CREATOR)

**Example:**
```json
{
  "tool": "generate_project_summary_ai",
  "arguments": {
    "project_id": "abc-123",
    "audience": "PROJECT_MANAGER"
  }
}
```

### 39. `submit_artwork_for_review`
**Description:** Submit artwork for approval review  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

### 40. `request_artwork_changes`
**Description:** Request changes/revisions on an artwork  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID
- `message` (string, required) - Change request details

### 41. `get_artwork_comments`
**Description:** Get artwork feedback thread  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

### 42. `add_artwork_comment`
**Description:** Comment on artwork  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID
- `text` (string, required) - Comment text

### 43. `get_artwork_versions`
**Description:** Get all revisions of artwork  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID

**Returns:** List of all artwork versions with metadata

### 44. `restore_artwork_version`
**Description:** Rollback to previous version  
**Parameters:**
- `artwork_id` (string, required) - Artwork UUID
- `version_id` (string, required) - Version UUID to restore

---

## Media Center (10 tools)

### 45. `get_folder_tree`
**Description:** Get the complete folder tree structure  
**Parameters:** None  
**Returns:** Hierarchical folder structure

### 46. `get_folder`
**Description:** Get a specific folder by ID  
**Parameters:**
- `folder_id` (string, required) - Folder UUID

### 47. `get_folder_items`
**Description:** Get items in a specific folder with pagination  
**Parameters:**
- `folder_id` (string, required) - Folder UUID
- `page` (integer, optional, default: 0) - Page number
- `size` (integer, optional, default: 20) - Page size

### 48. `search_media_center`
**Description:** Search media center with full-text search and filters  
**Parameters:**
- `query` (string, optional) - Search query
- `folder_id` (string, optional) - Limit to specific folder
- `limit` (integer, optional, default: 50) - Max results

**Example:**
```json
{
  "tool": "search_media_center",
  "arguments": {
    "query": "logo",
    "limit": 20
  }
}
```

### 49. `get_media_center_stats`
**Description:** Get media center storage and usage statistics  
**Parameters:** None  
**Returns:** Storage usage, file counts, folder statistics

### 50. `download_folder_contents`
**Description:** Download all files in a folder as zip  
**Parameters:**
- `folder_id` (string, required) - Folder UUID
- `zip_name` (string, optional) - Zip file name

**Returns:** Job ID for download tracking

### 51. `download_project_media`
**Description:** Download all media files for a project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `zip_name` (string, optional) - Zip file name

**Returns:** Job ID for download tracking

### 52. `get_file`
**Description:** Get a file by UUID  
**Parameters:**
- `file_id` (string, required) - File UUID

**Returns:** File metadata and download URL

### 53. `find_shares`
**Description:** Find all file shares  
**Parameters:**
- `limit` (integer, optional, default: 50) - Max results

**Returns:** List of file shares with pagination

### 54. `get_share`
**Description:** Get a specific share by ID  
**Parameters:**
- `share_id` (string, required) - Share UUID

**Returns:** Share details including files and access info

---

## Categories & Setup (6 tools)

### 55. `get_categories`
**Description:** Get all artwork categories  
**Parameters:** None  
**Returns:** List of all categories

### 56. `get_brands`
**Description:** Get all brands  
**Parameters:** None  
**Returns:** List of all brands

### 57. `get_print_specifications`
**Description:** Get all print specifications  
**Parameters:** None  
**Returns:** List of all print specs with dimensions

### 58. `create_category`
**Description:** Create a new category  
**Parameters:**
- `name` (string, required) - Category name
- `description` (string, optional) - Category description
- `color` (string, optional) - Color code

**Example:**
```json
{
  "tool": "create_category",
  "arguments": {
    "name": "Social Media",
    "description": "Social media graphics",
    "color": "#FF5733"
  }
}
```

### 59. `create_brand`
**Description:** Create a new brand  
**Parameters:**
- `name` (string, required) - Brand name
- `description` (string, optional) - Brand description

### 60. `create_print_specification`
**Description:** Create a new print specification  
**Parameters:**
- `name` (string, required) - Spec name
- `width` (number, required) - Width
- `height` (number, required) - Height
- `unit` (string, optional, default: "mm") - Unit (mm, in, cm)
- `description` (string, optional) - Spec description

**Example:**
```json
{
  "tool": "create_print_specification",
  "arguments": {
    "name": "Business Card",
    "width": 85,
    "height": 55,
    "unit": "mm"
  }
}
```

---

## Collaboration & Sharing (8 tools)

### 61. `get_project_members`
**Description:** List project team members  
**Parameters:**
- `project_id` (string, required) - Project UUID

**Returns:** List of members with roles

### 62. `add_project_member`
**Description:** Add user to project team  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `user_id` (string, required) - User UUID
- `role` (string, optional, default: "MEMBER") - Role (MANAGER, MEMBER, VIEWER)

### 63. `remove_project_member`
**Description:** Remove user from project team  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `user_id` (string, required) - User UUID

### 64. `update_project_member_role`
**Description:** Change member permissions in project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `user_id` (string, required) - User UUID
- `role` (string, required) - New role

### 65. `get_project_comments`
**Description:** Get project discussions and comments  
**Parameters:**
- `project_id` (string, required) - Project UUID

### 66. `add_project_comment`
**Description:** Post comment to project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `text` (string, required) - Comment text

### 67. `get_project_attachments`
**Description:** List project file attachments  
**Parameters:**
- `project_id` (string, required) - Project UUID

### 68. `upload_project_attachment`
**Description:** Attach file to project  
**Parameters:**
- `project_id` (string, required) - Project UUID
- `file_id` (string, required) - File UUID from media center

---

## Analytics & KPIs (8 tools)

### 69. `create_share`
**Description:** Create a new file share  
**Parameters:**
- `name` (string, required) - Share name
- `file_ids` (array[string], required) - File UUIDs to share
- `description` (string, optional) - Share description
- `expires_at` (string, optional) - ISO date for expiry
- `max_downloads` (integer, optional) - Download limit
- `password` (string, optional) - Password protection

**Example:**
```json
{
  "tool": "create_share",
  "arguments": {
    "name": "Client Review Files",
    "file_ids": ["file-1", "file-2", "file-3"],
    "expires_at": "2024-12-31T23:59:59Z",
    "max_downloads": 10,
    "password": "review2024"
  }
}
```

### 70. `delete_share`
**Description:** Delete a share  
**Parameters:**
- `share_id` (string, required) - Share UUID

### 71. `get_login_info`
**Description:** Get current user login information  
**Parameters:** None  
**Returns:** Current user details

### 72. `get_system_status`
**Description:** Get Cway system connection status  
**Parameters:** None  
**Returns:** System health and connectivity

### 73. `get_temporal_dashboard`
**Description:** Get comprehensive temporal KPI dashboard  
**Parameters:**
- `analysis_period_days` (integer, optional, default: 90) - Days to analyze

**Returns:** Velocity metrics, stagnation analysis, activity trends

### 74. `get_stagnation_alerts`
**Description:** Get projects at risk of stagnation  
**Parameters:**
- `min_urgency_score` (integer, optional, default: 5) - Urgency threshold (1-10)

**Returns:** At-risk projects with urgency scores and recommendations

### 75. `analyze_project_velocity`
**Description:** Analyze velocity trends for a specific project  
**Parameters:**
- `project_id` (string, required) - Project UUID

**Returns:** Project velocity patterns and trend analysis

### 76. `get_kpi_dashboard`
**Description:** Get comprehensive KPI dashboard  
**Parameters:** None  
**Returns:** Health scores, critical projects, system-wide metrics

---

## AI Features (2 tools)

### 77. `analyze_artwork_ai`
*(Already documented in Artwork Operations - #37)*

### 78. `generate_project_summary_ai`
*(Already documented in Artwork Operations - #38)*

---

## System (4 tools)

### 79. `get_login_info`
*(Already documented in Analytics - #71)*

### 80. `get_system_status`
*(Already documented in Analytics - #72)*

Additional system operations integrated throughout other categories.

---

## Usage Patterns

### Common Workflows

#### 1. Create and Set Up a New Project
```
1. create_project → Get project_id
2. add_project_member → Add team members
3. create_artwork → Create artworks
4. upload_project_attachment → Add reference files
```

#### 2. Review and Approve Artwork
```
1. get_artworks_to_approve → Get pending artworks
2. get_artwork_preview → View artwork
3. get_artwork_comments → Read feedback
4. approve_artwork OR reject_artwork
```

#### 3. Share Files with External Users
```
1. search_media_center → Find files
2. create_share → Create share with expiry/password
3. Get share URL → Share with recipients
```

#### 4. Monitor Project Health
```
1. get_kpi_dashboard → System overview
2. get_stagnation_alerts → Find at-risk projects
3. analyze_project_velocity → Deep dive on specific project
```

---

## Integration Examples

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "cway": {
      "command": "python",
      "args": ["/path/to/cwayMCP/server/main.py"],
      "env": {
        "CWAY_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Python Client Example
```python
from mcp import Client

client = Client("cway")

# List all projects
projects = await client.call_tool("list_projects", {})

# Create new project
new_project = await client.call_tool("create_project", {
    "name": "Q4 Campaign",
    "description": "Marketing materials"
})

# Add team member
await client.call_tool("add_project_member", {
    "project_id": new_project["id"],
    "user_id": "user-123",
    "role": "MANAGER"
})
```

---

## Response Formats

All tools return JSON responses with consistent structure:

**Success Response:**
```json
{
  "data": { ... },
  "success": true,
  "message": "Operation completed successfully"
}
```

**Error Response:**
```json
{
  "error": "Error description",
  "success": false,
  "message": "Operation failed"
}
```

---

## Rate Limits & Best Practices

1. **Batch Operations:** Use array parameters when available (e.g., `close_projects`, `download_artworks`)
2. **Pagination:** Use pagination for large datasets (projects, users, media)
3. **Search First:** Use search tools before listing all items
4. **Cache Results:** Cache frequently accessed data like categories, brands
5. **Error Handling:** Always check `success` field in responses

---

## Version History

- **v1.0 (Phase 2.3):** 80 tools, 31% GraphQL coverage
- **v0.9 (Phase 2.2):** 70 tools, 27% GraphQL coverage
- **v0.8 (Phase 2.1):** 56 tools, 22% GraphQL coverage
- **v0.7 (Phase 1):** 49 tools, 19% GraphQL coverage

---

## See Also

- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [Next Steps Roadmap](NEXT_STEPS_ROADMAP.md) - Future enhancements
- [Session Summary](SESSION_SUMMARY_PHASE_2_3.md) - Latest changes
- [OAuth2 Guide](OAUTH2_QUICKSTART.md) - Authentication setup
