"""
Token storage system with encryption for multi-user support.

Stores user tokens in SQLite database with Fernet encryption.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet

from config.settings import settings


class TokenStore:
    """Manages encrypted token storage for multiple users and organizations."""

    def __init__(self, db_path: Optional[str] = None, encryption_key: Optional[bytes] = None):
        """
        Initialize token store.

        Args:
            db_path: Path to SQLite database (default from settings)
            encryption_key: Fernet encryption key (default from settings)
        """
        self.db_path = db_path or settings.token_db_path
        self.encryption_key = encryption_key or self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._init_database()

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        if settings.token_encryption_key:
            # Use provided key (must be base64-encoded Fernet key)
            return settings.token_encryption_key.encode()
        else:
            # Generate new key for development
            # WARNING: This means tokens will be lost on restart!
            return Fernet.generate_key()

    def _init_database(self) -> None:
        """Initialize SQLite database with schema."""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_tokens (
                    user_id TEXT NOT NULL,
                    org_name TEXT NOT NULL,
                    encrypted_token TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_used TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, org_name)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_id ON user_tokens(user_id)
                """
            )
            conn.commit()

    def store_token(self, user_id: str, org_name: str, token: str) -> None:
        """
        Store or update a token for a user and organization.

        Args:
            user_id: User identifier
            org_name: Organization name
            token: Plain text API token
        """
        encrypted_token = self.cipher.encrypt(token.encode()).decode()
        now = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_tokens (user_id, org_name, encrypted_token, created_at, last_used)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, org_name) DO UPDATE SET
                    encrypted_token = excluded.encrypted_token,
                    last_used = excluded.last_used
                """,
                (user_id, org_name, encrypted_token, now, now),
            )
            conn.commit()

    def get_token(self, user_id: str, org_name: str) -> Optional[str]:
        """
        Retrieve a decrypted token for a user and organization.

        Args:
            user_id: User identifier
            org_name: Organization name

        Returns:
            Decrypted token or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT encrypted_token FROM user_tokens
                WHERE user_id = ? AND org_name = ?
                """,
                (user_id, org_name),
            )
            row = cursor.fetchone()

        if row:
            encrypted_token = row[0]
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        return None

    def get_user_tokens(self, user_id: str) -> Dict[str, str]:
        """
        Get all tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary mapping org_name -> decrypted_token
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT org_name, encrypted_token FROM user_tokens
                WHERE user_id = ?
                ORDER BY org_name
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        tokens = {}
        for org_name, encrypted_token in rows:
            token = self.cipher.decrypt(encrypted_token.encode()).decode()
            tokens[org_name] = token

        return tokens

    def list_orgs(self, user_id: str) -> List[str]:
        """
        List all organization names for a user.

        Args:
            user_id: User identifier

        Returns:
            List of organization names
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT org_name FROM user_tokens
                WHERE user_id = ?
                ORDER BY org_name
                """,
                (user_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def delete_token(self, user_id: str, org_name: str) -> bool:
        """
        Delete a token for a user and organization.

        Args:
            user_id: User identifier
            org_name: Organization name

        Returns:
            True if token was deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM user_tokens
                WHERE user_id = ? AND org_name = ?
                """,
                (user_id, org_name),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_last_used(self, user_id: str, org_name: str) -> None:
        """
        Update the last_used timestamp for a token.

        Args:
            user_id: User identifier
            org_name: Organization name
        """
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE user_tokens
                SET last_used = ?
                WHERE user_id = ? AND org_name = ?
                """,
                (now, user_id, org_name),
            )
            conn.commit()


# Global instance
_token_store: Optional[TokenStore] = None


def get_token_store() -> TokenStore:
    """Get or create the global token store instance."""
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store
