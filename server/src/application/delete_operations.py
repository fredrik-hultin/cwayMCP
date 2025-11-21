"""DELETE operation handlers with prepare-confirm pattern.

Following SOLID principles - this module has single responsibility:
handling all DELETE operations with safety confirmation.
"""
from typing import Any, Dict
from ..infrastructure.confirmation_token_manager import ConfirmationTokenManager


async def prepare_delete_file(
    file_id: str,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to delete a file - shows preview and returns confirmation token.
    
    Args:
        file_id: File UUID
        media_repo: Media repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'preview' and 'confirmation_token'
    """
    # Get file details
    file = await media_repo.get_file(file_id)
    
    # Build preview
    preview = {
        "file_name": file.name,
        "file_size": file.size,
        "file_type": file.content_type,
        "created_at": file.created_at,
        "warnings": []
    }
    
    # Check for risks
    if hasattr(file, 'is_shared') and file.is_shared:
        preview["warnings"].append("⚠️ File is currently shared")
    
    if hasattr(file, 'reference_count') and file.reference_count > 0:
        preview["warnings"].append(
            f"⚠️ Referenced by {file.reference_count} items"
        )
    
    # Generate confirmation token
    token_id = token_manager.create_token(
        operation="delete_file",
        arguments={"file_id": file_id},
        preview_data=preview
    )
    
    return {
        "preview": preview,
        "confirmation_token": token_id
    }


async def confirm_delete_file(
    confirmation_token: str,
    file_id: str,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute file deletion.
    
    Args:
        confirmation_token: Token from prepare_delete_file
        file_id: File UUID (must match token)
        media_repo: Media repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'success' and 'file_id'
        
    Raises:
        ValueError: If token is invalid or expired
    """
    # Validate token
    if not token_manager.validate_token(
        confirmation_token,
        "delete_file",
        {"file_id": file_id}
    ):
        raise ValueError("Invalid or expired confirmation token")
    
    # Get token to retrieve file_id
    token = token_manager.get_token(confirmation_token)
    file_id = token.arguments["file_id"]
    
    # Execute deletion
    await media_repo.delete_file(file_id)
    
    # Invalidate token (single-use)
    token_manager.invalidate_token(confirmation_token)
    
    return {
        "success": True,
        "file_id": file_id
    }


async def prepare_delete_folder(
    folder_id: str,
    force: bool,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to delete a folder - shows preview and returns confirmation token.
    
    Args:
        folder_id: Folder UUID
        force: Whether to force delete non-empty folder
        media_repo: Media repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'preview' and 'confirmation_token'
    """
    # Get folder details
    folder = await media_repo.get_folder(folder_id)
    
    # Build preview
    preview = {
        "folder_name": folder.name,
        "item_count": folder.item_count,
        "created_at": folder.created_at,
        "warnings": []
    }
    
    # Check for risks
    if folder.item_count > 0:
        if not force:
            preview["warnings"].append(
                f"⚠️ Folder contains {folder.item_count} items. Use force=true to delete."
            )
        else:
            preview["warnings"].append(
                f"🗑️ Will delete folder and all {folder.item_count} items inside"
            )
    
    # Generate confirmation token
    token_id = token_manager.create_token(
        operation="delete_folder",
        arguments={"folder_id": folder_id, "force": force},
        preview_data=preview
    )
    
    return {
        "preview": preview,
        "confirmation_token": token_id
    }


async def confirm_delete_folder(
    confirmation_token: str,
    folder_id: str,
    force: bool,
    media_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute folder deletion.
    
    Args:
        confirmation_token: Token from prepare_delete_folder
        folder_id: Folder UUID (must match token)
        force: Force delete flag (must match token)
        media_repo: Media repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'success' and 'folder_id'
        
    Raises:
        ValueError: If token is invalid or expired
    """
    # Validate token
    if not token_manager.validate_token(
        confirmation_token,
        "delete_folder",
        {"folder_id": folder_id, "force": force}
    ):
        raise ValueError("Invalid or expired confirmation token")
    
    # Get token
    token = token_manager.get_token(confirmation_token)
    folder_id = token.arguments["folder_id"]
    force = token.arguments["force"]
    
    # Execute deletion
    await media_repo.delete_folder(folder_id, force=force)
    
    # Invalidate token
    token_manager.invalidate_token(confirmation_token)
    
    return {
        "success": True,
        "folder_id": folder_id
    }


async def prepare_delete_share(
    share_id: str,
    share_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to delete a share - shows preview and returns confirmation token.
    
    Args:
        share_id: Share UUID
        share_repo: Share repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'preview' and 'confirmation_token'
    """
    # Get share details
    share = await share_repo.get_share(share_id)
    
    # Build preview
    preview = {
        "share_name": share.name,
        "file_count": share.file_count,
        "download_count": share.download_count,
        "created_at": share.created_at,
        "warnings": []
    }
    
    if share.download_count > 0:
        preview["warnings"].append(
            f"ℹ️ Share has been downloaded {share.download_count} times"
        )
    
    # Generate confirmation token
    token_id = token_manager.create_token(
        operation="delete_share",
        arguments={"share_id": share_id},
        preview_data=preview
    )
    
    return {
        "preview": preview,
        "confirmation_token": token_id
    }


async def confirm_delete_share(
    confirmation_token: str,
    share_id: str,
    share_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute share deletion.
    
    Args:
        confirmation_token: Token from prepare_delete_share
        share_id: Share UUID (must match token)
        share_repo: Share repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'success' and 'share_id'
        
    Raises:
        ValueError: If token is invalid or expired
    """
    # Validate token
    if not token_manager.validate_token(
        confirmation_token,
        "delete_share",
        {"share_id": share_id}
    ):
        raise ValueError("Invalid or expired confirmation token")
    
    # Get token
    token = token_manager.get_token(confirmation_token)
    share_id = token.arguments["share_id"]
    
    # Execute deletion
    await share_repo.delete_share(share_id)
    
    # Invalidate token
    token_manager.invalidate_token(confirmation_token)
    
    return {
        "success": True,
        "share_id": share_id
    }
