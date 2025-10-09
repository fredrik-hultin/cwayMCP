"""Tests for domain repository abstract classes."""

import pytest

from src.domain.repositories import ProjectRepository, UserRepository


class TestRepositoryAbstractions:
    """Test that repository abstract base classes behave correctly."""
    
    def test_project_repository_cannot_be_instantiated(self) -> None:
        """Test that ProjectRepository cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProjectRepository()  # type: ignore
            
    def test_user_repository_cannot_be_instantiated(self) -> None:
        """Test that UserRepository cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            UserRepository()  # type: ignore
            
    def test_project_repository_has_required_abstract_methods(self) -> None:
        """Test that ProjectRepository has all required abstract methods."""
        abstract_methods = ProjectRepository.__abstractmethods__
        expected_methods = {
            'get_all', 'get_by_id', 'create', 'update', 'delete'
        }
        assert abstract_methods == expected_methods
        
    def test_user_repository_has_required_abstract_methods(self) -> None:
        """Test that UserRepository has all required abstract methods."""
        abstract_methods = UserRepository.__abstractmethods__
        expected_methods = {
            'get_all', 'get_by_id', 'get_by_email', 'create', 'update', 'delete'
        }
        assert abstract_methods == expected_methods