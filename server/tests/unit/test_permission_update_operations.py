"""Unit tests for permission/role and update/move operations."""
import pytest
from unittest.mock import AsyncMock, Mock

from src.application.permission_update_operations import (
    # Permission operations
    prepare_add_member,
    confirm_add_member,
    prepare_remove_member,
    confirm_remove_member,
    prepare_update_member_role,
    confirm_update_member_role,
    prepare_transfer_ownership,
    confirm_transfer_ownership,
    prepare_set_permissions,
    confirm_set_permissions,
    # Update operations
    prepare_update_project,
    confirm_update_project,
    prepare_update_user_name,
    confirm_update_user_name,
    prepare_rename_file,
    confirm_rename_file,
    prepare_rename_folder,
    confirm_rename_folder,
    prepare_move_files,
    confirm_move_files,
    prepare_assign_artwork,
    confirm_assign_artwork,
    prepare_duplicate_artwork,
    confirm_duplicate_artwork
)
from src.infrastructure.confirmation_token_manager import ConfirmationTokenManager


@pytest.fixture
def token_manager():
    return ConfirmationTokenManager()


# PERMISSION/ROLE OPERATIONS
class TestAddMember:
    @pytest.mark.asyncio
    async def test_prepare_add_member(self, token_manager):
        result = await prepare_add_member(
            project_id="proj-123",
            user_id="user-456",
            role="MEMBER",
            token_manager=token_manager
        )
        assert result["preview"]["role"] == "MEMBER"
        assert "confirmation_token" in result


class TestRemoveMember:
    @pytest.mark.asyncio
    async def test_prepare_remove_member(self, token_manager):
        result = await prepare_remove_member(
            project_id="proj-123",
            user_id="user-456",
            token_manager=token_manager
        )
        assert result["preview"]["user_id"] == "user-456"


class TestUpdateMemberRole:
    @pytest.mark.asyncio
    async def test_prepare_update_role(self, token_manager):
        result = await prepare_update_member_role(
            project_id="proj-123",
            user_id="user-456",
            new_role="MANAGER",
            token_manager=token_manager
        )
        assert result["preview"]["new_role"] == "MANAGER"


class TestTransferOwnership:
    @pytest.mark.asyncio
    async def test_prepare_transfer_ownership(self, token_manager):
        result = await prepare_transfer_ownership(
            project_id="proj-123",
            new_owner_id="user-999",
            token_manager=token_manager
        )
        assert result["preview"]["new_owner_id"] == "user-999"
        warnings = result["preview"]["warnings"]
        assert any("irreversible" in w.lower() for w in warnings)


class TestSetPermissions:
    @pytest.mark.asyncio
    async def test_prepare_set_permissions(self, token_manager):
        result = await prepare_set_permissions(
            usernames=["john", "jane"],
            permission_group_id="group-123",
            token_manager=token_manager
        )
        assert result["preview"]["user_count"] == 2
        assert result["preview"]["permission_group_id"] == "group-123"


# UPDATE/MOVE OPERATIONS
class TestUpdateProject:
    @pytest.mark.asyncio
    async def test_prepare_update_project(self, token_manager):
        result = await prepare_update_project(
            project_id="proj-123",
            name="New Name",
            description="New Desc",
            token_manager=token_manager
        )
        assert result["preview"]["new_name"] == "New Name"
    
    @pytest.mark.asyncio
    async def test_confirm_update_project(self, token_manager):
        mock_repo = Mock()
        mock_repo.update_project = AsyncMock(return_value={"id": "proj-123"})
        
        token_id = token_manager.create_token(
            operation="update_project",
            arguments={"project_id": "proj-123"},
            preview_data={}
        )
        
        result = await confirm_update_project(
            confirmation_token=token_id,
            project_id="proj-123",
            name="Test",
            description=None,
            project_repo=mock_repo,
            token_manager=token_manager
        )
        assert result["success"] is True


class TestUpdateUserName:
    @pytest.mark.asyncio
    async def test_prepare_update_user_name(self, token_manager):
        result = await prepare_update_user_name(
            username="john.doe",
            first_name="John",
            last_name="Doe",
            token_manager=token_manager
        )
        assert result["preview"]["first_name"] == "John"


class TestRenameFile:
    @pytest.mark.asyncio
    async def test_prepare_rename_file(self, token_manager):
        result = await prepare_rename_file(
            file_id="file-123",
            new_name="updated.pdf",
            token_manager=token_manager
        )
        assert result["preview"]["new_name"] == "updated.pdf"


class TestRenameFolder:
    @pytest.mark.asyncio
    async def test_prepare_rename_folder(self, token_manager):
        result = await prepare_rename_folder(
            folder_id="folder-123",
            new_name="New Folder",
            token_manager=token_manager
        )
        assert result["preview"]["new_name"] == "New Folder"


class TestMoveFiles:
    @pytest.mark.asyncio
    async def test_prepare_move_files(self, token_manager):
        result = await prepare_move_files(
            file_ids=["f1", "f2", "f3"],
            target_folder_id="folder-999",
            token_manager=token_manager
        )
        assert result["preview"]["file_count"] == 3
        assert result["preview"]["target_folder_id"] == "folder-999"


class TestAssignArtwork:
    @pytest.mark.asyncio
    async def test_prepare_assign_artwork(self, token_manager):
        result = await prepare_assign_artwork(
            artwork_id="art-123",
            user_id="user-456",
            token_manager=token_manager
        )
        assert result["preview"]["artwork_id"] == "art-123"
        assert result["preview"]["assignee_id"] == "user-456"


class TestDuplicateArtwork:
    @pytest.mark.asyncio
    async def test_prepare_duplicate_artwork(self, token_manager):
        result = await prepare_duplicate_artwork(
            artwork_id="art-123",
            new_name="Logo Copy",
            token_manager=token_manager
        )
        assert result["preview"]["source_artwork_id"] == "art-123"
        assert result["preview"]["new_name"] == "Logo Copy"
    
    @pytest.mark.asyncio
    async def test_confirm_duplicate_artwork(self, token_manager):
        mock_repo = Mock()
        mock_repo.duplicate_artwork = AsyncMock(return_value={"id": "art-999"})
        
        token_id = token_manager.create_token(
            operation="duplicate_artwork",
            arguments={"artwork_id": "art-123"},
            preview_data={}
        )
        
        result = await confirm_duplicate_artwork(
            confirmation_token=token_id,
            artwork_id="art-123",
            new_name="Copy",
            artwork_repo=mock_repo,
            token_manager=token_manager
        )
        assert result["success"] is True
        assert result["new_artwork_id"] == "art-999"
