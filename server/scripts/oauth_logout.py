#!/usr/bin/env python3
"""Clear OAuth2 token cache."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.infrastructure.auth.token_cache import TokenCache


def main():
    """Clear token cache."""
    print("🔐 Cway MCP Server - Clear OAuth2 Cache\n")
    
    cache = TokenCache()
    cache_path = cache.cache_file
    
    if cache_path.exists():
        print(f"📁 Cache file: {cache_path}")
        confirm = input("Clear cache? (y/N): ").lower()
        
        if confirm == 'y':
            cache.clear()
            print("✅ Token cache cleared successfully")
            print("   You'll need to login again next time")
        else:
            print("❌ Cancelled")
    else:
        print(f"ℹ️  No cache file found at {cache_path}")
        print("   Nothing to clear")


if __name__ == "__main__":
    main()
