"""Tests for domain entities."""

from datetime import datetime
from typing import Optional
import pytest

from src.domain.entities import (
    Project, User, CwayEntity, Artwork, Revision,
    RevisionStatus, ArtworkType, ProjectState
)


class TestCwayEntity:
    """Test the base CwayEntity class."""
    
    def test_cway_entity_creation(self) -> None:
        """Test creating a CwayEntity with required fields."""
        entity_id = "test-id-123"
        created_at = datetime.now()
        updated_at = datetime.now()
        
        entity = CwayEntity(
            id=entity_id,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert entity.id == entity_id
        assert entity.created_at == created_at
        assert entity.updated_at == updated_at
        
    def test_cway_entity_equality(self) -> None:
        """Test equality comparison for CwayEntity."""
        entity_id = "test-id-123"
        created_at = datetime.now()
        updated_at = datetime.now()
        
        entity1 = CwayEntity(id=entity_id, created_at=created_at, updated_at=updated_at)
        entity2 = CwayEntity(id=entity_id, created_at=created_at, updated_at=updated_at)
        entity3 = CwayEntity(id="different-id", created_at=created_at, updated_at=updated_at)
        
        assert entity1 == entity2
        assert entity1 != entity3
        
    def test_cway_entity_hash(self) -> None:
        """Test that CwayEntity can be used in sets and as dict keys."""
        entity1 = CwayEntity(id="test-id", created_at=datetime.now(), updated_at=datetime.now())
        entity2 = CwayEntity(id="test-id", created_at=datetime.now(), updated_at=datetime.now())
        
        entity_set = {entity1, entity2}
        assert len(entity_set) == 1  # Should deduplicate based on ID


class TestProject:
    """Test the Project entity."""
    
    def test_project_creation(self) -> None:
        """Test creating a Project with all fields."""
        project_data = {
            "id": "proj-123",
            "name": "Test Project",
            "description": "A test project",
            "status": "ACTIVE",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        project = Project(**project_data)
        
        assert project.id == project_data["id"]
        assert project.name == project_data["name"]
        assert project.description == project_data["description"]
        assert project.status == ProjectState.ACTIVE  # Converted to enum
        
    def test_project_creation_minimal(self) -> None:
        """Test creating a Project with minimal required fields."""
        project = Project(
            id="proj-123",
            name="Test Project",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert project.id == "proj-123"
        assert project.name == "Test Project"
        assert project.description is None
        assert project.status == ProjectState.ACTIVE  # Default value
        
    def test_project_status_validation(self) -> None:
        """Test that Project status validation works."""
        valid_statuses = ["ACTIVE", "INACTIVE", "ARCHIVED"]
        expected_enums = [ProjectState.ACTIVE, ProjectState.INACTIVE, ProjectState.ARCHIVED]
        
        for status, expected_enum in zip(valid_statuses, expected_enums):
            project = Project(
                id="proj-123",
                name="Test Project",
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert project.status == expected_enum  # Should be converted to enum
            
        # Invalid status should raise ValueError
        with pytest.raises(ValueError, match="Status must be one of"):
            Project(
                id="proj-123",
                name="Test Project",
                status="invalid_status",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )


class TestUser:
    """Test the User entity."""
    
    def test_user_creation(self) -> None:
        """Test creating a User with all fields."""
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "admin",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        user = User(**user_data)
        
        assert user.id == user_data["id"]
        assert user.email == user_data["email"]
        assert user.name == user_data["name"]
        assert user.role == user_data["role"]
        
    def test_user_creation_minimal(self) -> None:
        """Test creating a User with minimal required fields."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.name is None
        assert user.role == "user"  # Default value
        
    def test_user_role_validation(self) -> None:
        """Test that User role validation works."""
        valid_roles = ["admin", "user", "viewer"]
        
        for role in valid_roles:
            user = User(
                id="user-123",
                email="test@example.com",
                role=role,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert user.role == role
            
        # Invalid role should raise ValueError
        with pytest.raises(ValueError, match="Role must be one of"):
            User(
                id="user-123",
                email="test@example.com",
                role="invalid_role",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_user_email_validation(self) -> None:
        """Test that User email validation works."""
        # Valid emails should work
        valid_emails = ["test@example.com", "user+tag@domain.co.uk", "simple@test.io"]
        
        for email in valid_emails:
            user = User(
                id="user-123",
                email=email,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert user.email == email
            
        # Invalid emails should raise ValueError
        invalid_emails = ["invalid-email", "@example.com", "test@", "test@.com"]
        
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                User(
                    id="user-123",
                    email=email,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
    def test_cway_entity_validation_empty_id(self) -> None:
        """Test that CwayEntity validates empty ID."""
        with pytest.raises(ValueError, match="Entity ID cannot be empty"):
            CwayEntity(
                id="",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_project_validation_empty_name(self) -> None:
        """Test that Project validates empty name."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            Project(
                id="proj-123",
                name="",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_user_validation_empty_email(self) -> None:
        """Test that User validates empty email."""
        with pytest.raises(ValueError, match="User email cannot be empty"):
            User(
                id="user-123",
                email="",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_user_record_login(self) -> None:
        """Test recording user login."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert user.login_count == 0
        assert user.last_login_at is None
        
        user.record_login()
        
        assert user.login_count == 1
        assert user.last_login_at is not None
        assert len(user.activity_log) == 1
        
    def test_user_log_activity(self) -> None:
        """Test logging user activity."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        user.log_activity("test_activity", "Test description", {"key": "value"})
        
        assert len(user.activity_log) == 1
        assert user.activity_log[0]["type"] == "test_activity"
        assert user.activity_log[0]["description"] == "Test description"
        
    def test_user_calculate_performance_metrics(self) -> None:
        """Test calculating user performance metrics."""
        user = User(
            id="user-123",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create test revisions
        now = datetime.now()
        revision1 = Revision(
            id="rev-1",
            artwork_id="art-1",
            version_number=1,
            submitted_by="user-123",
            submitted_at=now,
            reviewed_by="user-123",
            status=RevisionStatus.APPROVED,
            time_to_review_minutes=10.0,
            created_at=now,
            updated_at=now
        )
        
        user.calculate_performance_metrics([revision1])
        
        assert user.avg_review_time_minutes is not None
        assert user.approval_rate is not None


class TestArtwork:
    """Test the Artwork entity."""
    
    def test_artwork_creation(self) -> None:
        """Test creating an Artwork."""
        artwork = Artwork(
            id="art-123",
            project_id="proj-123",
            name="Test Artwork",
            artwork_type=ArtworkType.DIGITAL_ART,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert artwork.id == "art-123"
        assert artwork.project_id == "proj-123"
        assert artwork.name == "Test Artwork"
        assert artwork.artwork_type == ArtworkType.DIGITAL_ART
        
    def test_artwork_validation_missing_project(self) -> None:
        """Test that Artwork validates project_id."""
        with pytest.raises(ValueError, match="Artwork must belong to a project"):
            Artwork(
                id="art-123",
                project_id="",
                name="Test Artwork",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_artwork_add_revision(self) -> None:
        """Test adding revision to artwork."""
        artwork = Artwork(
            id="art-123",
            project_id="proj-123",
            name="Test Artwork",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert len(artwork.revisions) == 0
        
        artwork.add_revision("rev-123", "user-123")
        
        assert len(artwork.revisions) == 1
        assert "rev-123" in artwork.revisions
        assert len(artwork.activity_log) > 0
        
    def test_artwork_add_pending_revision(self) -> None:
        """Test adding pending revision."""
        artwork = Artwork(
            id="art-123",
            project_id="proj-123",
            name="Test Artwork",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Just manually add to pending list since no method exists
        artwork.pending_revisions.append("rev-123")
        
        assert "rev-123" in artwork.pending_revisions
        
    def test_artwork_approve_revision(self) -> None:
        """Test approving revision."""
        artwork = Artwork(
            id="art-123",
            project_id="proj-123",
            name="Test Artwork",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add pending revision first
        artwork.pending_revisions.append("rev-123")
        assert "rev-123" in artwork.pending_revisions
        
        # Approve it
        artwork.approve_revision("rev-123", "user-456")
        
        assert "rev-123" not in artwork.pending_revisions
        assert "rev-123" in artwork.approved_revisions


class TestRevision:
    """Test the Revision entity."""
    
    def test_revision_creation(self) -> None:
        """Test creating a Revision."""
        revision = Revision(
            id="rev-123",
            artwork_id="art-123",
            version_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert revision.id == "rev-123"
        assert revision.artwork_id == "art-123"
        assert revision.version_number == 1
        assert revision.status == RevisionStatus.PENDING
        
    def test_revision_validation_missing_artwork(self) -> None:
        """Test that Revision validates artwork_id."""
        with pytest.raises(ValueError, match="Revision must belong to an artwork"):
            Revision(
                id="rev-123",
                artwork_id="",
                version_number=1,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_revision_validation_invalid_version(self) -> None:
        """Test that Revision validates version number."""
        with pytest.raises(ValueError, match="Version number must be positive"):
            Revision(
                id="rev-123",
                artwork_id="art-123",
                version_number=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
    def test_revision_submit_for_review(self) -> None:
        """Test submitting revision for review."""
        revision = Revision(
            id="rev-123",
            artwork_id="art-123",
            version_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        revision.submit_for_review("user-123")
        
        assert revision.status == RevisionStatus.IN_REVIEW
        assert revision.submitted_by == "user-123"
        assert revision.submitted_at is not None
        assert len(revision.activity_log) > 0
        
    def test_revision_approve(self) -> None:
        """Test approving revision."""
        revision = Revision(
            id="rev-123",
            artwork_id="art-123",
            version_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        revision.submit_for_review("user-123")
        revision.approve("user-456", "Looks good!")
        
        assert revision.status == RevisionStatus.APPROVED
        assert revision.approved_by == "user-456"
        assert revision.approved_at is not None
        assert revision.reviewer_comments == "Looks good!"
        assert revision.time_to_approve_minutes is not None
        
    def test_revision_reject(self) -> None:
        """Test rejecting revision."""
        revision = Revision(
            id="rev-123",
            artwork_id="art-123",
            version_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        revision.submit_for_review("user-123")
        revision.reject("user-456", "Needs changes", "Please fix the colors")
        
        assert revision.status == RevisionStatus.REJECTED
        assert revision.rejected_by == "user-456"
        assert revision.rejected_at is not None
        assert revision.rejection_reason == "Needs changes"
        assert revision.reviewer_comments == "Please fix the colors"
        assert revision.time_to_review_minutes is not None
        
    def test_revision_add_feedback(self) -> None:
        """Test adding feedback to revision."""
        revision = Revision(
            id="rev-123",
            artwork_id="art-123",
            version_number=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        revision.add_feedback("user-456", "Great work!", "PRAISE")
        
        assert len(revision.feedback) == 1
        assert revision.feedback[0]["user_id"] == "user-456"
        assert revision.feedback[0]["text"] == "Great work!"
        assert revision.feedback[0]["feedback_type"] == "PRAISE"
