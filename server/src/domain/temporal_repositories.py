"""Temporal repository interfaces for artwork and revision management."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from .entities import Project, User, Artwork, Revision


class ArtworkRepository(ABC):
    """Repository interface for artwork entities with temporal capabilities."""
    
    @abstractmethod
    async def get_all_artworks(self) -> List[Artwork]:
        """Get all artworks."""
        pass
    
    @abstractmethod
    async def get_artwork_by_id(self, artwork_id: str) -> Optional[Artwork]:
        """Get artwork by ID."""
        pass
    
    @abstractmethod
    async def get_artworks_by_project(self, project_id: str) -> List[Artwork]:
        """Get all artworks for a specific project."""
        pass
    
    @abstractmethod
    async def get_artworks_by_user(self, user_id: str) -> List[Artwork]:
        """Get all artworks created by a specific user."""
        pass
    
    @abstractmethod
    async def get_artworks_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Artwork]:
        """Get artworks created within a date range."""
        pass
    
    @abstractmethod
    async def get_artworks_by_status(self, status: str) -> List[Artwork]:
        """Get artworks by status."""
        pass
    
    @abstractmethod
    async def create_artwork(self, artwork: Artwork) -> Artwork:
        """Create a new artwork."""
        pass
    
    @abstractmethod
    async def update_artwork(self, artwork: Artwork) -> Artwork:
        """Update an existing artwork."""
        pass
    
    @abstractmethod
    async def delete_artwork(self, artwork_id: str) -> bool:
        """Delete an artwork."""
        pass


class RevisionRepository(ABC):
    """Repository interface for revision entities with temporal capabilities."""
    
    @abstractmethod
    async def get_all_revisions(self) -> List[Revision]:
        """Get all revisions."""
        pass
    
    @abstractmethod
    async def get_revision_by_id(self, revision_id: str) -> Optional[Revision]:
        """Get revision by ID."""
        pass
    
    @abstractmethod
    async def get_revisions_by_artwork(self, artwork_id: str) -> List[Revision]:
        """Get all revisions for a specific artwork."""
        pass
    
    @abstractmethod
    async def get_revisions_by_user(self, user_id: str, role: str = "submitted") -> List[Revision]:
        """Get revisions by user (submitted, reviewed, approved, etc.)."""
        pass
    
    @abstractmethod
    async def get_revisions_by_status(self, status: str) -> List[Revision]:
        """Get revisions by status."""
        pass
    
    @abstractmethod
    async def get_revisions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Revision]:
        """Get revisions within a date range."""
        pass
    
    @abstractmethod
    async def get_pending_revisions(self, user_id: Optional[str] = None) -> List[Revision]:
        """Get pending revisions, optionally filtered by reviewer."""
        pass
    
    @abstractmethod
    async def get_revision_timeline(self, artwork_id: str) -> List[Revision]:
        """Get complete revision timeline for an artwork."""
        pass
    
    @abstractmethod
    async def create_revision(self, revision: Revision) -> Revision:
        """Create a new revision."""
        pass
    
    @abstractmethod
    async def update_revision(self, revision: Revision) -> Revision:
        """Update an existing revision."""
        pass
    
    @abstractmethod
    async def delete_revision(self, revision_id: str) -> bool:
        """Delete a revision."""
        pass


class TemporalAnalyticsRepository(ABC):
    """Repository interface for temporal analytics and insights."""
    
    @abstractmethod
    async def get_project_activity_timeline(self, project_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get activity timeline for a project."""
        pass
    
    @abstractmethod
    async def get_user_activity_timeline(self, user_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get activity timeline for a user."""
        pass
    
    @abstractmethod
    async def get_artwork_lifecycle_metrics(self, artwork_id: str) -> Dict[str, Any]:
        """Get lifecycle metrics for an artwork."""
        pass
    
    @abstractmethod
    async def get_revision_velocity_metrics(self, project_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get revision velocity metrics."""
        pass
    
    @abstractmethod
    async def get_approval_time_metrics(self, user_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get approval time metrics."""
        pass
    
    @abstractmethod
    async def get_productivity_trends(self, entity_type: str, entity_id: str, days: int = 90) -> Dict[str, Any]:
        """Get productivity trends for projects, users, or teams."""
        pass
    
    @abstractmethod
    async def get_bottleneck_analysis(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze workflow bottlenecks."""
        pass
    
    @abstractmethod
    async def get_collaboration_patterns(self, project_id: str) -> Dict[str, Any]:
        """Analyze collaboration patterns in a project."""
        pass
    
    @abstractmethod
    async def get_quality_metrics(self, project_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get quality metrics (approval rates, revision counts, etc.)."""
        pass
    
    @abstractmethod
    async def get_workload_distribution(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Get workload distribution across team members."""
        pass


class TemporalQueryRepository(ABC):
    """Repository interface for complex temporal queries."""
    
    @abstractmethod
    async def find_stagnant_projects(self, days_threshold: int = 30) -> List[Project]:
        """Find projects with no activity for specified days."""
        pass
    
    @abstractmethod
    async def find_overdue_revisions(self, days_threshold: int = 7) -> List[Revision]:
        """Find revisions pending approval beyond threshold."""
        pass
    
    @abstractmethod
    async def find_high_velocity_periods(self, entity_type: str, entity_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Find periods of high activity/velocity."""
        pass
    
    @abstractmethod
    async def find_idle_periods(self, entity_type: str, entity_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Find periods of low/no activity."""
        pass
    
    @abstractmethod
    async def find_similar_projects(self, project_id: str, similarity_criteria: List[str]) -> List[Project]:
        """Find projects with similar temporal patterns."""
        pass
    
    @abstractmethod
    async def predict_completion_time(self, entity_type: str, entity_id: str) -> Optional[datetime]:
        """Predict completion time based on historical patterns."""
        pass
    
    @abstractmethod
    async def get_seasonal_patterns(self, entity_type: str, entity_id: str, years: int = 2) -> Dict[str, Any]:
        """Analyze seasonal patterns in activity."""
        pass
    
    @abstractmethod
    async def get_performance_benchmarks(self, entity_type: str, metrics: List[str]) -> Dict[str, Any]:
        """Get performance benchmarks across similar entities."""
        pass
    
    @abstractmethod
    async def get_risk_indicators(self, project_id: str) -> List[Dict[str, Any]]:
        """Get risk indicators for project health."""
        pass
    
    @abstractmethod
    async def get_optimization_suggestions(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Get optimization suggestions based on temporal analysis."""
        pass
