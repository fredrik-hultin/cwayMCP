"""Tests for domain entities."""

from datetime import datetime
from typing import Optional
import pytest

from src.domain.entities import Project, User, CwayEntity


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
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        project = Project(**project_data)
        
        assert project.id == project_data["id"]
        assert project.name == project_data["name"]
        assert project.description == project_data["description"]
        assert project.status == project_data["status"]
        
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
        assert project.status == "active"  # Default value
        
    def test_project_status_validation(self) -> None:
        """Test that Project status validation works."""
        valid_statuses = ["active", "inactive", "archived"]
        
        for status in valid_statuses:
            project = Project(
                id="proj-123",
                name="Test Project",
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            assert project.status == status
            
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
