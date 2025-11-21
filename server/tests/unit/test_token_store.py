"""
Unit tests for TokenStore - token storage with encryption.

Tests cover:
- Token encryption/decryption
- Token storage and retrieval
- User isolation
- Organization management
- Database operations
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.infrastructure.token_store import TokenStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_tokens.db"
        yield str(db_path)


@pytest.fixture
def encryption_key():
    """Generate a test encryption key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


@pytest.fixture
def token_store(temp_db, encryption_key):
    """Create a TokenStore instance for testing."""
    return TokenStore(db_path=temp_db, encryption_key=encryption_key)


class TestTokenStoreInitialization:
    """Test TokenStore initialization and database setup."""

    def test_creates_database_file(self, temp_db, encryption_key):
        """Test that TokenStore creates the database file."""
        assert not os.path.exists(temp_db)
        TokenStore(db_path=temp_db, encryption_key=encryption_key)
        assert os.path.exists(temp_db)

    def test_creates_user_tokens_table(self, token_store, temp_db):
        """Test that the user_tokens table is created."""
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_tokens'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None
        assert result[0] == "user_tokens"

    def test_invalid_encryption_key_raises_error(self, temp_db):
        """Test that invalid encryption key raises error from Fernet."""
        with pytest.raises(Exception):  # Fernet raises ValueError or binascii.Error
            TokenStore(db_path=temp_db, encryption_key="invalid_key")


class TestTokenEncryption:
    """Test token encryption and decryption."""

    def test_encrypt_decrypt_roundtrip(self, token_store):
        """Test that encryption and decryption work correctly."""
        original_token = "test_bearer_token_12345"
        # Use store/get to test encryption roundtrip
        token_store.store_token("user1", "TestOrg", original_token)
        retrieved = token_store.get_token("user1", "TestOrg")
        assert retrieved == original_token

    def test_encrypted_token_in_db_is_different(self, token_store, temp_db):
        """Test that encrypted token in DB is different from original."""
        import sqlite3
        original_token = "test_bearer_token_12345"
        token_store.store_token("user1", "TestOrg", original_token)
        
        # Check the encrypted value in DB
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT encrypted_token FROM user_tokens WHERE user_id = ? AND org_name = ?",
            ("user1", "TestOrg")
        )
        encrypted_in_db = cursor.fetchone()[0]
        conn.close()
        
        assert encrypted_in_db != original_token

    def test_different_keys_cannot_decrypt(self, temp_db):
        """Test that tokens encrypted with one key cannot be decrypted with another."""
        from cryptography.fernet import Fernet, InvalidToken
        
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        
        store1 = TokenStore(db_path=temp_db, encryption_key=key1)
        store1.store_token("user1", "TestOrg", "test_token")
        
        store2 = TokenStore(db_path=temp_db, encryption_key=key2)
        with pytest.raises(InvalidToken):
            store2.get_token("user1", "TestOrg")


class TestTokenStorage:
    """Test token storage operations."""

    def test_store_token_success(self, token_store):
        """Test storing a token successfully."""
        token_store.store_token(
            user_id="user123",
            org_name="TestOrg",
            token="bearer_token_xyz"
        )
        
        tokens = token_store.get_user_tokens("user123")
        assert "TestOrg" in tokens
        assert tokens["TestOrg"] == "bearer_token_xyz"

    def test_store_multiple_org_tokens(self, token_store):
        """Test storing tokens for multiple organizations."""
        token_store.store_token("user123", "OrgA", "token_a")
        token_store.store_token("user123", "OrgB", "token_b")
        token_store.store_token("user123", "OrgC", "token_c")
        
        tokens = token_store.get_user_tokens("user123")
        assert len(tokens) == 3
        assert tokens["OrgA"] == "token_a"
        assert tokens["OrgB"] == "token_b"
        assert tokens["OrgC"] == "token_c"

    def test_update_existing_token(self, token_store):
        """Test updating an existing token for the same org."""
        token_store.store_token("user123", "TestOrg", "old_token")
        token_store.store_token("user123", "TestOrg", "new_token")
        
        tokens = token_store.get_user_tokens("user123")
        assert tokens["TestOrg"] == "new_token"

    def test_store_token_updates_last_used(self, token_store, temp_db):
        """Test that storing a token sets last_used timestamp."""
        import sqlite3
        from datetime import datetime
        
        before = datetime.utcnow()
        token_store.store_token("user123", "TestOrg", "token")
        after = datetime.utcnow()
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_used FROM user_tokens WHERE user_id = ? AND org_name = ?",
            ("user123", "TestOrg")
        )
        result = cursor.fetchone()
        conn.close()
        
        last_used = datetime.fromisoformat(result[0])
        assert before <= last_used <= after


class TestTokenRetrieval:
    """Test token retrieval operations."""

    def test_get_empty_tokens(self, token_store):
        """Test getting tokens for user with no stored tokens."""
        tokens = token_store.get_user_tokens("nonexistent_user")
        assert tokens == {}

    def test_get_user_tokens_user_isolation(self, token_store):
        """Test that users only see their own tokens."""
        token_store.store_token("user1", "OrgA", "token_user1_orgA")
        token_store.store_token("user2", "OrgA", "token_user2_orgA")
        token_store.store_token("user2", "OrgB", "token_user2_orgB")
        
        user1_tokens = token_store.get_user_tokens("user1")
        user2_tokens = token_store.get_user_tokens("user2")
        
        assert len(user1_tokens) == 1
        assert len(user2_tokens) == 2
        assert user1_tokens["OrgA"] == "token_user1_orgA"
        assert user2_tokens["OrgA"] == "token_user2_orgA"
        assert user2_tokens["OrgB"] == "token_user2_orgB"

    def test_get_user_tokens_decrypts_correctly(self, token_store):
        """Test that retrieved tokens are decrypted correctly."""
        original_token = "secret_bearer_token_12345"
        token_store.store_token("user123", "TestOrg", original_token)
        
        tokens = token_store.get_user_tokens("user123")
        assert tokens["TestOrg"] == original_token


class TestTokenDeletion:
    """Test token deletion operations."""

    def test_delete_token_success(self, token_store):
        """Test deleting a token successfully."""
        token_store.store_token("user123", "TestOrg", "token")
        result = token_store.delete_token("user123", "TestOrg")
        
        assert result is True
        tokens = token_store.get_user_tokens("user123")
        assert "TestOrg" not in tokens

    def test_delete_nonexistent_token(self, token_store):
        """Test deleting a token that doesn't exist."""
        result = token_store.delete_token("user123", "NonexistentOrg")
        assert result is False

    def test_delete_one_of_multiple_tokens(self, token_store):
        """Test deleting one token while keeping others."""
        token_store.store_token("user123", "OrgA", "token_a")
        token_store.store_token("user123", "OrgB", "token_b")
        token_store.store_token("user123", "OrgC", "token_c")
        
        token_store.delete_token("user123", "OrgB")
        
        tokens = token_store.get_user_tokens("user123")
        assert len(tokens) == 2
        assert "OrgA" in tokens
        assert "OrgB" not in tokens
        assert "OrgC" in tokens

    def test_delete_token_user_isolation(self, token_store):
        """Test that deleting a token only affects the specified user."""
        token_store.store_token("user1", "OrgA", "token_user1")
        token_store.store_token("user2", "OrgA", "token_user2")
        
        token_store.delete_token("user1", "OrgA")
        
        user1_tokens = token_store.get_user_tokens("user1")
        user2_tokens = token_store.get_user_tokens("user2")
        
        assert "OrgA" not in user1_tokens
        assert "OrgA" in user2_tokens


class TestOrganizationListing:
    """Test organization listing operations."""

    def test_list_orgs_empty(self, token_store):
        """Test listing organizations for user with no tokens."""
        orgs = token_store.list_orgs("user123")
        assert orgs == []

    def test_list_orgs_single(self, token_store):
        """Test listing organizations with single org."""
        token_store.store_token("user123", "TestOrg", "token")
        orgs = token_store.list_orgs("user123")
        assert orgs == ["TestOrg"]

    def test_list_orgs_multiple(self, token_store):
        """Test listing organizations with multiple orgs."""
        token_store.store_token("user123", "OrgA", "token_a")
        token_store.store_token("user123", "OrgB", "token_b")
        token_store.store_token("user123", "OrgC", "token_c")
        
        orgs = token_store.list_orgs("user123")
        assert len(orgs) == 3
        assert set(orgs) == {"OrgA", "OrgB", "OrgC"}

    def test_list_orgs_sorted(self, token_store):
        """Test that organizations are returned in sorted order."""
        token_store.store_token("user123", "Zebra", "token_z")
        token_store.store_token("user123", "Alpha", "token_a")
        token_store.store_token("user123", "Beta", "token_b")
        
        orgs = token_store.list_orgs("user123")
        assert orgs == ["Alpha", "Beta", "Zebra"]

    def test_list_orgs_user_isolation(self, token_store):
        """Test that org listing respects user isolation."""
        token_store.store_token("user1", "OrgA", "token_1a")
        token_store.store_token("user1", "OrgB", "token_1b")
        token_store.store_token("user2", "OrgC", "token_2c")
        token_store.store_token("user2", "OrgD", "token_2d")
        
        user1_orgs = token_store.list_orgs("user1")
        user2_orgs = token_store.list_orgs("user2")
        
        assert set(user1_orgs) == {"OrgA", "OrgB"}
        assert set(user2_orgs) == {"OrgC", "OrgD"}


class TestConcurrency:
    """Test concurrent access to TokenStore."""

    def test_concurrent_writes_different_users(self, token_store):
        """Test concurrent writes for different users."""
        import threading
        
        def store_tokens(user_id, org_count):
            for i in range(org_count):
                token_store.store_token(
                    user_id=user_id,
                    org_name=f"Org{i}",
                    token=f"token_{user_id}_{i}"
                )
        
        threads = [
            threading.Thread(target=store_tokens, args=("user1", 10)),
            threading.Thread(target=store_tokens, args=("user2", 10)),
            threading.Thread(target=store_tokens, args=("user3", 10)),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify all tokens were stored correctly
        for user_id in ["user1", "user2", "user3"]:
            tokens = token_store.get_user_tokens(user_id)
            assert len(tokens) == 10

    def test_concurrent_reads(self, token_store):
        """Test concurrent reads are safe."""
        import threading
        
        # Setup: Store some tokens
        token_store.store_token("user1", "OrgA", "token_a")
        token_store.store_token("user1", "OrgB", "token_b")
        
        results = []
        
        def read_tokens():
            tokens = token_store.get_user_tokens("user1")
            results.append(len(tokens))
        
        threads = [threading.Thread(target=read_tokens) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All reads should return the same result
        assert all(count == 2 for count in results)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_strings_allowed(self, token_store):
        """Test that empty strings are technically allowed by TokenStore.
        
        Note: Validation should happen at a higher layer (e.g., use cases).
        """
        # TokenStore itself doesn't validate - it just stores
        # This is by design - validation happens in use cases
        token_store.store_token("", "OrgA", "token")
        result = token_store.get_token("", "OrgA")
        assert result == "token"

    def test_special_characters_in_org_name(self, token_store):
        """Test handling of special characters in org names."""
        special_orgs = [
            "Org-With-Dashes",
            "Org_With_Underscores",
            "Org With Spaces",
            "Org.With.Dots",
            "Org@Special#Chars",
        ]
        
        for org_name in special_orgs:
            token_store.store_token("user123", org_name, f"token_{org_name}")
        
        tokens = token_store.get_user_tokens("user123")
        assert len(tokens) == len(special_orgs)
        for org_name in special_orgs:
            assert org_name in tokens

    def test_very_long_token(self, token_store):
        """Test handling of very long tokens."""
        long_token = "x" * 10000
        token_store.store_token("user123", "OrgA", long_token)
        
        tokens = token_store.get_user_tokens("user123")
        assert tokens["OrgA"] == long_token

    def test_unicode_org_names(self, token_store):
        """Test handling of Unicode organization names."""
        unicode_orgs = [
            "组织名称",  # Chinese
            "Организация",  # Russian
            "المنظمة",  # Arabic
            "संगठन",  # Hindi
        ]
        
        for org_name in unicode_orgs:
            token_store.store_token("user123", org_name, f"token_{org_name}")
        
        tokens = token_store.get_user_tokens("user123")
        assert len(tokens) == len(unicode_orgs)
