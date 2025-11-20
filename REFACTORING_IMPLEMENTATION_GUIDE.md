# Repository Refactoring Implementation Guide

## Status: STARTED
- ✅ Created `src/infrastructure/repositories/` directory
- ✅ Created `base_repository.py` (60 lines)
- ⏳ Next: Split remaining repositories

## Quick Reference: Method Distribution

### From CwayProjectRepository (2,671 lines) → 8 Repositories

#### 1. ProjectRepository (~450 lines)
**Methods (19)**:
- list_projects
- get_project
- create_project  
- update_project
- delete_projects
- close_projects
- reopen_projects
- get_active_projects
- get_completed_projects
- search_projects
- get_project_status_summary
- compare_projects
- get_project_history
- get_monthly_project_trends
- get_project_members
- add_project_member
- remove_project_member
- update_project_member_role
- get_project_by_id

**Lines**: 24-680 approx in cway_repositories.py

---

#### 2. UserRepository (~300 lines)
**Methods (13)**:
- list_users
- get_users_page
- search_users
- get_user
- create_user
- update_user_name
- delete_user
- find_user_by_email
- get_login_info
- get_user_activity (from line 2303)
- get_user_roles (from line 2180)

**Lines**: 680-980 approx + team methods

---

#### 3. ArtworkRepository (~650 lines)
**Methods (26)**:
- create_artwork
- approve_artwork
- reject_artwork
- get_artworks_to_approve
- get_artworks_to_upload
- get_my_artworks
- get_artwork
- get_artwork_preview
- download_artworks
- get_artwork_history
- analyze_artwork_ai
- submit_artwork_for_review
- request_artwork_changes
- get_artwork_comments
- add_artwork_comment
- get_artwork_versions
- restore_artwork_version
- assign_artwork (line 1951)
- duplicate_artwork (line 1981)
- archive_artwork (line 2009)
- unarchive_artwork (line 2033)
- search_artworks (line 2233)
- bulk_update_artwork_status (line 2333)
- generate_project_summary_ai
- get_project_comments
- add_project_comment

**Lines**: 980-1950, plus 1951-2055, 2233-2270, 2333-2363

---

#### 4. MediaRepository (~550 lines)
**Methods (16)**:
- get_folder_tree
- get_folder
- get_folder_items
- search_media_center
- get_media_center_stats
- download_folder_contents
- download_project_media
- get_file
- get_project_attachments
- upload_project_attachment
- create_folder (line 1321)
- rename_file (line 1357)
- rename_folder (line 1387)
- move_files (line 1415)
- delete_file (line 1436)
- delete_folder (line 1446)

**Lines**: Methods scattered, needs extraction

---

#### 5. TeamRepository (~350 lines)
**Methods (6)**:
- get_team_members (line 2057)
- add_team_member (line 2089)
- remove_team_member (line 2122)
- update_team_member_role (line 2147)
- get_user_roles (line 2180)
- transfer_project_ownership (line 2201)

**Lines**: 2057-2232

---

#### 6. CategoryRepository (~350 lines)
**Methods (9)**:
- get_categories
- create_category
- get_brands
- create_brand
- get_print_specifications
- create_print_specification

Plus from CwayCategoryRepository:
- All CwayCategoryRepository methods (already separate)

**Lines**: Spread across file + CwayCategoryRepository class

---

#### 7. ShareRepository (~250 lines)
**Methods (4)**:
- find_shares (line 2057)
- get_share (line 2088)
- create_share (line 2118)
- delete_share

**Lines**: 2057-2200 approx

---

#### 8. SearchRepository (~200 lines)
**Methods (4)**:
- search_artworks (line 2233)
- get_project_timeline (line 2272)
- get_user_activity (line 2303)
- bulk_update_artwork_status (line 2333)

**Lines**: 2233-2363

---

## Implementation Steps (Detailed)

### Step 1: Create Empty Repository Files
```bash
cd server/src/infrastructure/repositories
touch project_repository.py
touch user_repository.py
touch artwork_repository.py
touch media_repository.py
touch team_repository.py
touch category_repository.py
touch share_repository.py
touch search_repository.py
touch __init__.py
```

### Step 2: Template for Each Repository

```python
"""
[Domain] Repository - Handles [domain] operations.

Single Responsibility: [Domain] data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class [Domain]Repository(BaseRepository):
    """Repository for [domain] operations."""
    
    # Copy methods from cway_repositories.py here
    # Update self.graphql_client.execute_query → self._execute_query
    # Update self.graphql_client.execute_mutation → self._execute_mutation
```

### Step 3: Update __init__.py

```python
"""
Repositories module - exports all domain repositories.

Usage:
    from src.infrastructure.repositories import (
        ProjectRepository,
        UserRepository,
        ArtworkRepository,
        MediaRepository,
        TeamRepository,
        CategoryRepository,
        ShareRepository,
        SearchRepository
    )
"""

from .base_repository import BaseRepository
from .project_repository import ProjectRepository
from .user_repository import UserRepository
from .artwork_repository import ArtworkRepository
from .media_repository import MediaRepository
from .team_repository import TeamRepository
from .category_repository import CategoryRepository
from .share_repository import ShareRepository
from .search_repository import SearchRepository

__all__ = [
    'BaseRepository',
    'ProjectRepository',
    'UserRepository',
    'ArtworkRepository',
    'MediaRepository',
    'TeamRepository',
    'CategoryRepository',
    'ShareRepository',
    'SearchRepository',
]
```

### Step 4: Update cway_mcp_server.py Imports

**Before**:
```python
from src.infrastructure.cway_repositories import CwayProjectRepository, CwayCategoryRepository
```

**After**:
```python
from src.infrastructure.repositories import (
    ProjectRepository,
    UserRepository,
    ArtworkRepository,
    MediaRepository,
    TeamRepository,
    CategoryRepository,
    ShareRepository,
    SearchRepository
)
```

**Update initialization**:
```python
def __init__(self):
    # Initialize all repositories
    graphql_client = CwayGraphQLClient(...)
    
    self.project_repo = ProjectRepository(graphql_client)
    self.user_repo = UserRepository(graphql_client)
    self.artwork_repo = ArtworkRepository(graphql_client)
    self.media_repo = MediaRepository(graphql_client)
    self.team_repo = TeamRepository(graphql_client)
    self.category_repo = CategoryRepository(graphql_client)
    self.share_repo = ShareRepository(graphql_client)
    self.search_repo = SearchRepository(graphql_client)
```

**Update method calls throughout**:
- `self.project_repo.list_projects()` instead of `self.project_repo.list_projects()`
- Route to appropriate repository based on tool domain

### Step 5: Update Test Imports

Search and replace in all test files:
```python
# Before
from src.infrastructure.cway_repositories import CwayProjectRepository

# After  
from src.infrastructure.repositories import ProjectRepository, ArtworkRepository, ...
```

### Step 6: Verification Commands

```bash
# Run tests after each repository split
pytest tests/unit/ --ignore=tests/unit/test_infrastructure_repositories.py -q

# Check file sizes
find src/infrastructure/repositories/ -name "*.py" -exec wc -l {} +

# All should be < 700 lines
```

---

## Execution Order (Safest)

1. **SearchRepository** (smallest, 200 lines) - Test waters
2. **TeamRepository** (300 lines) - Build confidence  
3. **CategoryRepository** (350 lines) - Include existing class
4. **UserRepository** (300 lines) - Straightforward
5. **ShareRepository** (250 lines) - Simple
6. **MediaRepository** (550 lines) - More complex
7. **ProjectRepository** (450 lines) - Critical path
8. **ArtworkRepository** (650 lines) - Largest, most complex

After each:
- Run tests
- Commit with message: "refactor: split [Domain]Repository from monolith"
- Push to backup

---

## Rollback Strategy

If tests fail at any step:
```bash
git reset --hard HEAD~1  # Undo last commit
# Fix issue
# Re-attempt split
```

---

## Success Criteria

- ✅ All 379 tests passing
- ✅ All repository files < 700 lines
- ✅ base_repository.py provides common functionality
- ✅ __init__.py exports all repositories
- ✅ No code duplication
- ✅ Clear separation of concerns by domain

---

## Time Estimate Per Repository

| Repository | Lines | Methods | Time | Risk |
|------------|-------|---------|------|------|
| Search | 200 | 4 | 30 min | Low |
| Team | 300 | 6 | 45 min | Low |
| Category | 350 | 9 | 60 min | Low |
| User | 300 | 13 | 45 min | Low |
| Share | 250 | 4 | 30 min | Low |
| Media | 550 | 16 | 90 min | Medium |
| Project | 450 | 19 | 90 min | Medium |
| Artwork | 650 | 26 | 120 min | High |
| **Total** | **3,050** | **97** | **~9 hours** | **Medium** |

Add 2 hours for:
- Updating imports (1 hour)
- Testing & verification (1 hour)

**Total Estimate**: 11 hours

---

## Next Session Plan

1. Continue with SearchRepository (easiest)
2. Implement TeamRepository
3. Test both
4. Commit & push
5. Continue with remaining repositories
