# CLEAN/SOLID Architecture Analysis & Refactoring Roadmap

## Current State Assessment

### File Size Analysis
| File | Lines | Recommended | Status |
|------|-------|-------------|--------|
| `cway_repositories.py` | 2,671 | 300-500 | ❌ 5.3x too large |
| `tool_definitions.py` | 1,758 | 300-500 | ❌ 3.5x too large |
| `cway_mcp_server.py` | 1,812 | 300-500 | ❌ 3.6x too large |

### SOLID Principle Violations

#### 1. Single Responsibility Principle (SRP) ❌
**Problem**: `CwayProjectRepository` has 100+ methods handling 8 different domains:
- Projects (18 methods)
- Users (12 methods)
- Artworks (25 methods)
- Folders/Files (10 methods)
- Shares (4 methods)
- Categories (6 methods)
- Teams (6 methods)
- Search/Activity (4 methods)

**Impact**: 
- Hard to maintain
- Difficult to test in isolation
- Changes to one domain risk breaking others
- Violates "one reason to change" principle

#### 2. Open/Closed Principle (OCP) ❌
**Problem**: Adding new tools requires modifying existing files:
- New tool → modify `tool_definitions.py` (add to existing functions)
- New handler → modify `cway_mcp_server.py` (add elif branch)
- Not open for extension, requires modification

**Impact**:
- Risk of regression bugs
- Merge conflicts in team environments
- Testing overhead (retest entire file)

#### 3. Liskov Substitution Principle (LSP) ✅
**Status**: GOOD - Using proper interfaces and dependency injection

#### 4. Interface Segregation Principle (ISP) ⚠️
**Problem**: Repository clients must depend on entire 2,671-line class
- Artwork handlers don't need user methods
- User handlers don't need artwork methods

**Impact**:
- Unnecessary dependencies
- Larger memory footprint
- Harder to mock for testing

#### 5. Dependency Inversion Principle (DIP) ✅
**Status**: GOOD - Depends on GraphQL client abstraction

---

## CLEAN Architecture Analysis

### Current Architecture (Layered)
```
Presentation (cway_mcp_server.py)
        ↓
Application (use cases - minimal)
        ↓
Infrastructure (cway_repositories.py)
        ↓
Domain (entities, interfaces)
```

### Issues Identified

#### 1. Layer Coupling ⚠️
- Presentation layer directly instantiates infrastructure
- Missing clear use case layer
- Fat repositories (contain business logic)

#### 2. Repository Responsibilities ❌
**Current**: Repositories contain business logic
```python
# Should be in use case, not repository
async def compare_projects(self, project_ids):
    # Fetches data AND performs comparison logic
    ...
```

**Best Practice**: Repositories should only handle data access
```python
# Repository: Data access only
async def get_projects_by_ids(self, project_ids):
    return await self.fetch_projects(project_ids)

# Use Case: Business logic
class CompareProjectsUseCase:
    def execute(self, project_ids):
        projects = await repo.get_projects_by_ids(project_ids)
        return self._compare(projects)  # Business logic here
```

#### 3. God Objects ❌
- `CwayProjectRepository`: Does everything
- `CwayMCPServer`: Handles all 100 tools
- Violates "small, focused classes" principle

---

## Proposed Refactoring

### Phase 1: Split Repositories (High Priority)

#### Before (2,671 lines)
```
src/infrastructure/cway_repositories.py
    - CwayProjectRepository (100+ methods)
    - CwayCategoryRepository (6 methods)
```

#### After (~300 lines each)
```
src/infrastructure/repositories/
    __init__.py
    base_repository.py          (50 lines)  - Abstract base
    project_repository.py       (400 lines) - Project ops only
    user_repository.py          (250 lines) - User ops only
    artwork_repository.py       (600 lines) - Artwork ops only
    media_repository.py         (500 lines) - Files/folders/shares
    team_repository.py          (300 lines) - Team management
    category_repository.py      (300 lines) - Categories/brands/specs
    search_repository.py        (200 lines) - Search & activity
    analytics_repository.py     (200 lines) - KPIs & analytics
```

**Benefits**:
- ✅ Each file < 600 lines
- ✅ Single responsibility per repository
- ✅ Easy to find methods by domain
- ✅ Independent testing
- ✅ Can be developed/maintained by different team members

### Phase 2: Split Tool Definitions (High Priority)

#### Before (1,758 lines)
```
src/presentation/tool_definitions.py
    - get_project_tools()
    - get_user_tools()
    - get_artwork_tools()
    - ... (11 functions total)
```

#### After (~200 lines each)
```
src/presentation/tools/
    __init__.py                 (50 lines)  - Aggregator
    project_tools.py            (250 lines)
    user_tools.py               (150 lines)
    artwork_tools.py            (300 lines)
    media_tools.py              (200 lines)
    team_tools.py               (150 lines)
    category_tools.py           (150 lines)
    search_tools.py             (100 lines)
    system_tools.py             (150 lines)
    analytics_tools.py          (150 lines)
```

**Benefits**:
- ✅ Each file < 300 lines
- ✅ Clear domain separation
- ✅ Easy to add new tool categories
- ✅ Parallel development possible

### Phase 3: Implement Handler Pattern (High Priority)

#### Before (1,812 lines)
```python
class CwayMCPServer:
    async def call_tool(self, name, arguments):
        if name == "list_projects":
            ...
        elif name == "get_project":
            ...
        # 100 elif branches
```

#### After (~200 lines each)
```
src/presentation/handlers/
    __init__.py                 (50 lines)
    base_handler.py             (100 lines) - Abstract base
    project_handler.py          (250 lines)
    user_handler.py             (200 lines)
    artwork_handler.py          (300 lines)
    media_handler.py            (250 lines)
    team_handler.py             (200 lines)
    category_handler.py         (200 lines)
    search_handler.py           (150 lines)
    system_handler.py           (150 lines)
    
src/presentation/cway_mcp_server.py  (200 lines) - Routing only
```

#### Handler Pattern Implementation
```python
# base_handler.py
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    def __init__(self, repositories):
        self.repos = repositories
    
    @abstractmethod
    def get_handled_tools(self) -> List[str]:
        """Return list of tool names this handler can process"""
        pass
    
    @abstractmethod
    async def handle(self, tool_name: str, arguments: Dict) -> Dict:
        """Handle tool invocation"""
        pass

# project_handler.py
class ProjectHandler(BaseHandler):
    def get_handled_tools(self):
        return ["list_projects", "get_project", "create_project", ...]
    
    async def handle(self, tool_name, arguments):
        if tool_name == "list_projects":
            return await self._list_projects(arguments)
        elif tool_name == "get_project":
            return await self._get_project(arguments)
        ...

# cway_mcp_server.py (simplified)
class CwayMCPServer:
    def __init__(self):
        self.handlers = {
            handler.get_handled_tools()[0]: handler
            for handler in [
                ProjectHandler(repos),
                UserHandler(repos),
                ...
            ]
        }
    
    async def call_tool(self, name, arguments):
        handler = self._get_handler(name)
        return await handler.handle(name, arguments)
```

**Benefits**:
- ✅ Each handler < 300 lines
- ✅ Easy to add new handlers (OCP compliance)
- ✅ Handlers can be tested independently
- ✅ Clear separation of concerns
- ✅ Handlers can be registered dynamically

---

## Migration Strategy

### Step 1: Create Base Structure (No Breaking Changes)
```bash
mkdir -p src/infrastructure/repositories
mkdir -p src/presentation/tools
mkdir -p src/presentation/handlers
```

### Step 2: Split Repositories (Incremental)
1. Create `base_repository.py` with common functionality
2. Extract `project_repository.py` → Run tests → Commit
3. Extract `user_repository.py` → Run tests → Commit
4. Extract `artwork_repository.py` → Run tests → Commit
5. Continue for each domain
6. Update imports in tests
7. Delete old `cway_repositories.py`

### Step 3: Split Tool Definitions (Parallel)
1. Create `tools/__init__.py`
2. Move `get_project_tools()` to `tools/project_tools.py`
3. Update imports, run tests, commit
4. Repeat for each tool category
5. Delete old `tool_definitions.py`

### Step 4: Implement Handlers (Most Complex)
1. Create `BaseHandler` abstract class
2. Implement `ProjectHandler` → Test → Commit
3. Implement remaining handlers one by one
4. Update `CwayMCPServer` to use handler registry
5. Run full test suite
6. Remove old elif branches

### Step 5: Verification
```bash
# All tests must pass
pytest tests/unit/ --ignore=tests/unit/test_infrastructure_repositories.py -q
# Expected: 379 passed

# Verify file sizes
find src/ -name "*.py" -exec wc -l {} + | sort -rn | head -20
# All files should be < 600 lines
```

---

## Additional Improvements

### 1. Extract Use Cases (Medium Priority)
```
src/application/use_cases/
    compare_projects_use_case.py
    analyze_artwork_use_case.py
    generate_project_summary_use_case.py
```

### 2. Add Domain Services (Low Priority)
```
src/domain/services/
    project_comparison_service.py
    artwork_analysis_service.py
```

### 3. Improve Error Handling (Low Priority)
- Create specific exception types per domain
- Add retry logic for transient failures
- Implement circuit breaker pattern

### 4. Add Caching Layer (Low Priority)
- Cache frequently accessed data
- Implement cache invalidation strategies
- Use Redis or in-memory cache

---

## Benefits Summary

### Before Refactoring
- 3 files totaling 6,241 lines
- Violates SRP, OCP, ISP
- Hard to maintain and test
- High risk of merge conflicts
- Difficult to onboard new developers

### After Refactoring  
- ~25 files averaging 250 lines each
- Follows SOLID principles
- Easy to maintain and test
- Low risk of conflicts
- Clear code organization
- Easy to onboard new developers

### Metrics Improvement
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Max file size | 2,671 | ~600 | 4.5x smaller |
| Avg file size | 2,080 | ~250 | 8.3x smaller |
| Files violating SRP | 3 | 0 | 100% compliant |
| Test isolation | Poor | Excellent | ✅ |
| Maintainability | Low | High | ✅ |

---

## Timeline Estimate

| Phase | Effort | Risk |
|-------|--------|------|
| Split Repositories | 8 hours | Low |
| Split Tool Definitions | 4 hours | Low |
| Implement Handlers | 12 hours | Medium |
| Testing & Verification | 4 hours | Low |
| **Total** | **28 hours** | **Low** |

---

## Recommendation

**Priority**: HIGH  
**Complexity**: MEDIUM  
**Risk**: LOW (with proper testing)

This refactoring should be completed before adding more tools. Current technical debt will only grow worse as we add tools 101-120.

**Suggested Approach**: 
1. Complete Phase 1 (Repositories) immediately
2. Complete Phase 2 (Tool Definitions) next session
3. Complete Phase 3 (Handlers) over 2-3 sessions
4. Each phase maintains 100% test passing rate

**Success Criteria**:
- ✅ All 379 tests passing
- ✅ All files < 600 lines
- ✅ Clear separation of concerns
- ✅ Easy to add new tools without modifying existing files
- ✅ Improved code maintainability score
