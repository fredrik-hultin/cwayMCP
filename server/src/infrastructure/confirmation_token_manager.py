"""Confirmation Token Manager for dangerous operations.

Implements prepare-confirm pattern to protect users from accidental destructive actions.
Tokens expire after 5 minutes and are single-use.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ConfirmationToken:
    """Token for confirming a dangerous operation."""
    
    token_id: str
    operation: str  # Operation name (e.g., "delete_file")
    arguments: Dict[str, Any]  # Operation arguments
    preview_data: Dict[str, Any]  # What will happen
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(init=False)
    
    def __post_init__(self):
        """Set expiration time to 5 minutes from creation."""
        self.expires_at = self.created_at + timedelta(minutes=5)
    
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def matches(self, operation: str, arguments: Optional[Dict[str, Any]] = None) -> bool:
        """Check if token matches operation and arguments.
        
        Args:
            operation: Operation name to match
            arguments: Optional arguments to match (checks only keys present in arguments)
            
        Returns:
            True if operation matches and all provided arguments match
        """
        if self.operation != operation:
            return False
        
        # If no arguments provided, just match operation
        if arguments is None:
            return True
        
        # Check that all provided arguments match stored arguments
        for key, value in arguments.items():
            if key not in self.arguments or self.arguments[key] != value:
                return False
        
        return True


class ConfirmationTokenManager:
    """Manager for confirmation tokens with automatic expiry."""
    
    def __init__(self):
        """Initialize token manager with empty token store."""
        self._tokens: Dict[str, ConfirmationToken] = {}
        logger.info("✅ ConfirmationTokenManager initialized")
    
    def create_token(
        self,
        operation: str,
        arguments: Dict[str, Any],
        preview_data: Dict[str, Any]
    ) -> str:
        """Create a new confirmation token.
        
        Args:
            operation: Name of the operation requiring confirmation
            arguments: Operation arguments
            preview_data: Preview of what will happen
            
        Returns:
            Token ID string
        """
        token_id = str(uuid4())
        token = ConfirmationToken(
            token_id=token_id,
            operation=operation,
            arguments=arguments,
            preview_data=preview_data
        )
        
        self._tokens[token_id] = token
        logger.info(f"🎫 Created confirmation token for {operation}: {token_id}")
        
        # Cleanup expired tokens while we're here
        self.cleanup_expired()
        
        return token_id
    
    def validate_token(
        self,
        token_id: str,
        operation: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Validate that token exists, matches operation, and is not expired.
        
        Args:
            token_id: Token ID to validate
            operation: Expected operation name
            arguments: Expected operation arguments
            
        Returns:
            True if token is valid
        """
        token = self._tokens.get(token_id)
        
        if token is None:
            logger.warning(f"❌ Token not found: {token_id}")
            return False
        
        if token.is_expired():
            logger.warning(f"⏰ Token expired: {token_id}")
            self.invalidate_token(token_id)
            return False
        
        if not token.matches(operation, arguments):
            logger.warning(f"❌ Token mismatch for {token_id}: expected {operation}, got {token.operation}")
            return False
        
        logger.info(f"✅ Token validated: {token_id} for {operation}")
        return True
    
    def get_token(self, token_id: str) -> Optional[ConfirmationToken]:
        """Get token by ID.
        
        Args:
            token_id: Token ID
            
        Returns:
            ConfirmationToken if found, None otherwise
        """
        return self._tokens.get(token_id)
    
    def invalidate_token(self, token_id: str) -> None:
        """Invalidate (delete) a token.
        
        Tokens are single-use and should be invalidated after confirmation.
        
        Args:
            token_id: Token ID to invalidate
        """
        if token_id in self._tokens:
            operation = self._tokens[token_id].operation
            del self._tokens[token_id]
            logger.info(f"🗑️ Invalidated token {token_id} for {operation}")
        else:
            logger.debug(f"Token {token_id} not found (already invalidated?)")
    
    def cleanup_expired(self) -> int:
        """Remove all expired tokens from memory.
        
        Returns:
            Number of tokens cleaned up
        """
        expired_tokens = [
            token_id
            for token_id, token in self._tokens.items()
            if token.is_expired()
        ]
        
        for token_id in expired_tokens:
            operation = self._tokens[token_id].operation
            del self._tokens[token_id]
            logger.debug(f"🧹 Cleaned up expired token {token_id} for {operation}")
        
        if expired_tokens:
            logger.info(f"🧹 Cleaned up {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get token manager statistics.
        
        Returns:
            Dictionary with token counts and statistics
        """
        total = len(self._tokens)
        expired = sum(1 for token in self._tokens.values() if token.is_expired())
        active = total - expired
        
        operations = {}
        for token in self._tokens.values():
            operations[token.operation] = operations.get(token.operation, 0) + 1
        
        return {
            "total_tokens": total,
            "active_tokens": active,
            "expired_tokens": expired,
            "operations": operations
        }
