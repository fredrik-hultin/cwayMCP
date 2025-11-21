#!/usr/bin/env python3
"""Helper script for managing Cway API tokens and organizations."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def main():
    """Display current token configuration and help."""
    print("\n" + "=" * 80)
    print("Cway MCP Server - Token Management")
    print("=" * 80 + "\n")
    
    # Check if any tokens are configured
    if not settings.cway_api_token and not settings.org_tokens:
        print("❌ No API tokens configured!\n")
        print("To configure tokens:")
        print("1. Get API tokens from: https://app.cway.se/settings/api")
        print("2. Add to server/.env file:\n")
        print("   # Primary/default token")
        print("   CWAY_API_TOKEN=your_token_here\n")
        print("   # Additional org tokens (optional)")
        print("   CWAY_TOKEN_COLLABRA=collabra_token")
        print("   CWAY_TOKEN_CLIENT_A=client_a_token\n")
        sys.exit(1)
    
    # Display configured tokens
    print("📋 Configured Organizations:\n")
    
    orgs = settings.list_organizations()
    active_org = settings.active_org or "default"
    
    if not orgs:
        print("   (none)")
    else:
        for org in orgs:
            marker = "→" if org == active_org else " "
            status = "(active)" if org == active_org else ""
            print(f"   {marker} {org} {status}")
    
    print("\n" + "-" * 80)
    print("📍 Active Organization:", active_org)
    print("-" * 80 + "\n")
    
    # Display usage instructions
    print("To switch organizations:")
    print("  Use MCP tools: list_organizations, switch_organization, get_active_organization\n")
    
    print("To add/modify tokens:")
    print("  1. Edit server/.env file")
    print("  2. Add: CWAY_TOKEN_<ORG_NAME>=<token>")
    print("  3. Restart the MCP server\n")
    
    print("To get new tokens:")
    print("  1. Visit: https://app.cway.se/settings/api")
    print("  2. Select organization")
    print("  3. Generate/copy API token")
    print("  4. Add to .env file\n")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
