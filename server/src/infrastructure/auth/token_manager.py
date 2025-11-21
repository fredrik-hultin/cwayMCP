"""Token lifecycle manager with automatic refresh."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from threading import Lock

from .token_store import TokenStore, TokenStoreError
from .entra_auth import EntraIDAuthenticator, EntraAuthError

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages token lifecycle with automatic refresh."""
    
    def __init__(
        self,
        token_store: TokenStore,
        authenticator: EntraIDAuthenticator,
        refresh_threshold_minutes: int = 5,
    ):
        """
        Initialize token manager.
        
        Args:
            token_store: Token storage instance
            authenticator: Entra ID authenticator for token refresh
            refresh_threshold_minutes: Refresh tokens if expiring within this many minutes
        """
        self.token_store = token_store
        self.authenticator = authenticator
        self.refresh_threshold = timedelta(minutes=refresh_threshold_minutes)
        
        # Thread-safe refresh lock per user
        self._refresh_locks: dict[str, Lock] = {}
        self._locks_lock = Lock()  # Lock for the locks dict itself
        
        logger.info(f"TokenManager initialized (refresh threshold: {refresh_threshold_minutes}m)")
    
    def _get_user_lock(self, username: str) -> Lock:
        """Get or create refresh lock for user (thread-safe)."""
        with self._locks_lock:
            if username not in self._refresh_locks:
                self._refresh_locks[username] = Lock()
            return self._refresh_locks[username]
    
    async def get_valid_token(self, username: str) -> str:
        """
        Get valid access token for user, refreshing if necessary.
        
        This is the main method to use - it handles all token lifecycle:
        - Returns cached token if valid
        - Refreshes if expiring soon
        - Raises exception if no tokens or refresh fails
        
        Args:
            username: User's email/username
            
        Returns:
            Valid Cway JWT access token
            
        Raises:
            TokenManagerError: If no tokens exist or refresh fails
        """
        # Thread-safe token refresh
        lock = self._get_user_lock(username)
        
        with lock:
            # Get stored tokens
            token_data = self.token_store.get_tokens(username)
            
            if not token_data:
                raise TokenManagerError(
                    f"No tokens found for {username}. Please login first."
                )
            
            # Check if token needs refresh
            try:
                expires_at = datetime.fromisoformat(token_data["expires_at"])
                needs_refresh = datetime.now() + self.refresh_threshold >= expires_at
            except (KeyError, ValueError) as e:
                logger.error(f"Invalid token expiry data for {username}: {e}")
                raise TokenManagerError(f"Corrupted token data: {e}")
            
            if not needs_refresh:
                # Token is still valid
                logger.debug(f"Using cached token for {username} (expires: {expires_at})")
                return token_data["access_token"]
            
            # Token needs refresh
            logger.info(f"Token for {username} expires at {expires_at}, refreshing...")
            
            # Refresh token (async call)
            try:
                new_tokens = await self.authenticator.refresh_cway_token(
                    token_data["refresh_token"]
                )
            except EntraAuthError as e:
                logger.error(f"Token refresh failed for {username}: {e}")
                # Delete invalid tokens
                self.token_store.delete_tokens(username)
                raise TokenManagerError(f"Token refresh failed: {e}. Please login again.")
            
            # Save new tokens
            try:
                self.token_store.save_tokens(
                    username=username,
                    access_token=new_tokens["access_token"],
                    refresh_token=new_tokens["refresh_token"],
                    expires_in=new_tokens["expires_in"],
                )
            except TokenStoreError as e:
                logger.error(f"Failed to save refreshed tokens for {username}: {e}")
                raise TokenManagerError(f"Failed to save tokens: {e}")
            
            logger.info(f"Successfully refreshed token for {username}")
            return new_tokens["access_token"]
    
    def is_user_authenticated(self, username: str) -> bool:
        """
        Check if user has valid authentication.
        
        Args:
            username: User's email/username
            
        Returns:
            True if user has valid tokens
        """
        return self.token_store.is_token_valid(username)
    
    async def save_initial_tokens(
        self,
        username: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> None:
        """
        Save initial tokens after successful authentication.
        
        Args:
            username: User's email/username
            access_token: Cway JWT access token
            refresh_token: Cway JWT refresh token
            expires_in: Token expiry in seconds
        """
        try:
            self.token_store.save_tokens(
                username=username,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
            )
            logger.info(f"Saved initial tokens for {username}")
        except TokenStoreError as e:
            logger.error(f"Failed to save initial tokens for {username}: {e}")
            raise TokenManagerError(f"Failed to save tokens: {e}")
    
    def logout_user(self, username: str) -> bool:
        """
        Logout user by deleting their tokens.
        
        Args:
            username: User's email/username
            
        Returns:
            True if tokens were deleted, False if none existed
        """
        # Also clean up the refresh lock
        with self._locks_lock:
            self._refresh_locks.pop(username, None)
        
        result = self.token_store.delete_tokens(username)
        if result:
            logger.info(f"Logged out {username}")
        return result
    
    def get_token_info(self, username: str) -> Optional[dict]:
        """
        Get token information for user (without sensitive data).
        
        Args:
            username: User's email/username
            
        Returns:
            Dict with {username, expires_at, is_valid} or None
        """
        token_data = self.token_store.get_tokens(username)
        
        if not token_data:
            return None
        
        try:
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            is_valid = expires_at > datetime.now()
            
            return {
                "username": username,
                "expires_at": token_data["expires_at"],
                "is_valid": is_valid,
                "expires_in_seconds": int((expires_at - datetime.now()).total_seconds()),
            }
        except (KeyError, ValueError):
            return None
    
    def list_authenticated_users(self) -> list[str]:
        """
        List all users with stored tokens.
        
        Returns:
            List of usernames
        """
        return self.token_store.list_stored_users()


class TokenManagerError(Exception):
    """Exception raised for token management errors."""
    pass
