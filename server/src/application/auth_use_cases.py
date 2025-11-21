"""Authentication use cases for per-user SSO."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from ..infrastructure.auth.token_manager import TokenManager, TokenManagerError


logger = logging.getLogger(__name__)


@dataclass
class LoginInitiationResult:
    """Result of login initiation."""
    success: bool
    authorization_url: str
    state: str
    message: str


@dataclass
class LoginCompletionResult:
    """Result of login completion."""
    success: bool
    username: str
    message: str
    expires_in_minutes: Optional[int] = None


@dataclass
class WhoAmIResult:
    """Result of whoami query."""
    authenticated: bool
    username: str
    message: str
    expires_in_minutes: Optional[int] = None
    expires_at: Optional[str] = None


class AuthUseCases:
    """Use cases for authentication operations."""
    
    def __init__(self, token_manager: TokenManager):
        """Initialize auth use cases.
        
        Args:
            token_manager: TokenManager instance for token operations
        """
        self.token_manager = token_manager
    
    async def initiate_login(self, username: str) -> LoginInitiationResult:
        """Initiate login flow for a user.
        
        Args:
            username: User identifier (email)
            
        Returns:
            LoginInitiationResult with authorization URL
        """
        try:
            # Generate authorization URL with PKCE
            auth_url, state, code_verifier = (
                self.token_manager.entra_authenticator.get_authorization_url()
            )
            
            # Store code verifier and state for this user temporarily
            # Note: In production, this should be stored securely and associated with the user
            # For now, we rely on the state parameter being validated by Entra ID
            
            logger.info(f"🔐 Login initiated for user: {username}")
            
            return LoginInitiationResult(
                success=True,
                authorization_url=auth_url,
                state=state,
                message=(
                    f"Login initiated for {username}.\n"
                    f"Open this URL in your browser to authenticate:\n"
                    f"{auth_url}\n\n"
                    f"After authentication, you will receive an authorization code.\n"
                    f"Use the 'complete_login' tool with the code and state to finish login."
                )
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to initiate login for {username}: {e}")
            return LoginInitiationResult(
                success=False,
                authorization_url="",
                state="",
                message=f"Failed to initiate login: {str(e)}"
            )
    
    async def complete_login(
        self, 
        username: str, 
        authorization_code: str, 
        state: str
    ) -> LoginCompletionResult:
        """Complete login by exchanging authorization code for tokens.
        
        Args:
            username: User identifier (email)
            authorization_code: OAuth2 authorization code from Entra ID
            state: State parameter to verify request
            
        Returns:
            LoginCompletionResult with success status
        """
        try:
            # Exchange authorization code for Cway tokens
            tokens = await self.token_manager.entra_authenticator.exchange_code_for_cway_tokens(
                authorization_code, state
            )
            
            # Store tokens for this user
            self.token_manager.token_store.save_tokens(
                username=username,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_in=tokens["expires_in"]
            )
            
            expires_in_minutes = tokens.get("expires_in", 3600) // 60
            
            logger.info(f"✅ User {username} successfully authenticated")
            
            return LoginCompletionResult(
                success=True,
                username=username,
                message=f"User {username} successfully authenticated! Token expires in {expires_in_minutes} minutes.",
                expires_in_minutes=expires_in_minutes
            )
            
        except TokenManagerError as e:
            logger.error(f"❌ Login failed for {username}: {e}")
            return LoginCompletionResult(
                success=False,
                username=username,
                message=f"Login failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error during login for {username}: {e}")
            return LoginCompletionResult(
                success=False,
                username=username,
                message=f"Unexpected error during login: {str(e)}"
            )
    
    async def logout(self, username: str) -> Dict[str, Any]:
        """Logout user by removing stored tokens.
        
        Args:
            username: User identifier (email)
            
        Returns:
            Dictionary with success status and message
        """
        try:
            self.token_manager.token_store.delete_tokens(username)
            logger.info(f"🚪 User {username} logged out")
            
            return {
                "success": True,
                "username": username,
                "message": f"User {username} successfully logged out. Tokens have been removed."
            }
            
        except FileNotFoundError:
            # User wasn't authenticated - this is fine, logout is idempotent
            logger.info(f"ℹ️  Logout called for non-authenticated user: {username}")
            return {
                "success": True,
                "username": username,
                "message": f"User {username} was not authenticated. No tokens to remove."
            }
        except Exception as e:
            logger.error(f"❌ Error during logout for {username}: {e}")
            return {
                "success": False,
                "username": username,
                "message": f"Error during logout: {str(e)}"
            }
    
    async def whoami(self, username: str) -> WhoAmIResult:
        """Get current user authentication status.
        
        Args:
            username: User identifier (email)
            
        Returns:
            WhoAmIResult with authentication status and token expiry
        """
        try:
            # Check if user is authenticated
            if not self.token_manager.is_user_authenticated(username):
                return WhoAmIResult(
                    authenticated=False,
                    username=username,
                    message=f"User {username} is not authenticated. Please login first."
                )
            
            # Get token information
            tokens = self.token_manager.token_store.get_tokens(username)
            expires_at_str = tokens.get("expires_at")
            
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                now = datetime.now()
                time_remaining = expires_at - now
                expires_in_minutes = int(time_remaining.total_seconds() / 60)
                
                if expires_in_minutes < 5:
                    message = (
                        f"⚠️  User {username} is authenticated but token is expiring soon "
                        f"({expires_in_minutes} minutes remaining). "
                        f"Token will be automatically refreshed on next API call."
                    )
                else:
                    message = (
                        f"✅ User {username} is authenticated. "
                        f"Token expires in {expires_in_minutes} minutes."
                    )
                
                return WhoAmIResult(
                    authenticated=True,
                    username=username,
                    message=message,
                    expires_in_minutes=expires_in_minutes,
                    expires_at=expires_at_str
                )
            else:
                return WhoAmIResult(
                    authenticated=True,
                    username=username,
                    message=f"✅ User {username} is authenticated."
                )
                
        except Exception as e:
            logger.error(f"❌ Error checking auth status for {username}: {e}")
            return WhoAmIResult(
                authenticated=False,
                username=username,
                message=f"Error checking authentication status: {str(e)}"
            )
    
    async def list_authenticated_users(self) -> Dict[str, Any]:
        """List all authenticated users.
        
        Returns:
            Dictionary with list of authenticated usernames
        """
        try:
            users = self.token_manager.token_store.list_stored_users()
            
            return {
                "success": True,
                "users": users,
                "count": len(users),
                "message": f"Found {len(users)} authenticated user(s)."
            }
            
        except Exception as e:
            logger.error(f"❌ Error listing authenticated users: {e}")
            return {
                "success": False,
                "users": [],
                "count": 0,
                "message": f"Error listing authenticated users: {str(e)}"
            }
