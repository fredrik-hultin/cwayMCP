"""
Category Repository - Handles categories, brands, and specifications.

Single Responsibility: Category, brand, and specification data access only.
"""

from typing import Any, Dict, List, Optional
import logging

from src.infrastructure.graphql_client import CwayAPIError
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository):
    """Repository for categories, brands, and specifications."""
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all artwork categories."""
        query = """
        query GetCategories {
            categories {
                id
                name
                description
                color
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("categories", [])
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            raise CwayAPIError(f"Failed to get categories: {e}")
    
    async def get_brands(self) -> List[Dict[str, Any]]:
        """Get all brands."""
        query = """
        query GetBrands {
            brands {
                id
                name
                description
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("brands", [])
            
        except Exception as e:
            logger.error(f"Failed to get brands: {e}")
            raise CwayAPIError(f"Failed to get brands: {e}")
    
    async def get_print_specifications(self) -> List[Dict[str, Any]]:
        """Get all print specifications."""
        query = """
        query GetPrintSpecifications {
            printSpecifications {
                id
                name
                description
                width
                height
                unit
            }
        }
        """
        
        try:
            result = await self._execute_query(query, {})
            return result.get("printSpecifications", [])
            
        except Exception as e:
            logger.error(f"Failed to get print specifications: {e}")
            raise CwayAPIError(f"Failed to get print specifications: {e}")
    
    async def create_category(self, name: str, description: Optional[str] = None, 
                             color: Optional[str] = None) -> Dict[str, Any]:
        """Create a new category."""
        mutation = """
        mutation CreateCategory($input: CategoryInput!) {
            createCategory(input: $input) {
                id
                name
                description
                color
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "description": description,
                    "color": color
                }
            })
            return result.get("createCategory", {})
            
        except Exception as e:
            logger.error(f"Failed to create category: {e}")
            raise CwayAPIError(f"Failed to create category: {e}")
    
    async def create_brand(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new brand."""
        mutation = """
        mutation CreateBrand($input: BrandInput!) {
            createBrand(input: $input) {
                id
                name
                description
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "description": description
                }
            })
            return result.get("createBrand", {})
            
        except Exception as e:
            logger.error(f"Failed to create brand: {e}")
            raise CwayAPIError(f"Failed to create brand: {e}")
    
    async def create_print_specification(self, name: str, width: float, height: float,
                                        unit: str = "mm", description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new print specification."""
        mutation = """
        mutation CreatePrintSpecification($input: PrintSpecificationInput!) {
            createPrintSpecification(input: $input) {
                id
                name
                description
                width
                height
                unit
            }
        }
        """
        
        try:
            result = await self._execute_mutation(mutation, {
                "input": {
                    "name": name,
                    "width": width,
                    "height": height,
                    "unit": unit,
                    "description": description
                }
            })
            return result.get("createPrintSpecification", {})
            
        except Exception as e:
            logger.error(f"Failed to create print specification: {e}")
            raise CwayAPIError(f"Failed to create print specification: {e}")
