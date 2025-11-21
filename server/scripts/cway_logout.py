#!/usr/bin/env python3
"""Interactive CLI script for Cway logout."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError
from src.application.auth_use_cases import AuthUseCases
from config.settings import settings


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("  Cway MCP Server - Logout")
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


async def interactive_logout():
    """Run interactive logout flow."""
    print_banner()
    
    # Validate configuration
    if settings.auth_method != "oauth2":
        print_error(
            f"Authentication method is '{settings.auth_method}', but oauth2 is required.\n"
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
        
        # List authenticated users
        users_result = await auth_use_cases.list_authenticated_users()
        
        if not users_result["success"]:
            print_error(users_result["message"])
            return False
        
        if not users_result["users"]:
            print_info("No authenticated users found.")
            return True
        
        # Show authenticated users
        print(f"Found {users_result['count']} authenticated user(s):\n")
        for i, user in enumerate(users_result["users"], 1):
            print(f"  {i}. {user}")
        
        print("\nOptions:")
        print("  • Enter a number to logout specific user")
        print("  • Enter 'all' to logout all users")
        print("  • Press Ctrl+C to cancel\n")
        
        choice = input("> ").strip().lower()
        
        if not choice:
            print_error("No choice provided")
            return False
        
        users_to_logout = []
        
        if choice == "all":
            users_to_logout = users_result["users"]
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(users_result["users"]):
                    users_to_logout = [users_result["users"][index]]
                else:
                    print_error("Invalid number")
                    return False
            except ValueError:
                print_error("Invalid input. Enter a number or 'all'")
                return False
        
        # Confirm logout
        if len(users_to_logout) > 1:
            print(f"\n⚠️  You are about to logout {len(users_to_logout)} users:")
            for user in users_to_logout:
                print(f"  • {user}")
            print("\nAre you sure? (yes/no)")
            confirm = input("> ").strip().lower()
            if confirm not in ["yes", "y"]:
                print_info("Logout cancelled")
                return False
        
        # Logout users
        success_count = 0
        for username in users_to_logout:
            print_info(f"Logging out {username}...")
            result = await auth_use_cases.logout(username)
            
            if result["success"]:
                print_success(f"{username} logged out successfully")
                success_count += 1
            else:
                print_error(f"Failed to logout {username}: {result['message']}")
        
        if success_count > 0:
            print(f"\n{'=' * 60}")
            print(f"  ✅ Successfully logged out {success_count} user(s)")
            print(f"{'=' * 60}\n")
            return True
        else:
            print_error("No users were logged out")
            return False
        
    except TokenManagerError as e:
        print_error(f"Authentication error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Logout cancelled by user")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    try:
        success = await interactive_logout()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
