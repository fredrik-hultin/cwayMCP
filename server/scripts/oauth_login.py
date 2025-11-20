#!/usr/bin/env python3
"""Interactive OAuth2 login for local development."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))
sys.path.insert(0, str(server_dir / "src"))

from config.settings import settings
from infrastructure.auth.token_provider import OAuth2TokenProvider
from infrastructure.auth.token_cache import TokenCache


async def main():
    """Interactive OAuth2 login."""
    print("🔐 Cway MCP Server - OAuth2 Login\n")
    
    # Check configuration
    if not settings.azure_tenant_id or not settings.azure_client_id:
        print("❌ OAuth2 not configured!")
        print("\nPlease set these environment variables in your .env file:")
        print("  AUTH_METHOD=oauth2")
        print("  AZURE_TENANT_ID=your-tenant-id")
        print("  AZURE_CLIENT_ID=your-client-id")
        print("  USE_DEVICE_CODE_FLOW=true")
        print("\nFor server-to-server (non-interactive), also set:")
        print("  AZURE_CLIENT_SECRET=your-secret")
        sys.exit(1)
    
    print(f"📋 Configuration:")
    print(f"  Tenant ID: {settings.azure_tenant_id}")
    print(f"  Client ID: {settings.azure_client_id}")
    print(f"  Auth Method: {settings.auth_method}")
    print(f"  Device Code Flow: {settings.use_device_code_flow}")
    print()
    
    # Initialize token provider
    token_provider = OAuth2TokenProvider(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
        scope=settings.oauth2_scope,
        use_device_code_flow=settings.use_device_code_flow or not settings.azure_client_secret,
    )
    
    try:
        print("🔄 Acquiring token...\n")
        
        # This will prompt for device code if needed
        token = await token_provider.get_token()
        
        print("\n✅ Login successful!")
        print(f"Token acquired and cached: {token[:20]}...")
        print(f"\nToken cache location: ~/.cway_mcp/token_cache.json")
        print("\n🎉 You can now use the MCP server without re-authenticating")
        print("   (until the token expires)")
        
    except Exception as e:
        print(f"\n❌ Login failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
