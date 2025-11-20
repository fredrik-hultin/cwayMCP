"""
Base repository class providing common GraphQL client functionality.

All domain-specific repositories inherit from this base class to access
the GraphQL client and common utility methods.
"""

from typing import Any, Dict
import logging

from src.infrastructure.graphql_client import CwayGraphQLClient

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Abstract base repository providing GraphQL client access.
    
    All domain repositories (Project, User, Artwork, etc.) inherit from
    this class to access the GraphQL client and common utilities.
    
    Follows the Repository pattern from Domain-Driven Design.
    """
    
    def __init__(self, graphql_client: CwayGraphQLClient):
        """
        Initialize base repository with GraphQL client.
        
        Args:
            graphql_client: Configured CwayGraphQLClient instance
        """
        self.graphql_client = graphql_client
        self.logger = logger
    
    async def _execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query result data
        """
        return await self.graphql_client.execute_query(query, variables)
    
    async def _execute_mutation(self, mutation: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.
        
        Args:
            mutation: GraphQL mutation string
            variables: Mutation variables
            
        Returns:
            Mutation result data
        """
        return await self.graphql_client.execute_mutation(mutation, variables)
