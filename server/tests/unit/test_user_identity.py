"""
Unit tests for UserIdentityExtractor and UserIdentityCache.

Tests cover:
- Token validation with Cway API
- User identity extraction
- Caching behavior with TTL
- Error handling for invalid tokens
- Cache key generation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.user_identity import (
    UserIdentity,
    UserIdentityCache,
    UserIdentityExtractor,
)


# Test data
VALID_TOKEN = "test_bearer_token_abc123xyz"
USER_1_DATA = {
    "me": {
        "id": "user_001",
        "email": "user1@example.com",
        "organisation": {
            "id": "org_001",
            "name": "Organization One"
        }
    }
}
USER_2_DATA = {
    "me": {
        "id": "user_002",
        "email": "user2@example.com",
        "organisation": {
            "id": "org_002",
            "name": "Organization Two"
        }
    }
}


class TestUserIdentity:
    """Test UserIdentity dataclass."""

    def test_user_identity_creation(self):
        """Test creating a UserIdentity instance."""
        identity = UserIdentity(
            user_id="user123",
            org_id="org456",
            org_name="Test Org",
            email="test@example.com"
        )
        assert identity.user_id == "user123"
        assert identity.org_id == "org456"
        assert identity.org_name == "Test Org"
        assert identity.email == "test@example.com"

    def test_user_identity_without_email(self):
        """Test UserIdentity without email (optional field)."""
        identity = UserIdentity(
            user_id="user123",
            org_id="org456",
            org_name="Test Org"
        )
        assert identity.user_id == "user123"
        assert identity.email is None

    def test_user_identity_equality(self):
        """Test UserIdentity equality comparison."""
        id1 = UserIdentity("user1", "org1", "Org Name")
        id2 = UserIdentity("user1", "org1", "Org Name")
        id3 = UserIdentity("user2", "org1", "Org Name")
        
        assert id1 == id2
        assert id1 != id3


class TestUserIdentityCache:
    """Test UserIdentityCache functionality."""

    @pytest.fixture
    def cache(self):
        """Create a cache with short TTL for testing."""
        return UserIdentityCache(ttl_seconds=2)

    @pytest.fixture
    def identity(self):
        """Create a test identity."""
        return UserIdentity(
            user_id="user123",
            org_id="org456",
            org_name="Test Org",
            email="test@example.com"
        )

    def test_cache_key_generation_short_token(self, cache):
        """Test cache key generation for short tokens."""
        short_token = "abc123"
        key = cache._make_cache_key(short_token)
        assert key == "abc123"

    def test_cache_key_generation_long_token(self, cache):
        """Test cache key generation for long tokens."""
        long_token = "a" * 30
        key = cache._make_cache_key(long_token)
        assert key == f"{'a' * 8}...{'a' * 8}"
        assert len(key) == 19  # 8 + 3 + 8

    def test_cache_set_and_get(self, cache, identity):
        """Test setting and getting from cache."""
        token = "test_token_123"
        cache.set(token, identity)
        
        retrieved = cache.get(token)
        assert retrieved is not None
        assert retrieved.user_id == identity.user_id
        assert retrieved.org_id == identity.org_id
        assert retrieved.org_name == identity.org_name

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("nonexistent_token")
        assert result is None

    def test_cache_expiration(self, cache, identity):
        """Test that cache entries expire after TTL."""
        import time
        
        token = "test_token_expire"
        cache.set(token, identity)
        
        # Should be cached
        assert cache.get(token) is not None
        
        # Wait for expiration
        time.sleep(2.5)
        
        # Should be expired
        assert cache.get(token) is None

    def test_cache_invalidate(self, cache, identity):
        """Test manual cache invalidation."""
        token = "test_token_invalidate"
        cache.set(token, identity)
        
        assert cache.get(token) is not None
        
        cache.invalidate(token)
        assert cache.get(token) is None

    def test_cache_invalidate_nonexistent(self, cache):
        """Test invalidating a nonexistent entry doesn't error."""
        cache.invalidate("nonexistent_token")  # Should not raise

    def test_cache_clear(self, cache):
        """Test clearing all cache entries."""
        id1 = UserIdentity("user1", "org1", "Org1")
        id2 = UserIdentity("user2", "org2", "Org2")
        
        cache.set("token1", id1)
        cache.set("token2", id2)
        
        assert cache.get("token1") is not None
        assert cache.get("token2") is not None
        
        cache.clear()
        
        assert cache.get("token1") is None
        assert cache.get("token2") is None

    def test_cache_multiple_tokens(self, cache):
        """Test caching multiple different tokens."""
        tokens_and_ids = [
            ("token1", UserIdentity("user1", "org1", "Org1")),
            ("token2", UserIdentity("user2", "org2", "Org2")),
            ("token3", UserIdentity("user3", "org3", "Org3")),
        ]
        
        # Cache all
        for token, identity in tokens_and_ids:
            cache.set(token, identity)
        
        # Verify all cached
        for token, expected_identity in tokens_and_ids:
            cached = cache.get(token)
            assert cached is not None
            assert cached.user_id == expected_identity.user_id

    def test_cache_same_token_overwrites(self, cache):
        """Test that setting same token overwrites previous entry."""
        token = "test_token"
        id1 = UserIdentity("user1", "org1", "Org1")
        id2 = UserIdentity("user2", "org2", "Org2")
        
        cache.set(token, id1)
        assert cache.get(token).user_id == "user1"
        
        cache.set(token, id2)
        assert cache.get(token).user_id == "user2"


class TestUserIdentityExtractor:
    """Test UserIdentityExtractor functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a UserIdentityExtractor instance."""
        return UserIdentityExtractor()

    @pytest.mark.asyncio
    async def test_extract_identity_success(self, extractor):
        """Test successful identity extraction."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            # Mock the async context manager and execute_query
            mock_client = AsyncMock()
            mock_client.execute_query.return_value = USER_1_DATA
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            identity = await extractor.get_user_identity("test_token")
            
            assert identity.user_id == "user_001"
            assert identity.org_id == "org_001"
            assert identity.org_name == "Organization One"
            assert identity.email == "user1@example.com"

    @pytest.mark.asyncio
    async def test_extract_identity_caches_result(self, extractor):
        """Test that identity extraction caches the result."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.return_value = USER_1_DATA
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            # First call
            identity1 = await extractor.get_user_identity("test_token")
            
            # Second call should use cache
            identity2 = await extractor.get_user_identity("test_token")
            
            # Should only call API once
            assert mock_client.execute_query.call_count == 1
            
            # Results should be the same
            assert identity1 == identity2

    @pytest.mark.asyncio
    async def test_extract_identity_different_tokens(self, extractor):
        """Test extracting identities for different tokens."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            
            # Return different data for each call
            mock_client.execute_query.side_effect = [USER_1_DATA, USER_2_DATA]
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            identity1 = await extractor.get_user_identity("token1")
            identity2 = await extractor.get_user_identity("token2")
            
            assert identity1.user_id == "user_001"
            assert identity2.user_id == "user_002"
            assert mock_client.execute_query.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_identity_invalid_token(self, extractor):
        """Test handling of invalid token."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.side_effect = Exception("Unauthorized")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            with pytest.raises(ValueError, match="Invalid token or API error"):
                await extractor.get_user_identity("invalid_token")

    @pytest.mark.asyncio
    async def test_extract_identity_missing_me_field(self, extractor):
        """Test handling of API response missing 'me' field."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.return_value = {}  # Missing 'me'
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            with pytest.raises(ValueError, match="Invalid token or API error"):
                await extractor.get_user_identity("test_token")

    @pytest.mark.asyncio
    async def test_extract_identity_missing_user_id(self, extractor):
        """Test handling of API response missing user ID."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            invalid_data = {
                "me": {
                    # Missing id
                    "email": "test@example.com",
                    "organisation": {"id": "org1", "name": "Org"}
                }
            }
            mock_client.execute_query.return_value = invalid_data
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            with pytest.raises(ValueError, match="Invalid token or API error"):
                await extractor.get_user_identity("test_token")

    @pytest.mark.asyncio
    async def test_extract_identity_missing_org_id(self, extractor):
        """Test handling of API response missing organization ID."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            invalid_data = {
                "me": {
                    "id": "user1",
                    "email": "test@example.com",
                    "organisation": {
                        # Missing id
                        "name": "Org"
                    }
                }
            }
            mock_client.execute_query.return_value = invalid_data
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            with pytest.raises(ValueError, match="Invalid token or API error"):
                await extractor.get_user_identity("test_token")

    @pytest.mark.asyncio
    async def test_extract_identity_without_email(self, extractor):
        """Test extracting identity when email is not provided."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            data_no_email = {
                "me": {
                    "id": "user1",
                    # No email field
                    "organisation": {"id": "org1", "name": "Org"}
                }
            }
            mock_client.execute_query.return_value = data_no_email
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            identity = await extractor.get_user_identity("test_token")
            
            assert identity.user_id == "user1"
            assert identity.org_id == "org1"
            assert identity.email is None

    @pytest.mark.asyncio
    async def test_extract_identity_org_name_defaults_to_unknown(self, extractor):
        """Test that org_name defaults to 'Unknown' if not provided."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            data_no_org_name = {
                "me": {
                    "id": "user1",
                    "email": "test@example.com",
                    "organisation": {
                        "id": "org1"
                        # No name field
                    }
                }
            }
            mock_client.execute_query.return_value = data_no_org_name
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            identity = await extractor.get_user_identity("test_token")
            
            assert identity.org_name == "Unknown"

    @pytest.mark.asyncio
    async def test_extract_identity_api_network_error(self, extractor):
        """Test handling of network errors when calling API."""
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.side_effect = ConnectionError("Network error")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            with pytest.raises(ValueError, match="Invalid token or API error"):
                await extractor.get_user_identity("test_token")


class TestCacheIntegration:
    """Test cache behavior in real-world scenarios."""

    @pytest.mark.asyncio
    async def test_cache_reduces_api_calls(self):
        """Test that cache significantly reduces API calls."""
        extractor = UserIdentityExtractor()
        
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.return_value = USER_1_DATA
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            # Make 10 calls with same token
            for _ in range(10):
                await extractor.get_user_identity("same_token")
            
            # Should only call API once
            assert mock_client.execute_query.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_isolation_between_tokens(self):
        """Test that cache properly isolates different tokens."""
        extractor = UserIdentityExtractor()
        
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.side_effect = [
                USER_1_DATA,
                USER_2_DATA,
                USER_1_DATA,  # If called again for token1
                USER_2_DATA,  # If called again for token2
            ]
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            # Call with token1 twice
            id1a = await extractor.get_user_identity("token1")
            id1b = await extractor.get_user_identity("token1")
            
            # Call with token2 twice
            id2a = await extractor.get_user_identity("token2")
            id2b = await extractor.get_user_identity("token2")
            
            # Should call API only twice (once per token)
            assert mock_client.execute_query.call_count == 2
            
            # Verify correct results
            assert id1a.user_id == "user_001"
            assert id1b.user_id == "user_001"
            assert id2a.user_id == "user_002"
            assert id2b.user_id == "user_002"

    @pytest.mark.asyncio
    async def test_cache_refresh_after_expiry(self):
        """Test that cache refreshes after TTL expires."""
        import time
        
        # Create extractor with short TTL
        extractor = UserIdentityExtractor()
        extractor.cache = UserIdentityCache(ttl_seconds=1)
        
        with patch('src.infrastructure.user_identity.CwayGraphQLClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.execute_query.return_value = USER_1_DATA
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = AsyncMock()
            
            # First call
            await extractor.get_user_identity("test_token")
            assert mock_client.execute_query.call_count == 1
            
            # Second call (should use cache)
            await extractor.get_user_identity("test_token")
            assert mock_client.execute_query.call_count == 1
            
            # Wait for cache to expire
            time.sleep(1.5)
            
            # Third call (should fetch again)
            await extractor.get_user_identity("test_token")
            assert mock_client.execute_query.call_count == 2


class TestGlobalInstance:
    """Test global instance management."""

    def test_get_identity_extractor_returns_instance(self):
        """Test that get_identity_extractor returns a UserIdentityExtractor."""
        from src.infrastructure.user_identity import get_identity_extractor
        
        extractor = get_identity_extractor()
        assert isinstance(extractor, UserIdentityExtractor)

    def test_get_identity_extractor_singleton(self):
        """Test that get_identity_extractor returns the same instance."""
        from src.infrastructure.user_identity import get_identity_extractor
        
        extractor1 = get_identity_extractor()
        extractor2 = get_identity_extractor()
        assert extractor1 is extractor2
