"""Repository module - Clean Architecture data access layer.

All repositories follow Single Responsibility Principle and extend BaseRepository.
"""

from .base_repository import BaseRepository
from .user_repository import UserRepository
from .project_repository import ProjectRepository
from .artwork_repository import ArtworkRepository
from .media_repository import MediaRepository
from .share_repository import ShareRepository
from .team_repository import TeamRepository
from .search_repository import SearchRepository
from .category_repository import CategoryRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProjectRepository",
    "ArtworkRepository",
    "MediaRepository",
    "ShareRepository",
    "TeamRepository",
    "SearchRepository",
    "CategoryRepository",
]
