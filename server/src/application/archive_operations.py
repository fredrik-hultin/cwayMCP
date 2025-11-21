"""ARCHIVE operation handlers with prepare-confirm pattern.

Following SOLID principles - single responsibility for archiving operations.
"""
from typing import Any, Dict
from ..infrastructure.confirmation_token_manager import ConfirmationTokenManager


async def prepare_archive_artwork(
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to archive artwork - shows preview and returns confirmation token.
    
    Args:
        artwork_id: Artwork UUID
        artwork_repo: Artwork repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'preview' and 'confirmation_token'
    """
    # Get artwork details
    artwork = await artwork_repo.get_artwork(artwork_id)
    
    # Build preview
    preview = {
        "artwork_name": artwork.name,
        "status": artwork.status,
        "project_id": artwork.project_id,
        "project_name": artwork.project_name,
        "created_at": artwork.created_at,
        "warnings": []
    }
    
    # Check for risks
    if artwork.status == "IN_PROGRESS":
        preview["warnings"].append(
            "⚠️ Artwork is still in progress"
        )
    
    if artwork.status == "PENDING_APPROVAL":
        preview["warnings"].append(
            "⚠️ Artwork is pending approval"
        )
    
    # Generate confirmation token
    token_id = token_manager.create_token(
        operation="archive_artwork",
        arguments={"artwork_id": artwork_id},
        preview_data=preview
    )
    
    return {
        "preview": preview,
        "confirmation_token": token_id
    }


async def confirm_archive_artwork(
    confirmation_token: str,
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork archival.
    
    Args:
        confirmation_token: Token from prepare_archive_artwork
        artwork_id: Artwork UUID (must match token)
        artwork_repo: Artwork repository instance
        token_manager: Confirmation token manager
        
    Returns:
        Dictionary with 'success' and 'artwork_id'
        
    Raises:
        ValueError: If token is invalid or expired
    """
    # Validate token
    if not token_manager.validate_token(
        confirmation_token,
        "archive_artwork",
        {"artwork_id": artwork_id}
    ):
        raise ValueError("Invalid or expired confirmation token")
    
    # Get token
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    
    # Execute archival
    await artwork_repo.archive_artwork(artwork_id)
    
    # Invalidate token (single-use)
    token_manager.invalidate_token(confirmation_token)
    
    return {
        "success": True,
        "artwork_id": artwork_id
    }
