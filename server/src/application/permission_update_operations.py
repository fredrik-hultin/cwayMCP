"""Permission/role and update/move operations with prepare-confirm pattern.

SOLID: Single responsibility for permission management and data modifications.
"""
from typing import Any, Dict, List, Optional
from ..infrastructure.confirmation_token_manager import ConfirmationTokenManager


# PERMISSION/ROLE OPERATIONS

async def prepare_add_member(
    project_id: str,
    user_id: str,
    role: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to add member to project."""
    preview = {
        "project_id": project_id,
        "user_id": user_id,
        "role": role,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="add_member",
        arguments={"project_id": project_id, "user_id": user_id, "role": role},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_add_member(
    confirmation_token: str,
    project_id: str,
    user_id: str,
    role: str,
    team_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute adding member."""
    if not token_manager.validate_token(confirmation_token, "add_member", {"project_id": project_id, "user_id": user_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await team_repo.add_member(project_id, user_id, role)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_remove_member(
    project_id: str,
    user_id: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to remove member from project."""
    preview = {
        "project_id": project_id,
        "user_id": user_id,
        "warnings": ["⚠️ User will lose access to this project"]
    }
    
    token_id = token_manager.create_token(
        operation="remove_member",
        arguments={"project_id": project_id, "user_id": user_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_remove_member(
    confirmation_token: str,
    project_id: str,
    user_id: str,
    team_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute removing member."""
    if not token_manager.validate_token(confirmation_token, "remove_member", {"project_id": project_id, "user_id": user_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await team_repo.remove_member(project_id, user_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_update_member_role(
    project_id: str,
    user_id: str,
    new_role: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to update member role."""
    preview = {
        "project_id": project_id,
        "user_id": user_id,
        "new_role": new_role,
        "warnings": []
    }
    
    if new_role == "OWNER":
        preview["warnings"].append("⚠️ Granting OWNER role gives full control")
    
    token_id = token_manager.create_token(
        operation="update_member_role",
        arguments={"project_id": project_id, "user_id": user_id, "role": new_role},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_update_member_role(
    confirmation_token: str,
    project_id: str,
    user_id: str,
    role: str,
    team_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute role update."""
    if not token_manager.validate_token(confirmation_token, "update_member_role", {"project_id": project_id, "user_id": user_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await team_repo.update_role(project_id, user_id, role)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_transfer_ownership(
    project_id: str,
    new_owner_id: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to transfer project ownership."""
    preview = {
        "project_id": project_id,
        "new_owner_id": new_owner_id,
        "warnings": [
            "⚠️ Ownership transfer is irreversible",
            "⚠️ You will lose owner privileges"
        ]
    }
    
    token_id = token_manager.create_token(
        operation="transfer_ownership",
        arguments={"project_id": project_id, "new_owner_id": new_owner_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_transfer_ownership(
    confirmation_token: str,
    project_id: str,
    new_owner_id: str,
    team_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute ownership transfer."""
    if not token_manager.validate_token(confirmation_token, "transfer_ownership", {"project_id": project_id, "new_owner_id": new_owner_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await team_repo.transfer_ownership(project_id, new_owner_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_set_permissions(
    usernames: List[str],
    permission_group_id: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to set user permissions."""
    preview = {
        "user_count": len(usernames),
        "usernames": usernames,
        "permission_group_id": permission_group_id,
        "warnings": []
    }
    
    if len(usernames) > 10:
        preview["warnings"].append(f"⚠️ Updating permissions for {len(usernames)} users")
    
    token_id = token_manager.create_token(
        operation="set_permissions",
        arguments={"usernames": usernames, "permission_group_id": permission_group_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_set_permissions(
    confirmation_token: str,
    usernames: List[str],
    permission_group_id: str,
    user_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute permission update."""
    if not token_manager.validate_token(confirmation_token, "set_permissions", {"permission_group_id": permission_group_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await user_repo.set_permissions(usernames, permission_group_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "updated_count": len(usernames)}


# UPDATE/MOVE OPERATIONS

async def prepare_update_project(
    project_id: str,
    name: Optional[str],
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to update project."""
    preview = {
        "project_id": project_id,
        "new_name": name or "(unchanged)",
        "new_description": description or "(unchanged)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="update_project",
        arguments={"project_id": project_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_update_project(
    confirmation_token: str,
    project_id: str,
    name: Optional[str],
    description: Optional[str],
    project_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute project update."""
    if not token_manager.validate_token(confirmation_token, "update_project", {"project_id": project_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await project_repo.update_project(project_id, name, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_update_user_name(
    username: str,
    first_name: Optional[str],
    last_name: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to update user name."""
    preview = {
        "username": username,
        "first_name": first_name or "(unchanged)",
        "last_name": last_name or "(unchanged)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="update_user_name",
        arguments={"username": username},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_update_user_name(
    confirmation_token: str,
    username: str,
    first_name: Optional[str],
    last_name: Optional[str],
    user_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute user name update."""
    if not token_manager.validate_token(confirmation_token, "update_user_name", {"username": username}):
        raise ValueError("Invalid or expired confirmation token")
    
    await user_repo.update_name(username, first_name, last_name)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_rename_file(
    file_id: str,
    new_name: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to rename file."""
    preview = {
        "file_id": file_id,
        "new_name": new_name,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="rename_file",
        arguments={"file_id": file_id, "new_name": new_name},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_rename_file(
    confirmation_token: str,
    file_id: str,
    new_name: str,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute file rename."""
    if not token_manager.validate_token(confirmation_token, "rename_file", {"file_id": file_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await media_repo.rename_file(file_id, new_name)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_rename_folder(
    folder_id: str,
    new_name: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to rename folder."""
    preview = {
        "folder_id": folder_id,
        "new_name": new_name,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="rename_folder",
        arguments={"folder_id": folder_id, "new_name": new_name},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_rename_folder(
    confirmation_token: str,
    folder_id: str,
    new_name: str,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute folder rename."""
    if not token_manager.validate_token(confirmation_token, "rename_folder", {"folder_id": folder_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await media_repo.rename_folder(folder_id, new_name)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_move_files(
    file_ids: List[str],
    target_folder_id: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to move files."""
    preview = {
        "file_count": len(file_ids),
        "target_folder_id": target_folder_id,
        "warnings": []
    }
    
    if len(file_ids) > 20:
        preview["warnings"].append(f"⚠️ Moving {len(file_ids)} files at once")
    
    token_id = token_manager.create_token(
        operation="move_files",
        arguments={"file_ids": file_ids, "target_folder_id": target_folder_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_move_files(
    confirmation_token: str,
    file_ids: List[str],
    target_folder_id: str,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute file move."""
    if not token_manager.validate_token(confirmation_token, "move_files", {"target_folder_id": target_folder_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await media_repo.move_files(file_ids, target_folder_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "moved_count": len(file_ids)}


async def prepare_assign_artwork(
    artwork_id: str,
    user_id: str,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to assign artwork."""
    preview = {
        "artwork_id": artwork_id,
        "assignee_id": user_id,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="assign_artwork",
        arguments={"artwork_id": artwork_id, "user_id": user_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_assign_artwork(
    confirmation_token: str,
    artwork_id: str,
    user_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork assignment."""
    if not token_manager.validate_token(confirmation_token, "assign_artwork", {"artwork_id": artwork_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    await artwork_repo.assign(artwork_id, user_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True}


async def prepare_duplicate_artwork(
    artwork_id: str,
    new_name: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to duplicate artwork."""
    preview = {
        "source_artwork_id": artwork_id,
        "new_name": new_name or "(auto-generated)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="duplicate_artwork",
        arguments={"artwork_id": artwork_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_duplicate_artwork(
    confirmation_token: str,
    artwork_id: str,
    new_name: Optional[str],
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork duplication."""
    if not token_manager.validate_token(confirmation_token, "duplicate_artwork", {"artwork_id": artwork_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await artwork_repo.duplicate_artwork(artwork_id, new_name)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "new_artwork_id": result["id"]}
