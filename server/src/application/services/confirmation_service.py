"""
Confirmation service for managing destructive operation confirmations.

This service generates and validates time-limited confirmation tokens
to prevent accidental execution of destructive operations like deleting
or closing projects.
"""

import hashlib
import json
import secrets
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ConfirmationService:
    """
    Service for generating and validating confirmation tokens.
    
    Uses HMAC-style signatures with time-based expiration to ensure
    tokens are secure and time-limited.
    """
    
    def __init__(self, secret_key: Optional[str] = None, default_expiry_minutes: int = 5):
        """
        Initialize the confirmation service.
        
        Args:
            secret_key: Secret key for signing tokens. If None, generates a new one.
            default_expiry_minutes: Default token expiration time in minutes.
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.default_expiry_minutes = default_expiry_minutes
        self._used_tokens: Dict[str, float] = {}  # Track used tokens with cleanup timestamp
        
    def generate_token(
        self,
        action: str,
        data: Dict,
        expires_minutes: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Generate a confirmation token for a destructive operation.
        
        Args:
            action: The action type (e.g., "delete_projects", "close_projects")
            data: Data associated with the action (e.g., {"project_ids": [...]})
            expires_minutes: Token expiration time in minutes (default: service default)
            
        Returns:
            Dictionary containing:
                - token: The confirmation token string
                - expires_at: ISO timestamp when token expires
                - expires_in_seconds: Seconds until expiration
        """
        expires_minutes = expires_minutes or self.default_expiry_minutes
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        expires_timestamp = expires_at.timestamp()
        
        # Create payload
        payload = {
            "action": action,
            "data": data,
            "expires_at": expires_timestamp,
            "issued_at": datetime.utcnow().timestamp(),
            "nonce": secrets.token_hex(8)  # Prevent replay attacks
        }
        
        # Encode payload
        payload_json = json.dumps(payload, sort_keys=True)
        payload_encoded = payload_json.encode('utf-8')
        
        # Create signature
        signature = hashlib.pbkdf2_hmac(
            'sha256',
            payload_encoded,
            self.secret_key.encode('utf-8'),
            100000
        ).hex()
        
        # Combine payload and signature
        token = f"{payload_json}|{signature}"
        
        return {
            "token": token,
            "expires_at": expires_at.isoformat() + "Z",
            "expires_in_seconds": int(expires_minutes * 60)
        }
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate and extract data from a confirmation token.
        
        Args:
            token: The confirmation token to validate
            
        Returns:
            Dictionary containing action and data from the token
            
        Raises:
            ValueError: If token is invalid, expired, or already used
        """
        try:
            # Split token into payload and signature
            parts = token.split("|")
            if len(parts) != 2:
                raise ValueError("Invalid token format")
            
            payload_json, provided_signature = parts
            
            # Verify signature
            payload_encoded = payload_json.encode('utf-8')
            expected_signature = hashlib.pbkdf2_hmac(
                'sha256',
                payload_encoded,
                self.secret_key.encode('utf-8'),
                100000
            ).hex()
            
            if not secrets.compare_digest(provided_signature, expected_signature):
                raise ValueError("Invalid token signature")
            
            # Parse payload
            payload = json.loads(payload_json)
            
            # Check if token has been used
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            if token_hash in self._used_tokens:
                raise ValueError("Token has already been used")
            
            # Check expiration
            expires_at = payload["expires_at"]
            if datetime.utcnow().timestamp() > expires_at:
                raise ValueError("Token has expired")
            
            # Mark token as used
            self._used_tokens[token_hash] = time.time()
            self._cleanup_old_tokens()
            
            return {
                "action": payload["action"],
                "data": payload["data"]
            }
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid token format: {str(e)}")
    
    def _cleanup_old_tokens(self):
        """Remove used tokens older than 1 hour to prevent memory growth."""
        cutoff_time = time.time() - 3600  # 1 hour ago
        self._used_tokens = {
            token: timestamp
            for token, timestamp in self._used_tokens.items()
            if timestamp > cutoff_time
        }
    
    def create_preview_response(
        self,
        action: str,
        items: List[Dict],
        item_type: str,
        warnings: List[str],
        token_info: Dict
    ) -> Dict:
        """
        Create a standardized preview response for destructive operations.
        
        Args:
            action: The action being previewed (e.g., "delete", "close")
            items: List of items that would be affected
            item_type: Type of items (e.g., "projects", "users")
            warnings: List of warning messages
            token_info: Token information from generate_token()
            
        Returns:
            Standardized preview response dictionary
        """
        return {
            "action": "preview",
            "operation": action,
            "item_type": item_type,
            "items": items,
            "item_count": len(items),
            "warnings": warnings,
            "confirmation_required": True,
            "confirmation_token": token_info["token"],
            "token_expires_at": token_info["expires_at"],
            "token_expires_in_seconds": token_info["expires_in_seconds"],
            "next_step": f"To proceed, call confirm_{action}_{item_type} with the confirmation_token"
        }
