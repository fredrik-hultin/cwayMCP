"""
Tests for Phase 2.3: Categories, Brands, Specifications, and Shares tools
Tests 10 tools with comprehensive coverage for all tool types
"""
import pytest
from unittest.mock import AsyncMock
from src.infrastructure.cway_repositories import CwayProjectRepository, CwayCategoryRepository
from src.infrastructure.graphql_client import CwayAPIError


@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client"""
    mock = AsyncMock()
    mock.execute_query = AsyncMock()
    mock.execute_mutation = AsyncMock()
    return mock


@pytest.fixture
def category_repo(mock_graphql_client):
    """Create a CwayCategoryRepository with mocked client"""
    return CwayCategoryRepository(mock_graphql_client)


@pytest.fixture
def project_repo(mock_graphql_client):
    """Create a CwayProjectRepository with mocked client"""
    return CwayProjectRepository(mock_graphql_client)


# ========================================
# Category Tools Tests
# ========================================

@pytest.mark.asyncio
async def test_get_categories_success(category_repo, mock_graphql_client):
    """Test successful retrieval of categories"""
    mock_categories = [
        {"id": "cat1", "name": "Print", "description": "Print materials"},
        {"id": "cat2", "name": "Digital", "description": "Digital assets"}
    ]
    mock_graphql_client.execute_query.return_value = {
        "categories": mock_categories
    }
    
    result = await category_repo.get_categories()
    
    assert len(result) == 2
    assert result[0]["name"] == "Print"


@pytest.mark.asyncio
async def test_get_categories_empty(category_repo, mock_graphql_client):
    """Test getting categories when none exist"""
    mock_graphql_client.execute_query.return_value = {
        "categories": []
    }
    
    result = await category_repo.get_categories()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_categories_error(category_repo, mock_graphql_client):
    """Test error handling when getting categories"""
    mock_graphql_client.execute_query.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to get categories"):
        await category_repo.get_categories()


@pytest.mark.asyncio
async def test_create_category_success(category_repo, mock_graphql_client):
    """Test successful category creation"""
    mock_category = {
        "id": "new-cat",
        "name": "New Category",
        "description": "A new category"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createCategory": mock_category
    }
    
    result = await category_repo.create_category("New Category", "A new category")
    
    assert result["name"] == "New Category"


@pytest.mark.asyncio
async def test_create_category_error(category_repo, mock_graphql_client):
    """Test error handling when creating category"""
    mock_graphql_client.execute_mutation.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to create category"):
        await category_repo.create_category("New Category")


# ========================================
# Brand Tools Tests
# ========================================

@pytest.mark.asyncio
async def test_get_brands_success(category_repo, mock_graphql_client):
    """Test successful retrieval of brands"""
    mock_brands = [
        {"id": "brand1", "name": "Acme Corp", "description": "Main brand"},
        {"id": "brand2", "name": "TechCo", "description": "Tech products"}
    ]
    mock_graphql_client.execute_query.return_value = {
        "brands": mock_brands
    }
    
    result = await category_repo.get_brands()
    
    assert len(result) == 2
    assert result[0]["name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_get_brands_empty(category_repo, mock_graphql_client):
    """Test getting brands when none exist"""
    mock_graphql_client.execute_query.return_value = {
        "brands": []
    }
    
    result = await category_repo.get_brands()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_brands_error(category_repo, mock_graphql_client):
    """Test error handling when getting brands"""
    mock_graphql_client.execute_query.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to get brands"):
        await category_repo.get_brands()


@pytest.mark.asyncio
async def test_create_brand_success(category_repo, mock_graphql_client):
    """Test successful brand creation"""
    mock_brand = {"id": "new-brand", "name": "New Brand", "description": "Brand desc"}
    mock_graphql_client.execute_mutation.return_value = {
        "createBrand": mock_brand
    }
    
    result = await category_repo.create_brand("New Brand", "Brand desc")
    
    assert result["name"] == "New Brand"


@pytest.mark.asyncio
async def test_create_brand_error(category_repo, mock_graphql_client):
    """Test error handling when creating brand"""
    mock_graphql_client.execute_mutation.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to create brand"):
        await category_repo.create_brand("New Brand")


# ========================================
# Print Specification Tools Tests
# ========================================

@pytest.mark.asyncio
async def test_get_print_specifications_success(category_repo, mock_graphql_client):
    """Test successful retrieval of print specifications"""
    mock_specs = [
        {"id": "spec1", "name": "A4", "width": 210, "height": 297, "unit": "mm"},
        {"id": "spec2", "name": "Letter", "width": 8.5, "height": 11, "unit": "in"}
    ]
    mock_graphql_client.execute_query.return_value = {
        "printSpecifications": mock_specs
    }
    
    result = await category_repo.get_print_specifications()
    
    assert len(result) == 2
    assert result[0]["name"] == "A4"


@pytest.mark.asyncio
async def test_get_print_specifications_empty(category_repo, mock_graphql_client):
    """Test getting specifications when none exist"""
    mock_graphql_client.execute_query.return_value = {
        "printSpecifications": []
    }
    
    result = await category_repo.get_print_specifications()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_print_specifications_error(category_repo, mock_graphql_client):
    """Test error handling when getting specs"""
    mock_graphql_client.execute_query.side_effect = Exception("API error")
    
    with pytest.raises(CwayAPIError, match="Failed to get print specifications"):
        await category_repo.get_print_specifications()


@pytest.mark.asyncio
async def test_create_print_specification_success(category_repo, mock_graphql_client):
    """Test successful print specification creation with all parameters"""
    mock_spec = {
        "id": "new-spec",
        "name": "Custom Size",
        "width": 150,
        "height": 200,
        "unit": "mm",
        "description": "Custom print size"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createPrintSpecification": mock_spec
    }
    
    result = await category_repo.create_print_specification("Custom Size", 150, 200, unit="mm", description="Custom print size")
    
    assert result["name"] == "Custom Size"
    assert result["width"] == 150


@pytest.mark.asyncio
async def test_create_print_specification_minimal(category_repo, mock_graphql_client):
    """Test specification creation with only required parameters"""
    mock_spec = {"id": "min-spec", "name": "Minimal", "width": 100, "height": 100, "unit": "mm"}
    mock_graphql_client.execute_mutation.return_value = {
        "createPrintSpecification": mock_spec
    }
    
    result = await category_repo.create_print_specification("Minimal", 100, 100)
    
    assert result["unit"] == "mm"  # Default unit


# ========================================
# Share Tools Tests
# ========================================

@pytest.mark.asyncio
async def test_find_shares_success(project_repo, mock_graphql_client):
    """Test successful retrieval of shares"""
    mock_shares = [
        {
            "id": "share1",
            "name": "Project Files",
            "created": "2024-01-01T10:00:00Z"
        },
        {
            "id": "share2",
            "name": "Client Review",
            "created": "2024-01-02T11:00:00Z"
        }
    ]
    mock_graphql_client.execute_query.return_value = {
        "findShares": {"shares": mock_shares, "totalHits": 2}
    }
    
    result = await project_repo.find_shares(limit=50)
    
    assert len(result) == 2
    assert result[0]["name"] == "Project Files"


@pytest.mark.asyncio
async def test_find_shares_empty(project_repo, mock_graphql_client):
    """Test finding shares when none exist"""
    mock_graphql_client.execute_query.return_value = {
        "findShares": {"shares": [], "totalHits": 0}
    }
    
    result = await project_repo.find_shares()
    
    assert result == []


@pytest.mark.asyncio
async def test_get_share_success(project_repo, mock_graphql_client):
    """Test successful retrieval of a specific share"""
    mock_share = {
        "id": "share123",
        "name": "Important Files",
        "description": "Files for review",
        "url": "https://share.cway.se/abc123",
        "expiresAt": "2024-12-31T23:59:59Z",
        "filesCount": 7
    }
    mock_graphql_client.execute_query.return_value = {"share": mock_share}
    
    result = await project_repo.get_share("share123")
    
    assert result["id"] == "share123"
    assert result["name"] == "Important Files"


@pytest.mark.asyncio
async def test_get_share_not_found(project_repo, mock_graphql_client):
    """Test getting a share that doesn't exist"""
    mock_graphql_client.execute_query.return_value = {"share": None}
    
    result = await project_repo.get_share("nonexistent")
    
    assert result is None


@pytest.mark.asyncio
async def test_get_share_error_handling(project_repo, mock_graphql_client):
    """Test error handling when GraphQL query fails"""
    mock_graphql_client.execute_query.side_effect = Exception("Network error")
    
    with pytest.raises(CwayAPIError, match="Failed to get share"):
        await project_repo.get_share("share123")


@pytest.mark.asyncio
async def test_create_share_minimal(project_repo, mock_graphql_client):
    """Test creating share with minimal required parameters"""
    mock_share = {
        "id": "new-share",
        "name": "Quick Share"
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createShare": mock_share
    }
    
    result = await project_repo.create_share("Quick Share", ["file1", "file2"])
    
    assert result["name"] == "Quick Share"


@pytest.mark.asyncio
async def test_create_share_full_options(project_repo, mock_graphql_client):
    """Test creating share with all optional parameters"""
    mock_share = {
        "id": "secure-share",
        "name": "Secure Files",
        "description": "Protected share",
        "expiresAt": "2024-12-31T23:59:59Z",
        "maxDownloads": 10
    }
    mock_graphql_client.execute_mutation.return_value = {
        "createShare": mock_share
    }
    
    result = await project_repo.create_share(
        "Secure Files",
        ["f1", "f2", "f3", "f4", "f5"],
        description="Protected share",
        expires_at="2024-12-31T23:59:59Z",
        max_downloads=10,
        password="secret123"
    )
    
    assert result["name"] == "Secure Files"
    assert result["maxDownloads"] == 10


@pytest.mark.asyncio
async def test_create_share_single_file(project_repo, mock_graphql_client):
    """Test creating share with single file"""
    mock_share = {"id": "single-share", "name": "One File"}
    mock_graphql_client.execute_mutation.return_value = {
        "createShare": mock_share
    }
    
    result = await project_repo.create_share("One File", ["file1"]) 
    
    assert result["name"] == "One File"


@pytest.mark.asyncio
async def test_delete_share_success(project_repo, mock_graphql_client):
    """Test successful share deletion"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteShare": True
    }
    
    result = await project_repo.delete_share("share123")
    
    assert result is True


@pytest.mark.asyncio
async def test_delete_share_failure(project_repo, mock_graphql_client):
    """Test failed share deletion"""
    mock_graphql_client.execute_mutation.return_value = {
        "deleteShare": False
    }
    
    result = await project_repo.delete_share("share123")
    
    assert result is False


@pytest.mark.asyncio
async def test_delete_share_error_handling(project_repo, mock_graphql_client):
    """Test error handling during share deletion"""
    mock_graphql_client.execute_mutation.side_effect = Exception("GraphQL error")
    
    with pytest.raises(CwayAPIError, match="Failed to delete share"):
        await project_repo.delete_share("share123")
