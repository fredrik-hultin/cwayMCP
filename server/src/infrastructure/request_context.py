"""
Request context management for per-request state.

Uses contextvars for thread-safe async context management.
"""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Dict, Optional

from src.infrastructure.user_identity import UserIdentity

# Context variables for request-scoped data
_request_token: ContextVar[Optional[str]] = ContextVar("request_token", default=None)
_request_user: ContextVar[Optional[UserIdentity]] = ContextVar("request_user", default=None)
_request_user_tokens: ContextVar[Optional[Dict[str, str]]] = ContextVar(
    "request_user_tokens", default=None
)


@dataclass
class RequestContext:
    """Container for request-scoped data."""

    authorization_token: Optional[str] = None
    user_identity: Optional[UserIdentity] = None
    user_tokens: Optional[Dict[str, str]] = None  # org_name -> token mapping

    @property
    def user_id(self) -> Optional[str]:
        """Get user ID from identity."""
        return self.user_identity.user_id if self.user_identity else None

    @property
    def org_id(self) -> Optional[str]:
        """Get organization ID from identity."""
        return self.user_identity.org_id if self.user_identity else None

    @property
    def org_name(self) -> Optional[str]:
        """Get organization name from identity."""
        return self.user_identity.org_name if self.user_identity else None

    def get_token_for_org(self, org_name: str) -> Optional[str]:
        """
        Get token for a specific organization.

        Args:
            org_name: Organization name

        Returns:
            Token for the organization, or None if not found
        """
        if not self.user_tokens:
            return None
        return self.user_tokens.get(org_name)


def set_request_context(
    token: Optional[str] = None,
    user: Optional[UserIdentity] = None,
    user_tokens: Optional[Dict[str, str]] = None,
) -> None:
    """
    Set request context for current async context.

    Args:
        token: Authorization token from request
        user: User identity
        user_tokens: Dictionary of org_name -> token for multi-org queries
    """
    _request_token.set(token)
    _request_user.set(user)
    _request_user_tokens.set(user_tokens)


def get_request_context() -> RequestContext:
    """
    Get current request context.

    Returns:
        RequestContext with current values
    """
    return RequestContext(
        authorization_token=_request_token.get(),
        user_identity=_request_user.get(),
        user_tokens=_request_user_tokens.get(),
    )


def clear_request_context() -> None:
    """Clear request context (should be called after request completes)."""
    _request_token.set(None)
    _request_user.set(None)
    _request_user_tokens.set(None)


def get_current_token() -> Optional[str]:
    """Get current request's authorization token."""
    return _request_token.get()


def get_current_user() -> Optional[UserIdentity]:
    """Get current request's user identity."""
    return _request_user.get()


def get_current_user_tokens() -> Optional[Dict[str, str]]:
    """Get current request's user tokens."""
    return _request_user_tokens.get()
