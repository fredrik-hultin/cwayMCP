#!/usr/bin/env python3
"""CLI script to check Cway authentication status."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError
from src.application.auth_use_cases import AuthUseCases
from config.settings import settings


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("  Cway MCP Server - Authentication Status")
    print("=" * 60 + "\n")


def print_error(message: str):
    """Print error message."""
    print(f"\n❌ Error: {message}\n")


def print_success(message: str):
    """Print success message."""
    print(f"\n✅ {message}\n")


def print_info(message: str):
    """Print info message."""
    print(f"\nℹ️  {message}\n")


async def check_auth_status():
    """Check authentication status."""
    print_banner()
    
    # Validate configuration
    if settings.auth_method != "oauth2":
        print_error(
            f"Authentication method is '{settings.auth_method}'.\n"
            f"This script is only for oauth2 mode."
        )
        return False
    
    try:
        # Initialize authentication
        token_manager = TokenManager(
            api_url=settings.cway_api_url,
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id
        )
        auth_use_cases = AuthUseCases(token_manager)
        
        # Check for CWAY_USERNAME environment variable
        username = os.environ.get("CWAY_USERNAME")
        
        if username:
            print(f"Checking authentication status for: {username}\n")
            result = await auth_use_cases.whoami(username)
            
            print("-" * 60)
            print(f"👤 User: {result.username}")
            print(f"🔐 Status: {'✅ Authenticated' if result.authenticated else '❌ Not authenticated'}")
            
            if result.authenticated and result.expires_in_minutes is not None:
                print(f"⏰ Token expires in: {result.expires_in_minutes} minutes")
                if result.expires_at:
                    print(f"📅 Expires at: {result.expires_at}")
            
            print("-" * 60 + "\n")
            
            if not result.authenticated:
                print("To authenticate, run: python scripts/cway_login.py\n")
            
            return result.authenticated
        else:
            # No specific user, show all authenticated users
            print("No CWAY_USERNAME environment variable set.")
            print("Showing all authenticated users...\n")
            
            users_result = await auth_use_cases.list_authenticated_users()
            
            if not users_result["success"]:
                print_error(users_result["message"])
                return False
            
            if not users_result["users"]:
                print_info("No authenticated users found.")
                print("To authenticate, run: python scripts/cway_login.py\n")
                return False
            
            print(f"Found {users_result['count']} authenticated user(s):\n")
            
            for i, user in enumerate(users_result["users"], 1):
                result = await auth_use_cases.whoami(user)
                
                status_icon = "✅" if result.authenticated else "❌"
                expiry = f" (expires in {result.expires_in_minutes}m)" if result.expires_in_minutes else ""
                
                print(f"  {i}. {status_icon} {user}{expiry}")
            
            print("\n" + "-" * 60)
            print("To use a specific user, set CWAY_USERNAME environment variable:")
            print(f"  export CWAY_USERNAME={users_result['users'][0]}")
            print("-" * 60 + "\n")
            
            return True
        
    except TokenManagerError as e:
        print_error(f"Authentication error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    try:
        success = await check_auth_status()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
