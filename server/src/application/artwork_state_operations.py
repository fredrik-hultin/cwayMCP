"""Artwork state change operations with prepare-confirm pattern.

SOLID: Single responsibility for artwork workflow state transitions.
"""
from typing import Any, Dict, List
from ..infrastructure.confirmation_token_manager import ConfirmationTokenManager


async def prepare_approve_artwork(
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to approve artwork."""
    artwork = await artwork_repo.get_artwork(artwork_id)
    
    preview = {
        "artwork_name": artwork.name,
        "current_status": artwork.status,
        "new_status": "APPROVED",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="approve_artwork",
        arguments={"artwork_id": artwork_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_approve_artwork(
    confirmation_token: str,
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork approval."""
    if not token_manager.validate_token(confirmation_token, "approve_artwork", {"artwork_id": artwork_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    
    await artwork_repo.approve_artwork(artwork_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": artwork_id}


async def prepare_reject_artwork(
    artwork_id: str,
    reason: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to reject artwork."""
    artwork = await artwork_repo.get_artwork(artwork_id)
    
    preview = {
        "artwork_name": artwork.name,
        "current_status": artwork.status,
        "new_status": "REJECTED",
        "reason": reason,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="reject_artwork",
        arguments={"artwork_id": artwork_id, "reason": reason},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_reject_artwork(
    confirmation_token: str,
    artwork_id: str,
    reason: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork rejection."""
    if not token_manager.validate_token(confirmation_token, "reject_artwork", {"artwork_id": artwork_id, "reason": reason}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    reason = token.arguments["reason"]
    
    await artwork_repo.reject_artwork(artwork_id, reason)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": artwork_id}


async def prepare_submit_artwork(
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to submit artwork for review."""
    artwork = await artwork_repo.get_artwork(artwork_id)
    
    preview = {
        "artwork_name": artwork.name,
        "current_status": artwork.status,
        "new_status": "PENDING_APPROVAL",
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="submit_artwork",
        arguments={"artwork_id": artwork_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_submit_artwork(
    confirmation_token: str,
    artwork_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute artwork submission."""
    if not token_manager.validate_token(confirmation_token, "submit_artwork", {"artwork_id": artwork_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    
    await artwork_repo.submit_for_review(artwork_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": artwork_id}


async def prepare_request_changes(
    artwork_id: str,
    reason: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to request changes on artwork."""
    artwork = await artwork_repo.get_artwork(artwork_id)
    
    preview = {
        "artwork_name": artwork.name,
        "reason": reason,
        "warnings": []
    }
    
    token_id = token_manager.create_token(
        operation="request_changes",
        arguments={"artwork_id": artwork_id, "reason": reason},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_request_changes(
    confirmation_token: str,
    artwork_id: str,
    reason: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute change request."""
    if not token_manager.validate_token(confirmation_token, "request_changes", {"artwork_id": artwork_id, "reason": reason}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    reason = token.arguments["reason"]
    
    await artwork_repo.request_changes(artwork_id, reason)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": artwork_id}


async def prepare_restore_version(
    artwork_id: str,
    version_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to restore artwork to previous version."""
    artwork = await artwork_repo.get_artwork(artwork_id)
    version = await artwork_repo.get_version(version_id)
    
    preview = {
        "artwork_name": artwork.name,
        "current_version": artwork.current_version,
        "restore_to_version": version.version_number,
        "version_created_at": version.created_at,
        "warnings": []
    }
    
    # Warn about losing newer versions
    if version.version_number < artwork.current_version:
        versions_lost = list(range(version.version_number + 1, artwork.current_version + 1))
        preview["warnings"].append(
            f"⚠️ Will lose version {' and '.join(map(str, versions_lost))}"
        )
    
    token_id = token_manager.create_token(
        operation="restore_version",
        arguments={"artwork_id": artwork_id, "version_id": version_id},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_restore_version(
    confirmation_token: str,
    artwork_id: str,
    version_id: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute version restoration."""
    if not token_manager.validate_token(confirmation_token, "restore_version", {"artwork_id": artwork_id, "version_id": version_id}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_id = token.arguments["artwork_id"]
    version_id = token.arguments["version_id"]
    
    await artwork_repo.restore_version(artwork_id, version_id)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "artwork_id": artwork_id, "version_id": version_id}


async def prepare_bulk_update_status(
    artwork_ids: List[str],
    new_status: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Prepare to bulk update artwork statuses."""
    artworks = await artwork_repo.get_artworks(artwork_ids)
    
    preview = {
        "artwork_count": len(artworks),
        "new_status": new_status,
        "artworks": [
            {
                "id": a.id,
                "name": a.name,
                "current_status": a.status
            }
            for a in artworks
        ],
        "warnings": []
    }
    
    if len(artworks) > 10:
        preview["warnings"].append(
            f"⚠️ Updating {len(artworks)} artworks at once"
        )
    
    token_id = token_manager.create_token(
        operation="bulk_update_status",
        arguments={"artwork_ids": artwork_ids, "status": new_status},
        preview_data=preview
    )
    
    return {"preview": preview, "confirmation_token": token_id}


async def confirm_bulk_update_status(
    confirmation_token: str,
    artwork_ids: List[str],
    status: str,
    artwork_repo: Any,
    token_manager: ConfirmationTokenManager
) -> Dict[str, Any]:
    """Confirm and execute bulk status update."""
    if not token_manager.validate_token(confirmation_token, "bulk_update_status", {"artwork_ids": artwork_ids, "status": status}):
        raise ValueError("Invalid or expired confirmation token")
    
    token = token_manager.get_token(confirmation_token)
    artwork_ids = token.arguments["artwork_ids"]
    status = token.arguments["status"]
    
    await artwork_repo.bulk_update_status(artwork_ids, status)
    token_manager.invalidate_token(confirmation_token)
    
    return {"success": True, "updated_count": len(artwork_ids)}
