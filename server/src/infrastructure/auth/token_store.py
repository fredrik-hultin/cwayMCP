"""Secure per-user token storage with encryption."""

import json
import logging
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class TokenStore:
    """Manages secure storage of per-user authentication tokens."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize token store.
        
        Args:
            storage_dir: Directory for token storage (default: ~/.cway_mcp/tokens)
        """
        self.storage_dir = storage_dir or Path.home() / ".cway_mcp" / "tokens"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate encryption key from system-specific data
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        
        logger.info(f"TokenStore initialized at {self.storage_dir}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for token storage.
        
        Uses PBKDF2 to derive key from system-specific data.
        """
        key_file = self.storage_dir.parent / ".token_key"
        
        if key_file.exists():
            return key_file.read_bytes()
        
        # Generate key from system-specific data
        # In production, consider using keyring/keychain
        system_data = f"{os.getuid()}-{Path.home()}".encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"cway_mcp_salt",  # Fixed salt for deterministic key
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(system_data))
        
        # Save key with restricted permissions
        key_file.write_bytes(key)
        os.chmod(key_file, 0o600)
        
        logger.info("Created new encryption key")
        return key
    
    def _username_to_filename(self, username: str) -> str:
        """Convert username to safe filename using hash."""
        username_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
        return f"{username_hash}.json"
    
    def _get_token_file(self, username: str) -> Path:
        """Get token file path for username."""
        filename = self._username_to_filename(username)
        return self.storage_dir / filename
    
    def save_tokens(
        self,
        username: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> None:
        """
        Save tokens for user with encryption.
        
        Args:
            username: User's email/username
            access_token: Cway JWT access token
            refresh_token: Cway JWT refresh token
            expires_in: Token expiry time in seconds
        """
        token_file = self._get_token_file(username)
        
        # Calculate expiry timestamp
        expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        
        token_data = {
            "username": username,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "created_at": datetime.now().isoformat(),
        }
        
        try:
            # Encrypt token data
            json_data = json.dumps(token_data).encode()
            encrypted_data = self._cipher.encrypt(json_data)
            
            # Write to file with restricted permissions
            token_file.write_bytes(encrypted_data)
            os.chmod(token_file, 0o600)
            
            logger.info(f"Saved tokens for {username} (expires: {expires_at})")
        except Exception as e:
            logger.error(f"Failed to save tokens for {username}: {e}")
            raise TokenStoreError(f"Failed to save tokens: {e}")
    
    def get_tokens(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tokens for user.
        
        Args:
            username: User's email/username
            
        Returns:
            Token data dict or None if not found/expired
        """
        token_file = self._get_token_file(username)
        
        if not token_file.exists():
            logger.debug(f"No tokens found for {username}")
            return None
        
        try:
            # Read and decrypt token data
            encrypted_data = token_file.read_bytes()
            decrypted_data = self._cipher.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            # Validate username matches
            if token_data.get("username") != username:
                logger.warning(f"Username mismatch in token file for {username}")
                return None
            
            logger.debug(f"Retrieved tokens for {username}")
            return token_data
            
        except InvalidToken:
            logger.error(f"Token decryption failed for {username} (corrupted file)")
            # Delete corrupted file
            token_file.unlink(missing_ok=True)
            return None
        except json.JSONDecodeError:
            logger.error(f"Token JSON parsing failed for {username}")
            token_file.unlink(missing_ok=True)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve tokens for {username}: {e}")
            return None
    
    def is_token_valid(self, username: str) -> bool:
        """
        Check if user has valid (non-expired) tokens.
        
        Args:
            username: User's email/username
            
        Returns:
            True if valid tokens exist, False otherwise
        """
        token_data = self.get_tokens(username)
        
        if not token_data:
            return False
        
        try:
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            # Consider valid if more than 1 minute remaining
            return expires_at > datetime.now() + timedelta(minutes=1)
        except (KeyError, ValueError):
            logger.error(f"Invalid expires_at in token data for {username}")
            return False
    
    def delete_tokens(self, username: str) -> bool:
        """
        Delete tokens for user (logout).
        
        Args:
            username: User's email/username
            
        Returns:
            True if deleted, False if not found
        """
        token_file = self._get_token_file(username)
        
        if token_file.exists():
            token_file.unlink()
            logger.info(f"Deleted tokens for {username}")
            return True
        
        logger.debug(f"No tokens to delete for {username}")
        return False
    
    def list_stored_users(self) -> list[str]:
        """
        List usernames with stored tokens.
        
        Returns:
            List of usernames
        """
        users = []
        
        for token_file in self.storage_dir.glob("*.json"):
            try:
                encrypted_data = token_file.read_bytes()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                token_data = json.loads(decrypted_data.decode())
                
                if username := token_data.get("username"):
                    users.append(username)
            except Exception as e:
                logger.warning(f"Failed to read token file {token_file}: {e}")
        
        return users
    
    def clear_all_tokens(self) -> int:
        """
        Clear all stored tokens (admin/debug).
        
        Returns:
            Number of token files deleted
        """
        count = 0
        
        for token_file in self.storage_dir.glob("*.json"):
            token_file.unlink()
            count += 1
        
        logger.info(f"Cleared {count} token files")
        return count


class TokenStoreError(Exception):
    """Exception raised for token storage errors."""
    pass
