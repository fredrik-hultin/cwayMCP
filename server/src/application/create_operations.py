"""CREATE operation handlers with prepare-confirm pattern.

SOLID: Single responsibility for all creation operations.
All CREATE operations follow same pattern: preview inputs, confirm to create.
"""
from typing import Any, Dict, List, Optional
from ..infrastructure.confirmation_token_manager import ConfirmationTokenManager


# PROJECT CREATION
async def prepare_create_project(
    name: str,
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create project."""
    preview = {
        "name": name,
        "description": description or "(no description)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_project",
        arguments={"name": name, "description": description},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_project(
    confirmation_token: str,
    name: str,
    description: Optional[str],
    project_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute project creation."""
    if not token_manager.validate_token(confirmation_token, "create_project", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await project_repo.create_project(name, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "project_id": result["id"]}


# USER CREATION
async def prepare_create_user(
    email: str,
    username: str,
    first_name: Optional[str],
    last_name: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create user."""
    preview = {
        "email": email,
        "username": username,
        "first_name": first_name or "(not set)",
        "last_name": last_name or "(not set)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_user",
        arguments={"email": email, "username": username},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_user(
    confirmation_token: str,
    email: str,
    username: str,
    first_name: Optional[str],
    last_name: Optional[str],
    user_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute user creation."""
    if not token_manager.validate_token(confirmation_token, "create_user", {"email": email, "username": username}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await user_repo.create_user(email, username, first_name, last_name)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "user_id": result["id"]}


# ARTWORK CREATION
async def prepare_create_artwork(
    project_id: str,
    name: str,
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create artwork."""
    preview = {
        "project_id": project_id,
        "name": name,
        "description": description or "(no description)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_artwork",
        arguments={"project_id": project_id, "name": name},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_artwork(
    confirmation_token: str,
    project_id: str,
    name: str,
    description: Optional[str],
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork creation."""
    if not token_manager.validate_token(confirmation_token, "create_artwork", {"project_id": project_id, "name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await artwork_repo.create_artwork(project_id, name, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": result["id"]}


# FOLDER CREATION
async def prepare_create_folder(
    name: str,
    parent_folder_id: Optional[str],
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create folder."""
    preview = {
        "name": name,
        "parent_folder_id": parent_folder_id or "root",
        "description": description or "(no description)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_folder",
        arguments={"name": name, "parent_folder_id": parent_folder_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_folder(
    confirmation_token: str,
    name: str,
    parent_folder_id: Optional[str],
    description: Optional[str],
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute folder creation."""
    if not token_manager.validate_token(confirmation_token, "create_folder", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await media_repo.create_folder(name, parent_folder_id, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "folder_id": result["id"]}


# CATEGORY CREATION
async def prepare_create_category(
    name: str,
    description: Optional[str],
    color: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create category."""
    preview = {
        "name": name,
        "description": description or "(no description)",
        "color": color or "(default)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_category",
        arguments={"name": name},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_category(
    confirmation_token: str,
    name: str,
    description: Optional[str],
    color: Optional[str],
    category_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute category creation."""
    if not token_manager.validate_token(confirmation_token, "create_category", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await category_repo.create_category(name, description, color)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "category_id": result["id"]}


# BRAND CREATION
async def prepare_create_brand(
    name: str,
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create brand."""
    preview = {
        "name": name,
        "description": description or "(no description)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_brand",
        arguments={"name": name},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_brand(
    confirmation_token: str,
    name: str,
    description: Optional[str],
    category_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute brand creation."""
    if not token_manager.validate_token(confirmation_token, "create_brand", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await category_repo.create_brand(name, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "brand_id": result["id"]}


# PRINT SPEC CREATION
async def prepare_create_print_spec(
    name: str,
    width: float,
    height: float,
    unit: str,
    description: Optional[str],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create print specification."""
    preview = {
        "name": name,
        "dimensions": f"{width}x{height} {unit}",
        "description": description or "(no description)",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="create_print_spec",
        arguments={"name": name, "width": width, "height": height, "unit": unit},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_print_spec(
    confirmation_token: str,
    name: str,
    width: float,
    height: float,
    unit: str,
    description: Optional[str],
    category_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute print spec creation."""
    if not token_manager.validate_token(confirmation_token, "create_print_spec", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await category_repo.create_print_spec(name, width, height, unit, description)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "print_spec_id": result["id"]}


# SHARE CREATION
async def prepare_create_share(
    name: str,
    file_ids: List[str],
    description: Optional[str],
    password: Optional[str],
    max_downloads: Optional[int],
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to create file share."""
    preview = {
        "name": name,
        "file_count": len(file_ids),
        "description": description or "(no description)",
        "password_protected": password is not None,
        "max_downloads": max_downloads or "unlimited",
        "warnings": []
    }
    
    if len(file_ids) > 20:
        preview["warnings"].append(f"⚠️ Sharing {len(file_ids)} files at once")
    
    token_id = token_manager.create_token(
        operation="create_share",
        arguments={"name": name, "file_ids": file_ids},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_create_share(
    confirmation_token: str,
    name: str,
    file_ids: List[str],
    description: Optional[str],
    password: Optional[str],
    max_downloads: Optional[int],
    expires_at: Optional[str],
    share_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute share creation."""
    if not token_manager.validate_token(confirmation_token, "create_share", {"name": name}):
        raise ValueError("Invalid or expired confirmation token")
    
    result = await share_repo.create_share(name, file_ids, description, password, max_downloads, expires_at)
    token_manager.invalidate_token(confirmation_token)
    
    return {
        "success": True,
        "share_id": result["id"],
        "share_url": result["url"]
    }
