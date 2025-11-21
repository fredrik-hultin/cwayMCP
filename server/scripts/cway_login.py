#!/usr/bin/env python3
"""Interactive CLI script for Cway authentication with Entra ID."""

import asyncio
import sys
import webbrowser
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.auth.token_manager import TokenManager, TokenManagerError
from src.application.auth_use_cases import AuthUseCases
from config.settings import settings


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 60)
    print("  Cway MCP Server - User Authentication")
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


async def interactive_login():
    """Run interactive login flow."""
    print_banner()
    
    # Validate configuration
    if settings.auth_method != "oauth2":
        print_error(
            f"Authentication method is '{settings.auth_method}', but oauth2 is required.\n"
            f"Please set AUTH_METHOD=oauth2 in your .env file."
        )
        return False
    
    if not settings.azure_tenant_id or not settings.azure_client_id:
        print_error(
            "Azure AD configuration is missing.\n"
            "Please set AZURE_TENANT_ID and AZURE_CLIENT_ID in your .env file."
        )
        return False
    
    # Get username
    print("Enter your email address:")
    username = input("> ").strip()
    
    if not username or "@" not in username:
        print_error("Invalid email address")
        return False
    
    try:
        # Initialize authentication
        token_manager = TokenManager(
            api_url=settings.cway_api_url,
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id
        )
        auth_use_cases = AuthUseCases(token_manager)
        
        # Initiate login
        print_info(f"Initiating login for {username}...")
        result = await auth_use_cases.initiate_login(username)
        
        if not result.success:
            print_error(result.message)
            return False
        
        print("\n" + "-" * 60)
        print("📋 Authorization URL:")
        print(result.authorization_url)
        print("-" * 60 + "\n")
        
        print("Opening browser for authentication...")
        try:
            webbrowser.open(result.authorization_url)
            print_success("Browser opened!")
        except Exception as e:
            print_info(f"Could not open browser automatically: {e}")
            print("Please copy and paste the URL above into your browser.")
        
        print("\nAfter authenticating in your browser:")
        print("1. You will be redirected to a URL")
        print("2. Copy the FULL redirect URL from your browser")
        print("3. Paste it below\n")
        
        print("Enter the redirect URL (or press Ctrl+C to cancel):")
        redirect_url = input("> ").strip()
        
        if not redirect_url:
            print_error("No redirect URL provided")
            return False
        
        # Parse authorization code from redirect URL
        # Format: http://localhost:8080/callback?code=XXX&state=YYY
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(redirect_url)
            params = parse_qs(parsed.query)
            
            if "code" not in params:
                print_error("No authorization code found in redirect URL")
                return False
            
            authorization_code = params["code"][0]
            returned_state = params.get("state", [None])[0]
            
            if returned_state != result.state:
                print_error("State parameter mismatch - possible security issue")
                return False
            
        except Exception as e:
            print_error(f"Failed to parse redirect URL: {e}")
            return False
        
        # Complete login
        print_info("Exchanging authorization code for tokens...")
        completion_result = await auth_use_cases.complete_login(
            username, authorization_code, result.state
        )
        
        if not completion_result.success:
            print_error(completion_result.message)
            return False
        
        print_success(completion_result.message)
        
        # Show authentication status
        whoami_result = await auth_use_cases.whoami(username)
        print("\n" + "-" * 60)
        print(f"👤 User: {whoami_result.username}")
        print(f"🔐 Status: {'Authenticated' if whoami_result.authenticated else 'Not authenticated'}")
        if whoami_result.expires_in_minutes:
            print(f"⏰ Token expires in: {whoami_result.expires_in_minutes} minutes")
        print("-" * 60 + "\n")
        
        print("You can now use the Cway MCP Server with your credentials.")
        print(f"Set CWAY_USERNAME={username} in your environment to use this account.\n")
        
        return True
        
    except TokenManagerError as e:
        print_error(f"Authentication error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Login cancelled by user")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    try:
        success = await interactive_login()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
