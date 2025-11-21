"""Organization management use cases."""

import os
from dataclasses import dataclass
from config.settings import settings


@dataclass
class OrganizationInfo:
    """Organization information."""
    name: str
    is_active: bool
    has_token: bool


class OrganizationUseCases:
    """Use cases for managing multiple organizations."""
    
    def list_organizations(self) -> list[OrganizationInfo]:
        """List all configured organizations."""
        orgs = []
        
        # Add default org if primary token exists
        if settings.cway_api_token:
            orgs.append(OrganizationInfo(
                name="default",
                is_active=(settings.active_org is None),
                has_token=True
            ))
        
        # Add configured organization tokens
        for org_name in settings.org_tokens.keys():
            orgs.append(OrganizationInfo(
                name=org_name,
                is_active=(settings.active_org == org_name),
                has_token=True
            ))
        
        return orgs
    
    def get_active_organization(self) -> str:
        """Get the currently active organization."""
        return settings.active_org or "default"
    
    def switch_organization(self, org_name: str) -> dict:
        """
        Switch to a different organization.
        
        Args:
            org_name: Organization name to switch to ("default" or a configured org)
            
        Returns:
            Dict with success status and message
        """
        # Validate organization exists
        if org_name == "default":
            if not settings.cway_api_token:
                return {
                    "success": False,
                    "message": "No default token configured (CWAY_API_TOKEN)"
                }
            # Set to None to use default
            settings.active_org = None
        else:
            if org_name not in settings.org_tokens:
                available = settings.list_organizations()
                return {
                    "success": False,
                    "message": f"Organization '{org_name}' not found. Available: {', '.join(available)}"
                }
            settings.active_org = org_name
        
        return {
            "success": True,
            "message": f"Switched to organization: {org_name}",
            "active_org": settings.active_org or "default"
        }
