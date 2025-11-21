"""
User identity extraction from Cway API tokens.

Validates tokens with the Cway API and caches user identity information.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from src.infrastructure.graphql_client import CwayGraphQLClient

logger = logging.getLogger(__name__)


@dataclass
class UserIdentity:
    """User identity information extracted from token."""

    user_id: str
    org_id: str
    org_name: str
    email: Optional[str] = None


class UserIdentityCache:
    """Cache for user identity information with TTL."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[UserIdentity, datetime]] = {}

    def get(self, token: str) -> Optional[UserIdentity]:
        """
        Get cached identity for a token.

        Args:
            token: API token

        Returns:
            UserIdentity if cached and not expired, None otherwise
        """
        # Use first/last 8 chars as cache key (don't store full token)
        cache_key = self._make_cache_key(token)

        if cache_key in self._cache:
            identity, expiry = self._cache[cache_key]
            if datetime.utcnow() < expiry:
                logger.debug(f"Cache hit for user {identity.user_id}")
                return identity
            else:
                # Expired, remove from cache
                del self._cache[cache_key]
                logger.debug("Cache entry expired")

        return None

    def set(self, token: str, identity: UserIdentity) -> None:
        """
        Cache identity for a token.

        Args:
            token: API token
            identity: User identity to cache
        """
        cache_key = self._make_cache_key(token)
        expiry = datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
        self._cache[cache_key] = (identity, expiry)
        logger.debug(f"Cached identity for user {identity.user_id}")

    def invalidate(self, token: str) -> None:
        """
        Invalidate cache entry for a token.

        Args:
            token: API token
        """
        cache_key = self._make_cache_key(token)
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug("Invalidated cache entry")

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.debug("Cleared cache")

    def _make_cache_key(self, token: str) -> str:
        """
        Create a cache key from token.

        Uses first and last 8 characters to avoid storing full token.

        Args:
            token: API token

        Returns:
            Cache key
        """
        if len(token) <= 16:
            return token
        return f"{token[:8]}...{token[-8:]}"


class UserIdentityExtractor:
    """Extracts user identity from Cway API tokens."""

    def __init__(self):
        """Initialize extractor with cache."""
        self.cache = UserIdentityCache()

    async def get_user_identity(self, token: str) -> UserIdentity:
        """
        Get user identity from token.

        Validates token with Cway API and extracts user information.
        Results are cached to reduce API calls.

        Args:
            token: Cway API token

        Returns:
            UserIdentity with user_id, org_id, and org_name

        Raises:
            ValueError: If token is invalid or API call fails
        """
        # Check cache first
        cached = self.cache.get(token)
        if cached:
            return cached

        # Validate token and extract identity via Cway API
        try:
            identity = await self._fetch_identity(token)
            self.cache.set(token, identity)
            return identity
        except Exception as e:
            logger.error(f"Failed to extract user identity: {e}")
            raise ValueError(f"Invalid token or API error: {e}")

    async def _fetch_identity(self, token: str) -> UserIdentity:
        """
        Fetch user identity from Cway API.

        Uses the GraphQL 'me' query to get current user information.

        Args:
            token: Cway API token

        Returns:
            UserIdentity

        Raises:
            Exception: If API call fails
        """
        async with CwayGraphQLClient(api_token=token) as client:
            # Query for current user information
            query = """
            query GetCurrentUser {
                me {
                    id
                    email
                    organisation {
                        id
                        name
                    }
                }
            }
            """

            result = await client.execute_query(query)

            if not result or "me" not in result:
                raise ValueError("Invalid API response: missing 'me' field")

            user_data = result["me"]
            org_data = user_data.get("organisation", {})

            if not user_data.get("id") or not org_data.get("id"):
                raise ValueError("Invalid API response: missing user or organization ID")

            identity = UserIdentity(
                user_id=str(user_data["id"]),
                org_id=str(org_data["id"]),
                org_name=org_data.get("name", "Unknown"),
                email=user_data.get("email"),
            )

            logger.info(
                f"Extracted identity: user={identity.user_id}, "
                f"org={identity.org_name} ({identity.org_id})"
            )

            return identity


# Global instance
_identity_extractor: Optional[UserIdentityExtractor] = None


def get_identity_extractor() -> UserIdentityExtractor:
    """Get or create the global identity extractor instance."""
    global _identity_extractor
    if _identity_extractor is None:
        _identity_extractor = UserIdentityExtractor()
    return _identity_extractor
