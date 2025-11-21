"""Unit tests for CREATE operation handlers."""
import pytest
from unittest.mock import AsyncMock, Mock

from src.application.create_operations import (
    prepare_create_project,
    confirm_create_project,
    prepare_create_user,
    confirm_create_user,
    prepare_create_artwork,
    confirm_create_artwork,
    prepare_create_folder,
    confirm_create_folder,
    prepare_create_category,
    confirm_create_category,
    prepare_create_brand,
    confirm_create_brand,
    prepare_create_print_spec,
    confirm_create_print_spec,
    prepare_create_share,
    confirm_create_share
)
from src.infrastructure.confirmation_token_manager import ConfirmationTokenManager


@pytest.fixture
def token_manager():
    return ConfirmationTokenManager()


class TestCreateProject:
    """Tests for create_project operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_project(self, token_manager):
        """Test preparing to create project."""
        result = await prepare_create_project(
            name="New Brand Campaign",
            description="Q1 2024 campaign",
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "New Brand Campaign"
        assert result["preview"]["description"] == "Q1 2024 campaign"
        assert "confirmation_token" in result
    
    @pytest.mark.asyncio
    async def test_confirm_create_project(self, token_manager):
        """Test confirming project creation."""
        mock_repo = Mock()
        mock_repo.create_project = AsyncMock(return_value={"id": "proj-123"})
        
        token_id = token_manager.create_token(
            operation="create_project",
            arguments={"name": "Test Project", "description": "Test"},
            preview_data={}
        )
        
        result = await confirm_create_project(
            confirmation_token=token_id,
            name="Test Project",
            description="Test",
            project_repo=mock_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        assert result["project_id"] == "proj-123"


class TestCreateUser:
    """Tests for create_user operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_user(self, token_manager):
        """Test preparing to create user."""
        result = await prepare_create_user(
            email="john@example.com",
            username="john.doe",
            first_name="John",
            last_name="Doe",
            token_manager=token_manager
        )
        
        assert result["preview"]["email"] == "john@example.com"
        assert result["preview"]["username"] == "john.doe"
    
    @pytest.mark.asyncio
    async def test_confirm_create_user(self, token_manager):
        """Test confirming user creation."""
        mock_repo = Mock()
        mock_repo.create_user = AsyncMock(return_value={"id": "user-123"})
        
        token_id = token_manager.create_token(
            operation="create_user",
            arguments={"email": "test@test.com", "username": "test"},
            preview_data={}
        )
        
        result = await confirm_create_user(
            confirmation_token=token_id,
            email="test@test.com",
            username="test",
            first_name=None,
            last_name=None,
            user_repo=mock_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True


class TestCreateArtwork:
    """Tests for create_artwork operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_artwork(self, token_manager):
        """Test preparing to create artwork."""
        result = await prepare_create_artwork(
            project_id="proj-123",
            name="Logo Design",
            description="Primary logo",
            token_manager=token_manager
        )
        
        assert result["preview"]["project_id"] == "proj-123"
        assert result["preview"]["name"] == "Logo Design"


class TestCreateFolder:
    """Tests for create_folder operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_folder(self, token_manager):
        """Test preparing to create folder."""
        result = await prepare_create_folder(
            name="Assets",
            parent_folder_id="parent-123",
            description="Project assets",
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "Assets"
        assert result["preview"]["parent_folder_id"] == "parent-123"


class TestCreateCategory:
    """Tests for create_category operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_category(self, token_manager):
        """Test preparing to create category."""
        result = await prepare_create_category(
            name="Marketing Materials",
            description="All marketing content",
            color="#FF5733",
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "Marketing Materials"
        assert result["preview"]["color"] == "#FF5733"


class TestCreateBrand:
    """Tests for create_brand operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_brand(self, token_manager):
        """Test preparing to create brand."""
        result = await prepare_create_brand(
            name="Acme Corp",
            description="Corporate brand",
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "Acme Corp"


class TestCreatePrintSpec:
    """Tests for create_print_specification operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_print_spec(self, token_manager):
        """Test preparing to create print specification."""
        result = await prepare_create_print_spec(
            name="A4 Portrait",
            width=210,
            height=297,
            unit="mm",
            description="Standard A4",
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "A4 Portrait"
        assert result["preview"]["dimensions"] == "210x297 mm"


class TestCreateShare:
    """Tests for create_share operations."""
    
    @pytest.mark.asyncio
    async def test_prepare_create_share(self, token_manager):
        """Test preparing to create file share."""
        result = await prepare_create_share(
            name="Client Review",
            file_ids=["file-1", "file-2"],
            description="Files for client",
            password="secret123",
            max_downloads=10,
            token_manager=token_manager
        )
        
        assert result["preview"]["name"] == "Client Review"
        assert result["preview"]["file_count"] == 2
        assert result["preview"]["password_protected"] is True
        assert result["preview"]["max_downloads"] == 10
    
    @pytest.mark.asyncio
    async def test_confirm_create_share(self, token_manager):
        """Test confirming share creation."""
        mock_repo = Mock()
        mock_repo.create_share = AsyncMock(return_value={"id": "share-123", "url": "https://share.link"})
        
        token_id = token_manager.create_token(
            operation="create_share",
            arguments={"name": "Test", "file_ids": ["f1"]},
            preview_data={}
        )
        
        result = await confirm_create_share(
            confirmation_token=token_id,
            name="Test",
            file_ids=["f1"],
            description=None,
            password=None,
            max_downloads=None,
            expires_at=None,
            share_repo=mock_repo,
            token_manager=token_manager
        )
        
        assert result["success"] is True
        assert result["share_id"] == "share-123"
        assert result["share_url"] == "https://share.link"
