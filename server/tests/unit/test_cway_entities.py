"""Tests for Cway-specific domain entities."""

from datetime import datetime, date
import pytest

from src.domain.cway_entities import (
    CwayUser, PlannerProject, Organisation, OrganisationMembership, UserTeam,
    ProjectState, parse_cway_date, parse_cway_datetime
)


class TestProjectState:
    """Test ProjectState enumeration."""
    
    def test_project_state_values(self) -> None:
        """Test all project state values."""
        assert ProjectState.IN_PROGRESS.value == "IN_PROGRESS"
        assert ProjectState.COMPLETED.value == "COMPLETED" 
        assert ProjectState.CANCELLED.value == "CANCELLED"
        assert ProjectState.PLANNED.value == "PLANNED"


class TestCwayUser:
    """Test CwayUser entity."""
    
    def test_cway_user_creation(self) -> None:
        """Test creating a CwayUser with required fields."""
        user = CwayUser(
            id="user-123",
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            firstName="John",
            lastName="Doe"
        )
        
        assert user.id == "user-123"
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.username == "johndoe"
        assert user.firstName == "John"
        assert user.lastName == "Doe"
        assert user.enabled is True  # Default
        assert user.avatar is False  # Default
        assert user.acceptedTerms is False  # Default
        assert user.earlyAccessProgram is False  # Default
        assert user.isSSO is False  # Default
        assert user.createdAt is None  # Default
        
    def test_cway_user_creation_with_all_fields(self) -> None:
        """Test creating a CwayUser with all fields."""
        timestamp = 1640995200  # 2022-01-01
        
        user = CwayUser(
            id="user-123",
            name="Jane Smith",
            email="jane@example.com",
            username="janesmith",
            firstName="Jane",
            lastName="Smith",
            enabled=False,
            avatar=True,
            acceptedTerms=True,
            earlyAccessProgram=True,
            isSSO=True,
            createdAt=timestamp
        )
        
        assert user.enabled is False
        assert user.avatar is True
        assert user.acceptedTerms is True
        assert user.earlyAccessProgram is True
        assert user.isSSO is True
        assert user.createdAt == timestamp
        
    def test_cway_user_validation_empty_id(self) -> None:
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            CwayUser(
                id="",
                name="John Doe",
                email="john@example.com",
                username="johndoe",
                firstName="John",
                lastName="Doe"
            )
            
    def test_cway_user_validation_empty_email(self) -> None:
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="User email cannot be empty"):
            CwayUser(
                id="user-123",
                name="John Doe",
                email="",
                username="johndoe",
                firstName="John",
                lastName="Doe"
            )
            
    def test_cway_user_full_name_with_first_last(self) -> None:
        """Test full_name property with firstName and lastName."""
        user = CwayUser(
            id="user-123",
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            firstName="John",
            lastName="Doe"
        )
        
        assert user.full_name == "John Doe"
        
    def test_cway_user_full_name_with_first_only(self) -> None:
        """Test full_name property with only firstName."""
        user = CwayUser(
            id="user-123",
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            firstName="John",
            lastName=""
        )
        
        assert user.full_name == "John Doe"
        
    def test_cway_user_full_name_fallback_to_name(self) -> None:
        """Test full_name property falls back to name."""
        user = CwayUser(
            id="user-123",
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            firstName="",
            lastName=""
        )
        
        assert user.full_name == "John Doe"
        
    def test_cway_user_full_name_fallback_to_username(self) -> None:
        """Test full_name property falls back to username."""
        user = CwayUser(
            id="user-123",
            name="",
            email="john@example.com",
            username="johndoe",
            firstName="",
            lastName=""
        )
        
        assert user.full_name == "johndoe"


class TestPlannerProject:
    """Test PlannerProject entity."""
    
    def test_planner_project_creation(self) -> None:
        """Test creating a PlannerProject with required fields."""
        project = PlannerProject(
            id="proj-123",
            name="Test Project",
            state=ProjectState.IN_PROGRESS
        )
        
        assert project.id == "proj-123"
        assert project.name == "Test Project"
        assert project.state == ProjectState.IN_PROGRESS
        assert project.percentageDone == 0.0  # Default
        assert project.startDate is None  # Default
        assert project.endDate is None  # Default
        
    def test_planner_project_creation_with_all_fields(self) -> None:
        """Test creating a PlannerProject with all fields."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        project = PlannerProject(
            id="proj-123",
            name="Full Project",
            state=ProjectState.COMPLETED,
            percentageDone=100.0,
            startDate=start_date,
            endDate=end_date
        )
        
        assert project.percentageDone == 100.0
        assert project.startDate == start_date
        assert project.endDate == end_date
        assert project.state == ProjectState.COMPLETED
        
    def test_planner_project_validation_empty_id(self) -> None:
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Project ID cannot be empty"):
            PlannerProject(
                id="",
                name="Test Project",
                state=ProjectState.IN_PROGRESS
            )
            
    def test_planner_project_validation_empty_name(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            PlannerProject(
                id="proj-123",
                name="",
                state=ProjectState.IN_PROGRESS
            )
            
    def test_planner_project_is_active(self) -> None:
        """Test is_active property."""
        active_project = PlannerProject(
            id="proj-1",
            name="Active Project",
            state=ProjectState.IN_PROGRESS
        )
        
        completed_project = PlannerProject(
            id="proj-2",
            name="Completed Project",
            state=ProjectState.COMPLETED
        )
        
        assert active_project.is_active is True
        assert completed_project.is_active is False
        
    def test_planner_project_is_completed(self) -> None:
        """Test is_completed property."""
        active_project = PlannerProject(
            id="proj-1",
            name="Active Project",
            state=ProjectState.IN_PROGRESS
        )
        
        completed_project = PlannerProject(
            id="proj-2",
            name="Completed Project",
            state=ProjectState.COMPLETED
        )
        
        assert active_project.is_completed is False
        assert completed_project.is_completed is True


class TestOrganisation:
    """Test Organisation entity."""
    
    def test_organisation_creation(self) -> None:
        """Test creating an Organisation with required fields."""
        org = Organisation(
            id="org-123",
            name="Test Org"
        )
        
        assert org.id == "org-123"
        assert org.name == "Test Org"
        assert org.description is None  # Default
        assert org.active is True  # Default
        assert org.numberOfUsers == 0  # Default
        assert org.numberOfFullUsers == 0  # Default
        assert org.numberOfLimitedUsers == 0  # Default
        assert org.canAddArtwork is True  # Default
        assert org.canAddUser is True  # Default
        
    def test_organisation_creation_with_all_fields(self) -> None:
        """Test creating an Organisation with all fields."""
        org = Organisation(
            id="org-123",
            name="Full Org",
            description="A complete organization",
            active=False,
            numberOfUsers=50,
            numberOfFullUsers=30,
            numberOfLimitedUsers=20,
            canAddArtwork=False,
            canAddUser=False
        )
        
        assert org.description == "A complete organization"
        assert org.active is False
        assert org.numberOfUsers == 50
        assert org.numberOfFullUsers == 30
        assert org.numberOfLimitedUsers == 20
        assert org.canAddArtwork is False
        assert org.canAddUser is False
        
    def test_organisation_validation_empty_id(self) -> None:
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Organisation ID cannot be empty"):
            Organisation(id="", name="Test Org")
            
    def test_organisation_validation_empty_name(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Organisation name cannot be empty"):
            Organisation(id="org-123", name="")


class TestOrganisationMembership:
    """Test OrganisationMembership entity."""
    
    def test_organisation_membership_creation(self) -> None:
        """Test creating an OrganisationMembership."""
        membership = OrganisationMembership(
            organisationId="org-123",
            name="Test Org"
        )
        
        assert membership.organisationId == "org-123"
        assert membership.name == "Test Org"
        assert membership.permissionGroupId is None  # Default
        
    def test_organisation_membership_with_permission_group(self) -> None:
        """Test creating an OrganisationMembership with permission group."""
        membership = OrganisationMembership(
            organisationId="org-123",
            name="Test Org",
            permissionGroupId="perm-456"
        )
        
        assert membership.permissionGroupId == "perm-456"
        
    def test_organisation_membership_validation_empty_org_id(self) -> None:
        """Test that empty organisation ID raises ValueError."""
        with pytest.raises(ValueError, match="Organisation ID cannot be empty"):
            OrganisationMembership(organisationId="", name="Test Org")
            
    def test_organisation_membership_validation_empty_name(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Organisation name cannot be empty"):
            OrganisationMembership(organisationId="org-123", name="")


class TestUserTeam:
    """Test UserTeam entity."""
    
    def test_user_team_creation(self) -> None:
        """Test creating a UserTeam."""
        team = UserTeam(
            id="team-123",
            name="Test Team"
        )
        
        assert team.id == "team-123"
        assert team.name == "Test Team"
        assert team.description == ""  # Default
        
    def test_user_team_creation_with_description(self) -> None:
        """Test creating a UserTeam with description."""
        team = UserTeam(
            id="team-123",
            name="Test Team",
            description="A test team"
        )
        
        assert team.description == "A test team"
        
    def test_user_team_validation_empty_id(self) -> None:
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Team ID cannot be empty"):
            UserTeam(id="", name="Test Team")
            
    def test_user_team_validation_empty_name(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Team name cannot be empty"):
            UserTeam(id="team-123", name="")


class TestHelperFunctions:
    """Test helper functions for data conversion."""
    
    def test_parse_cway_date_valid(self) -> None:
        """Test parsing valid date strings."""
        result = parse_cway_date("2024-01-15")
        assert result == date(2024, 1, 15)
        
        result = parse_cway_date("2024-12-31T00:00:00")
        assert result == date(2024, 12, 31)
        
    def test_parse_cway_date_none(self) -> None:
        """Test parsing None returns None."""
        result = parse_cway_date(None)
        assert result is None
        
    def test_parse_cway_date_empty_string(self) -> None:
        """Test parsing empty string returns None."""
        result = parse_cway_date("")
        assert result is None
        
    def test_parse_cway_date_invalid(self) -> None:
        """Test parsing invalid date string returns None."""
        result = parse_cway_date("invalid-date")
        assert result is None
        
    def test_parse_cway_datetime_valid(self) -> None:
        """Test parsing valid datetime strings."""
        result = parse_cway_datetime("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)
        
    def test_parse_cway_datetime_with_z(self) -> None:
        """Test parsing datetime with Z timezone."""
        result = parse_cway_datetime("2024-01-15T10:30:00Z")
        expected = datetime(2024, 1, 15, 10, 30, 0, tzinfo=datetime.fromisoformat("2024-01-15T10:30:00+00:00").tzinfo)
        assert result == expected
        
    def test_parse_cway_datetime_none(self) -> None:
        """Test parsing None returns None."""
        result = parse_cway_datetime(None)
        assert result is None
        
    def test_parse_cway_datetime_empty_string(self) -> None:
        """Test parsing empty string returns None."""
        result = parse_cway_datetime("")
        assert result is None
        
    def test_parse_cway_datetime_invalid(self) -> None:
        """Test parsing invalid datetime string returns None."""
        result = parse_cway_datetime("invalid-datetime")
        assert result is None