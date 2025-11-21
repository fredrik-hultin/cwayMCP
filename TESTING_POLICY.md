# Testing Policy

## Critical Rules

### ❌ NEVER Run Tests Against Live Server

**All tests MUST use mocks or test fixtures. NEVER hit the real Cway production server.**

### Why?

1. **Data integrity** - Tests should not create, modify, or delete production data
2. **Reliability** - Tests must not depend on external services being available
3. **Speed** - Tests should run fast without network latency
4. **Safety** - Prevents accidental data corruption or API rate limiting
5. **CI/CD** - Tests must run in isolated environments without credentials

## Test Structure

### Unit Tests (`tests/unit/`)
- Test individual functions, classes, and modules in isolation
- MUST use mocks for all external dependencies
- MUST NOT require API tokens or network access
- Should run in < 1 second per test

### Integration Tests (`tests/integration/`)
- Test interaction between multiple components
- MUST use mocked GraphQL clients and repositories
- MUST NOT hit real Cway API endpoints
- Should verify component integration logic only

## Mocking Guidelines

### ✅ Correct Approach

```python
@pytest.fixture
def mock_graphql_client():
    """Create a mock GraphQL client."""
    client = AsyncMock()
    client.execute_query = AsyncMock()
    client.execute_mutation = AsyncMock()
    return client

@pytest.fixture
def repository(mock_graphql_client):
    """Create repository with mocked client."""
    return CwayProjectRepository(mock_graphql_client)

@pytest.mark.asyncio
async def test_find_projects(repository, mock_graphql_client):
    # Mock the response
    mock_graphql_client.execute_query.return_value = {
        "plannerProjects": [{"id": "1", "name": "Test"}]
    }
    
    # Test the logic
    result = await repository.find_all_projects()
    assert len(result) == 1
```

### ❌ Wrong Approach

```python
# NEVER DO THIS
@pytest.mark.asyncio
async def test_find_projects():
    # This hits the REAL server!
    client = CwayGraphQLClient()
    repo = CwayProjectRepository(client)
    result = await repo.find_all_projects()
    assert len(result) > 0
```

## Manual Testing

If you need to test against a real server:

1. **Use a dedicated test/dev environment** - Never production
2. **Run manually outside of pytest** - Keep out of automated test suite
3. **Document the test** - Explain what data is being used
4. **Clean up after** - Remove any test data created

Create manual test scripts in `scripts/manual_tests/` (not in `tests/`).

## Code Review Checklist

Before merging code, verify:

- [ ] No tests use real API tokens from `.env`
- [ ] All GraphQL clients are mocked in tests
- [ ] No tests require `CWAY_API_TOKEN` environment variable
- [ ] Tests pass without network connectivity
- [ ] No `CwayGraphQLClient()` instantiation without mocks in tests

## Enforcement

- CI/CD pipeline runs without Cway API credentials
- Any test requiring real credentials will fail in CI
- Code reviews MUST check for proper mocking
- Violating this policy requires immediate fix

---

**Remember: Tests should verify OUR code logic, not that the Cway API works.**
