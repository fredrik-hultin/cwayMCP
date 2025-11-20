"""Token caching implementation for OAuth2 tokens."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from msal import SerializableTokenCache


logger = logging.getLogger(__name__)


class TokenCache:
    """Token cache with persistent storage."""
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize token cache.
        
        Args:
            cache_file: Path to cache file (defaults to ~/.cway_mcp_token_cache.json)
        """
        if cache_file is None:
            cache_dir = Path.home() / ".cway_mcp"
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / "token_cache.json"
        
        self.cache_file = cache_file
        self.msal_cache = SerializableTokenCache()
        
        # Load existing cache
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    cache_data = f.read()
                    self.msal_cache.deserialize(cache_data)
                logger.info(f"Loaded token cache from {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to load token cache: {e}")
    
    def save(self) -> None:
        """Save token cache to disk."""
        if self.msal_cache.has_state_changed:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_file, "w") as f:
                    f.write(self.msal_cache.serialize())
                # Secure the cache file (owner read/write only)
                os.chmod(self.cache_file, 0o600)
                logger.debug(f"Saved token cache to {self.cache_file}")
            except Exception as e:
                logger.error(f"Failed to save token cache: {e}")
    
    def clear(self) -> None:
        """Clear the token cache."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            self.msal_cache = SerializableTokenCache()
            logger.info("Token cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear token cache: {e}")
