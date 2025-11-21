"""
Unit tests for request context management.

Tests cover:
- Context setting and getting
- Context isolation between async tasks
- Thread safety
- Context clearing
- Property accessors
"""

import pytest
import asyncio
from src.infrastructure.request_context import (
    RequestContext,
    set_request_context,
    get_request_context,
    clear_request_context,
    get_current_token,
    get_current_user,
    get_current_user_tokens,
)
from src.infrastructure.user_identity import UserIdentity


class TestRequestContext:
    """Test RequestContext dataclass."""

    def test_request_context_creation(self):
        """Test creating a RequestContext."""
        identity = UserIdentity("user1", "org1", "Org Name")
        tokens = {"Org1": "token1", "Org2": "token2"}
        
        context = RequestContext(
            authorization_token="auth_token",
            user_identity=identity,
            user_tokens=tokens
        )
        
        assert context.authorization_token == "auth_token"
        assert context.user_identity == identity
        assert context.user_tokens == tokens

    def test_request_context_defaults(self):
        """Test RequestContext with default None values."""
        context = RequestContext()
        
        assert context.authorization_token is None
        assert context.user_identity is None
        assert context.user_tokens is None

    def test_user_id_property(self):
        """Test user_id property accessor."""
        identity = UserIdentity("user123", "org1", "Org Name")
        context = RequestContext(user_identity=identity)
        
        assert context.user_id == "user123"

    def test_user_id_property_without_identity(self):
        """Test user_id property returns None without identity."""
        context = RequestContext()
        assert context.user_id is None

    def test_org_id_property(self):
        """Test org_id property accessor."""
        identity = UserIdentity("user1", "org456", "Org Name")
        context = RequestContext(user_identity=identity)
        
        assert context.org_id == "org456"

    def test_org_id_property_without_identity(self):
        """Test org_id property returns None without identity."""
        context = RequestContext()
        assert context.org_id is None

    def test_org_name_property(self):
        """Test org_name property accessor."""
        identity = UserIdentity("user1", "org1", "Test Organization")
        context = RequestContext(user_identity=identity)
        
        assert context.org_name == "Test Organization"

    def test_org_name_property_without_identity(self):
        """Test org_name property returns None without identity."""
        context = RequestContext()
        assert context.org_name is None

    def test_get_token_for_org_success(self):
        """Test getting token for specific organization."""
        tokens = {"Org1": "token1", "Org2": "token2", "Org3": "token3"}
        context = RequestContext(user_tokens=tokens)
        
        assert context.get_token_for_org("Org1") == "token1"
        assert context.get_token_for_org("Org2") == "token2"
        assert context.get_token_for_org("Org3") == "token3"

    def test_get_token_for_org_not_found(self):
        """Test getting token for org that doesn't exist."""
        tokens = {"Org1": "token1"}
        context = RequestContext(user_tokens=tokens)
        
        assert context.get_token_for_org("NonexistentOrg") is None

    def test_get_token_for_org_without_tokens(self):
        """Test getting token when user_tokens is None."""
        context = RequestContext()
        assert context.get_token_for_org("AnyOrg") is None


class TestContextManagement:
    """Test context setting, getting, and clearing."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_request_context()

    def test_set_and_get_context(self):
        """Test setting and getting request context."""
        identity = UserIdentity("user1", "org1", "Org Name")
        tokens = {"Org1": "token1"}
        
        set_request_context(
            token="auth_token",
            user=identity,
            user_tokens=tokens
        )
        
        context = get_request_context()
        assert context.authorization_token == "auth_token"
        assert context.user_identity == identity
        assert context.user_tokens == tokens

    def test_set_partial_context(self):
        """Test setting only some context values."""
        set_request_context(token="just_token")
        
        context = get_request_context()
        assert context.authorization_token == "just_token"
        assert context.user_identity is None
        assert context.user_tokens is None

    def test_clear_context(self):
        """Test clearing request context."""
        identity = UserIdentity("user1", "org1", "Org Name")
        set_request_context(
            token="auth_token",
            user=identity,
            user_tokens={"Org1": "token1"}
        )
        
        clear_request_context()
        
        context = get_request_context()
        assert context.authorization_token is None
        assert context.user_identity is None
        assert context.user_tokens is None

    def test_overwrite_context(self):
        """Test overwriting existing context."""
        identity1 = UserIdentity("user1", "org1", "Org1")
        identity2 = UserIdentity("user2", "org2", "Org2")
        
        set_request_context(token="token1", user=identity1)
        assert get_request_context().user_id == "user1"
        
        set_request_context(token="token2", user=identity2)
        assert get_request_context().user_id == "user2"

    def test_get_current_token(self):
        """Test get_current_token convenience function."""
        set_request_context(token="test_token")
        assert get_current_token() == "test_token"

    def test_get_current_token_empty(self):
        """Test get_current_token returns None when not set."""
        clear_request_context()
        assert get_current_token() is None

    def test_get_current_user(self):
        """Test get_current_user convenience function."""
        identity = UserIdentity("user1", "org1", "Org Name")
        set_request_context(user=identity)
        
        user = get_current_user()
        assert user is not None
        assert user.user_id == "user1"

    def test_get_current_user_empty(self):
        """Test get_current_user returns None when not set."""
        clear_request_context()
        assert get_current_user() is None

    def test_get_current_user_tokens(self):
        """Test get_current_user_tokens convenience function."""
        tokens = {"Org1": "token1", "Org2": "token2"}
        set_request_context(user_tokens=tokens)
        
        retrieved = get_current_user_tokens()
        assert retrieved == tokens

    def test_get_current_user_tokens_empty(self):
        """Test get_current_user_tokens returns None when not set."""
        clear_request_context()
        assert get_current_user_tokens() is None


class TestAsyncIsolation:
    """Test context isolation between async tasks."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_request_context()

    @pytest.mark.asyncio
    async def test_context_isolation_between_tasks(self):
        """Test that each async task has its own context."""
        results = []
        
        async def task1():
            identity1 = UserIdentity("user1", "org1", "Org1")
            set_request_context(token="token1", user=identity1)
            await asyncio.sleep(0.01)  # Yield control
            context = get_request_context()
            results.append(("task1", context.authorization_token, context.user_id))
        
        async def task2():
            identity2 = UserIdentity("user2", "org2", "Org2")
            set_request_context(token="token2", user=identity2)
            await asyncio.sleep(0.01)  # Yield control
            context = get_request_context()
            results.append(("task2", context.authorization_token, context.user_id))
        
        async def task3():
            identity3 = UserIdentity("user3", "org3", "Org3")
            set_request_context(token="token3", user=identity3)
            await asyncio.sleep(0.01)  # Yield control
            context = get_request_context()
            results.append(("task3", context.authorization_token, context.user_id))
        
        # Run tasks concurrently
        await asyncio.gather(task1(), task2(), task3())
        
        # Each task should have preserved its own context
        assert len(results) == 3
        task1_result = next(r for r in results if r[0] == "task1")
        task2_result = next(r for r in results if r[0] == "task2")
        task3_result = next(r for r in results if r[0] == "task3")
        
        assert task1_result == ("task1", "token1", "user1")
        assert task2_result == ("task2", "token2", "user2")
        assert task3_result == ("task3", "token3", "user3")

    @pytest.mark.asyncio
    async def test_context_survives_await(self):
        """Test that context survives across await boundaries."""
        identity = UserIdentity("user1", "org1", "Org Name")
        set_request_context(token="test_token", user=identity)
        
        # Context before await
        assert get_current_token() == "test_token"
        assert get_current_user().user_id == "user1"
        
        # Simulate async work
        await asyncio.sleep(0.001)
        
        # Context after await (should be preserved)
        assert get_current_token() == "test_token"
        assert get_current_user().user_id == "user1"

    @pytest.mark.asyncio
    async def test_many_concurrent_contexts(self):
        """Test context isolation with many concurrent tasks."""
        num_tasks = 20
        results = []
        
        async def worker(task_id):
            identity = UserIdentity(f"user{task_id}", f"org{task_id}", f"Org{task_id}")
            set_request_context(
                token=f"token{task_id}",
                user=identity,
                user_tokens={f"Org{task_id}": f"token{task_id}"}
            )
            await asyncio.sleep(0.001)  # Simulate work
            context = get_request_context()
            results.append((
                task_id,
                context.authorization_token,
                context.user_id,
                context.org_name
            ))
        
        # Create and run many concurrent tasks
        tasks = [worker(i) for i in range(num_tasks)]
        await asyncio.gather(*tasks)
        
        # Verify all contexts were preserved correctly
        assert len(results) == num_tasks
        for task_id in range(num_tasks):
            result = next(r for r in results if r[0] == task_id)
            assert result == (
                task_id,
                f"token{task_id}",
                f"user{task_id}",
                f"Org{task_id}"
            )


class TestThreadSafety:
    """Test thread safety of context management."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_request_context()

    def test_context_isolation_between_threads(self):
        """Test that each thread has its own context."""
        import threading
        results = {}
        
        def worker(thread_id):
            identity = UserIdentity(f"user{thread_id}", f"org{thread_id}", f"Org{thread_id}")
            set_request_context(
                token=f"token{thread_id}",
                user=identity
            )
            import time
            time.sleep(0.01)  # Simulate work
            context = get_request_context()
            results[thread_id] = (
                context.authorization_token,
                context.user_id
            )
        
        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Each thread should have had its own context
        assert len(results) == 5
        for i in range(5):
            assert results[i] == (f"token{i}", f"user{i}")


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_request_context()

    def test_multiple_clears(self):
        """Test that clearing multiple times doesn't error."""
        set_request_context(token="test")
        clear_request_context()
        clear_request_context()  # Should not error
        assert get_current_token() is None

    def test_get_before_set(self):
        """Test getting context before it's been set."""
        clear_request_context()
        context = get_request_context()
        assert context.authorization_token is None
        assert context.user_identity is None
        assert context.user_tokens is None

    def test_set_none_values_explicitly(self):
        """Test explicitly setting None values."""
        set_request_context(token=None, user=None, user_tokens=None)
        context = get_request_context()
        assert context.authorization_token is None
        assert context.user_identity is None
        assert context.user_tokens is None

    def test_empty_user_tokens_dict(self):
        """Test with empty user_tokens dictionary."""
        set_request_context(user_tokens={})
        context = get_request_context()
        assert context.user_tokens == {}
        assert context.get_token_for_org("AnyOrg") is None

    def test_context_with_special_characters(self):
        """Test context with special characters in values."""
        special_org = "Org@#$%^&*()Name"
        identity = UserIdentity("user1", "org1", special_org)
        tokens = {special_org: "token_with_special_chars!@#"}
        
        set_request_context(token="token!@#$%", user=identity, user_tokens=tokens)
        
        context = get_request_context()
        assert context.authorization_token == "token!@#$%"
        assert context.org_name == special_org
        assert context.get_token_for_org(special_org) == "token_with_special_chars!@#"

    def test_very_long_token(self):
        """Test context with very long token."""
        long_token = "x" * 10000
        set_request_context(token=long_token)
        assert get_current_token() == long_token

    def test_many_org_tokens(self):
        """Test context with many organization tokens."""
        many_tokens = {f"Org{i}": f"token{i}" for i in range(100)}
        set_request_context(user_tokens=many_tokens)
        
        context = get_request_context()
        assert len(context.user_tokens) == 100
        for i in range(100):
            assert context.get_token_for_org(f"Org{i}") == f"token{i}"


class TestRealWorldScenarios:
    """Test realistic usage patterns."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_request_context()

    @pytest.mark.asyncio
    async def test_request_lifecycle(self):
        """Test typical request lifecycle: set -> use -> clear."""
        # Incoming request
        identity = UserIdentity("user123", "org456", "My Organization")
        tokens = {"My Organization": "token123", "Other Org": "token456"}
        
        # Set context at start of request
        set_request_context(
            token="bearer_auth_token",
            user=identity,
            user_tokens=tokens
        )
        
        # Use context during request processing
        current_user = get_current_user()
        assert current_user.user_id == "user123"
        assert current_user.org_name == "My Organization"
        
        # Get token for multi-org query
        context = get_request_context()
        org1_token = context.get_token_for_org("My Organization")
        org2_token = context.get_token_for_org("Other Org")
        assert org1_token == "token123"
        assert org2_token == "token456"
        
        # Clear context at end of request
        clear_request_context()
        assert get_current_user() is None

    @pytest.mark.asyncio
    async def test_fallback_to_env_token(self):
        """Test scenario where no context is set (fallback behavior)."""
        # No context set - simulating STDIO mode or SSE without auth
        context = get_request_context()
        assert context.authorization_token is None
        assert context.user_identity is None
        
        # Application should fall back to env token in this case
        # (tested in integration tests)

    @pytest.mark.asyncio
    async def test_multi_org_query_workflow(self):
        """Test workflow for querying multiple organizations."""
        identity = UserIdentity("user1", "org1", "Primary Org")
        tokens = {
            "Primary Org": "token_primary",
            "Client Org A": "token_client_a",
            "Client Org B": "token_client_b",
        }
        
        set_request_context(token="main_token", user=identity, user_tokens=tokens)
        
        # Simulate multi-org query
        context = get_request_context()
        orgs_to_query = ["Primary Org", "Client Org A", "Client Org B"]
        
        for org_name in orgs_to_query:
            org_token = context.get_token_for_org(org_name)
            assert org_token is not None
            assert org_token.startswith("token_")
