"""Extended tests for domain entities to improve coverage."""

from datetime import datetime
from typing import Optional
import pytest

from src.domain.entities import (
    Project, User, Artwork, ProjectState,
    TemporalMetadata, RevisionStatus
)


class TestTemporalMetadata:
    """Test TemporalMetadata class."""
    
    def test_temporal_metadata_creation(self) -> None:
        """Test creating temporal metadata."""
        created = datetime.now()
        updated = datetime.now()
        
        metadata = TemporalMetadata(
            created_at=created,
            updated_at=updated,
            version=1
        )
        
        assert metadata.created_at == created
        assert metadata.updated_at == updated
        assert metadata.version == 1
        assert metadata.activity_count == 0
        
    def test_update_activity(self) -> None:
        """Test updating activity tracking."""
        metadata = TemporalMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # First activity
        metadata.update_activity()
        assert metadata.activity_count == 1
        assert metadata.first_activity_at is not None
        assert metadata.last_activity_at is not None
        
        # Second activity
        timestamp = datetime(2024, 1, 15, 10, 0, 0)
        metadata.update_activity(timestamp)
        assert metadata.activity_count == 2
        assert metadata.last_activity_at == timestamp


class TestProjectExtended:
    """Extended tests for Project entity."""
    
    def test_project_with_temporal_metadata(self) -> None:
        """Test project with temporal metadata."""
        created = datetime.now()
        project = Project(
            id="proj-123",
            name="Test Project",
            created_at=created,
            updated_at=created
        )
        
        # Temporal metadata should be auto-created
        assert project.temporal_metadata is not None
        assert project.temporal_metadata.created_at == created
        
    def test_project_add_activity(self) -> None:
        """Test adding activity to project."""
        project = Project(
            id="proj-123",
            name="Test Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        project.add_activity(
            "status_change",
            "Project status changed",
            user_id="user-123"
        )
        
        assert len(project.activity_log) == 1
        assert project.activity_log[0]["type"] == "status_change"
        assert project.activity_log[0]["user_id"] == "user-123"
        
    def test_project_update_progress(self) -> None:
        """Test updating project progress."""
        project = Project(
            id="proj-123",
            name="Test Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        project.update_progress(50.0, user_id="user-123")
        
        assert project.completion_percentage == 50.0
        assert len(project.activity_log) == 1
        assert project.activity_log[0]["type"] == "progress_update"
        
    def test_project_progress_clamping(self) -> None:
        """Test that progress is clamped to 0-100."""
        project = Project(
            id="proj-123",
            name="Test Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test upper bound
        project.update_progress(150.0)
        assert project.completion_percentage == 100.0
        
        # Test lower bound
        project.update_progress(-10.0)
        assert project.completion_percentage == 0.0
        
    def test_project_all_valid_statuses(self) -> None:
        """Test all valid project statuses."""
        valid_statuses = [
            "ACTIVE", "INACTIVE", "COMPLETED", "CANCELLED",
            "PLANNED", "IN_PROGRESS", "DELIVERED", "ARCHIVED"
        ]
        
        for status in valid_statuses:
            project = Project(
                id=f"proj-{status}",
                name="Test Project",
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert project.status == status
            
    def test_project_with_all_fields(self) -> None:
        """Test creating project with all fields."""
        project = Project(
            id="proj-full",
            name="Full Project",
            description="A complete project",
            status="ACTIVE",
            state=ProjectState.ACTIVE,
            completion_percentage=75.0,
            milestone_count=10,
            completed_milestones=7,
            start_date="2024-01-01",
            end_date="2024-12-31",
            tags=["urgent", "client"],
            priority="HIGH",
            owner_id="user-123",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert project.completion_percentage == 75.0
        assert project.milestone_count == 10
        assert len(project.tags) == 2
        assert project.priority == "HIGH"


class TestArtwork:
    """Test Artwork entity."""
    
    def test_artwork_creation(self) -> None:
        """Test creating an artwork."""
        artwork = Artwork(
            id="art-123",
            name="Test Artwork",
            project_id="proj-123",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert artwork.id == "art-123"
        assert artwork.name == "Test Artwork"
        assert artwork.project_id == "proj-123"
        assert artwork.status == "DRAFT"
        assert artwork.current_version == 1
        
    def test_artwork_with_file_info(self) -> None:
        """Test artwork with file information."""
        artwork = Artwork(
            id="art-123",
            name="Logo",
            project_id="proj-123",
            file_path="/path/to/logo.png",
            file_size=1024,
            file_format="PNG",
            dimensions={"width": 1920, "height": 1080},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert artwork.file_path == "/path/to/logo.png"
        assert artwork.file_size == 1024
        assert artwork.file_format == "PNG"
        assert artwork.dimensions["width"] == 1920
        
    def test_artwork_add_revision(self) -> None:
        """Test adding revision to artwork."""
        artwork = Artwork(
            id="art-123",
            name="Test Artwork",
            project_id="proj-123",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        initial_version = artwork.current_version
        artwork.add_revision("rev-1", user_id="user-123")
        
        assert len(artwork.revisions) == 1
        assert artwork.revisions[0] == "rev-1"
        assert artwork.current_revision_id == "rev-1"
        assert artwork.current_version == initial_version + 1
        assert len(artwork.activity_log) == 1
        assert artwork.activity_log[0]["type"] == "revision_created"
        
    def test_artwork_approve_revision(self) -> None:
        """Test approving an artwork revision."""
        artwork = Artwork(
            id="art-123",
            name="Test Artwork",
            project_id="proj-123",
            current_version=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        artwork.pending_revisions.append("rev-1")
        artwork.approve_revision("rev-1", user_id="user-123")
        
        assert "rev-1" not in artwork.pending_revisions
        assert "rev-1" in artwork.approved_revisions
        assert len(artwork.activity_log) == 1
        assert artwork.activity_log[0]["type"] == "revision_approved"
        
    def test_artwork_with_collaborators(self) -> None:
        """Test artwork with collaborators."""
        artwork = Artwork(
            id="art-123",
            name="Collaborative Artwork",
            project_id="proj-123",
            collaborators=["user-1", "user-2", "user-3"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert len(artwork.collaborators) == 3
        assert "user-1" in artwork.collaborators
            
    def test_artwork_status_validation(self) -> None:
        """Test artwork status validation."""
        valid_statuses = ["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED", "PUBLISHED", "ARCHIVED"]
        
        for status in valid_statuses:
            artwork = Artwork(
                id=f"art-{status}",
                name="Test",
                project_id="proj-123",
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert artwork.status == status
            
        # Invalid status
        with pytest.raises(ValueError, match="Status must be one of"):
            Artwork(
                id="art-invalid",
                name="Test",
                project_id="proj-123",
                status="INVALID_STATUS",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )


class TestUser:
    """Test User entity extended functionality."""
    
    def test_user_with_all_fields(self) -> None:
        """Test user with all optional fields."""
        user = User(
            id="user-123",
            email="test@example.com",
            name="Test User",
            role="admin",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == "admin"
        
    def test_user_all_roles(self) -> None:
        """Test all valid user roles."""
        valid_roles = ["admin", "user", "viewer"]
        
        for role in valid_roles:
            user = User(
                id=f"user-{role}",
                email=f"{role}@example.com",
                role=role,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert user.role == role
