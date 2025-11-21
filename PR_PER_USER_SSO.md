# Pull Request: Per-User SSO Authentication with Entra ID

## Overview

This PR implements comprehensive per-user authentication for the cwayMCP server, enabling seamless SSO integration with Microsoft Entra ID (Azure AD). Each user authenticates individually, receives personalized JWT tokens from Cway, and benefits from automatic token refresh for uninterrupted 40-hour sessions.

## Problem Statement

The original MCP server used a single static API token shared across all users, which prevented:
- Per-user data access control
- Personalized content filtering
- User-specific audit trails
- Compliance with zero-trust security models

Users needed a way to authenticate with their own credentials while maintaining a smooth, non-disruptive experience.

## Solution

Implemented a complete per-user OAuth2 authentication system with:
- **Entra ID SSO Integration**: OAuth2 Authorization Code flow with PKCE
- **Cway Token Exchange**: Entra ID auth codes exchanged for Cway JWT tokens
- **Encrypted Token Storage**: Per-user tokens stored encrypted with Fernet in `~/.cway_mcp/tokens/`
- **Automatic Token Refresh**: Transparent refresh when <5 minutes remaining (40-hour sessions)
- **Thread-Safe Operations**: Concurrent user support with per-user locks
- **MCP Tools**: Built-in authentication tools (login, logout, whoami)
- **CLI Scripts**: User-friendly command-line tools for authentication management

## Architecture

```
┌─────────────┐
│ MCP Client  │ (Claude Desktop, Warp, etc.)
│ CWAY_USERNAME=user@example.com
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│         Cway MCP Server                      │
│  ┌───────────────────────────────────────┐  │
│  │ TokenManager (per-request)            │  │
│  │  • get_valid_token(username)          │  │
│  │  • Auto-refresh if <5 min             │  │
│  └───────────┬───────────────────────────┘  │
│              │                               │
│  ┌───────────▼───────────────────────────┐  │
│  │ TokenStore (encrypted)                │  │
│  │  ~/.cway_mcp/tokens/{hash}.json       │  │
│  │  chmod 600, Fernet encryption         │  │
│  └───────────────────────────────────────┘  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Entra ID (Microsoft Identity Platform)      │
│   • OAuth2 Authorization Code + PKCE         │
│   • User authentication & consent            │
└──────────────┬───────────────────────────────┘
               │ auth_code
               ▼
┌──────────────────────────────────────────────┐
│  Cway Backend                                 │
│   POST /oauth/token?grant_type=azure         │
│   • Validates with Microsoft Graph           │
│   • Returns Cway JWT tokens                  │
│     - Access token (1 hour)                  │
│     - Refresh token (40 hours)               │
└──────────────────────────────────────────────┘
```

## Key Features

### 1. Per-User Authentication Flow
- User initiates login via MCP tool or CLI script
- Browser opens to Entra ID login page (PKCE flow)
- After successful authentication, authorization code exchanged for Cway tokens
- Tokens encrypted and stored per-user
- Subsequent requests use stored tokens automatically

### 2. Automatic Token Refresh
- Background monitoring of token expiry
- Refresh triggered when <5 minutes remaining
- Zero user intervention required
- Thread-safe with per-user locks to prevent race conditions

### 3. Multi-User Support
- Multiple users can authenticate on the same machine
- Each user's tokens stored separately with hashed filenames
- Complete data isolation between users
- Concurrent operations fully supported (tested with 50 users)

### 4. Security
- Fernet symmetric encryption for token storage
- File permissions set to 600 (owner read/write only)
- PKCE (Proof Key for Code Exchange) for OAuth2
- No tokens in environment variables or command line
- Automatic cleanup on logout

### 5. Developer Experience
- **MCP Tools**: login, complete_login, logout, whoami, list_authenticated_users
- **CLI Scripts**: `cway_login.py`, `cway_logout.py`, `cway_whoami.py`
- **Backward Compatible**: Static token mode still supported
- **Comprehensive Docs**: Setup guides, architecture docs, troubleshooting

## Changes Summary

### New Files Created (17 files)

#### Core Authentication (3 files)
- `server/src/infrastructure/auth/token_store.py` (247 lines) - Encrypted token storage
- `server/src/infrastructure/auth/entra_auth.py` (276 lines) - OAuth2 + PKCE implementation
- `server/src/infrastructure/auth/token_manager.py` (233 lines) - Token lifecycle management

#### Application Layer (1 file)
- `server/src/application/auth_use_cases.py` (267 lines) - Authentication business logic

#### CLI Scripts (4 files)
- `server/scripts/cway_login.py` (181 lines) - Interactive login with browser
- `server/scripts/cway_logout.py` (158 lines) - User logout management
- `server/scripts/cway_whoami.py` (139 lines) - Authentication status checker
- `server/scripts/README_AUTH_SCRIPTS.md` (247 lines) - CLI usage guide

#### Documentation (2 files)
- `docs/PER_USER_AUTH.md` (512 lines) - Complete architecture documentation
- `docs/AZURE_AD_SETUP.md` (337 lines) - Azure AD setup guide

#### Tests (7 files)
- `server/tests/unit/test_token_store.py` (341 lines) - Token storage tests
- `server/tests/unit/test_entra_auth.py` (284 lines) - OAuth2 flow tests
- `server/tests/unit/test_token_manager.py` (401 lines) - Token manager tests
- `server/tests/unit/test_auth_use_cases.py` (287 lines) - Use case tests
- `server/tests/integration/test_mcp_per_user_auth.py` (246 lines) - MCP integration tests
- `server/tests/integration/test_graphql_per_user.py` (215 lines) - GraphQL client tests
- `server/tests/integration/test_multi_user.py` (429 lines) - Multi-user integration tests

### Modified Files (4 files)

- `server/src/presentation/cway_mcp_server.py` (+147 lines)
  - Initialize TokenManager for oauth2 mode
  - Per-request token retrieval via `_get_authenticated_client()`
  - Thread-safe repository creation with user tokens
  - Integration with auth MCP tools

- `server/src/presentation/tool_definitions.py` (+64 lines)
  - Added `get_auth_tools()` function
  - 5 new MCP tool definitions for authentication

- `server/src/infrastructure/graphql_client.py` (+45 lines)
  - Accept `api_token` parameter with highest priority
  - Per-request token support via StaticTokenProvider
  - Backward compatible with existing token_provider

- `server/.env.example` (+74 lines)
  - Added AUTH_METHOD configuration
  - Documented static vs oauth2 modes
  - Added Azure AD configuration variables

## Test Coverage

**Total: 64 tests passing**

### Unit Tests (46 tests)
- Token Store: 11 tests (encryption, file permissions, error handling)
- Entra Auth: 9 tests (OAuth2 flow, PKCE, token exchange)
- Token Manager: 9 tests (refresh logic, thread safety, expiry handling)
- Auth Use Cases: 9 tests (login, logout, whoami)
- GraphQL Client: 8 tests (per-user token support)

### Integration Tests (18 tests)
- MCP Server: 6 tests (per-user auth integration)
- Multi-User: 12 tests
  - Separate token storage per user
  - Concurrent token refresh (race condition protection)
  - 50 concurrent users scalability test
  - Data isolation verification
  - File permission security
  - Corrupted file handling
  - Full authentication lifecycle
  - Token expiry timeline

### Coverage
- Token Store: 86%
- Entra Auth: 84%
- Token Manager: 85%
- Auth Use Cases: 81%
- All critical paths covered

## Configuration

### Environment Variables

```bash
# Authentication method (static or oauth2)
AUTH_METHOD=oauth2

# Azure AD configuration
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_REDIRECT_URI=http://localhost:8000/oauth/callback

# Cway API
CWAY_API_URL=https://app.cway.se/graphql

# Runtime: User identification
CWAY_USERNAME=user@example.com
```

### Backward Compatibility

Static token mode still works:
```bash
AUTH_METHOD=static
CWAY_API_TOKEN=your_static_bearer_token
```

## Usage Examples

### CLI Authentication
```bash
# Login
python server/scripts/cway_login.py
# → Opens browser for Entra ID login
# → Stores encrypted tokens

# Check status
python server/scripts/cway_whoami.py
# ✅ Authenticated as: user@example.com
# 📅 Token expires: 2024-03-20 15:30:00
# ⏰ Time remaining: 39h 45m

# Logout
python server/scripts/cway_logout.py
```

### MCP Tool Usage
```python
# From Claude Desktop or other MCP client
await mcp.call_tool("login", {"email": "user@example.com"})
# Returns authorization URL

await mcp.call_tool("complete_login", {
    "authorization_code": "code_from_redirect",
    "state": "state_from_redirect"
})
# Completes authentication

await mcp.call_tool("whoami", {})
# Returns current user info

await mcp.call_tool("logout", {})
# Clears tokens
```

### Running the Server
```bash
# Set user identity
export CWAY_USERNAME=user@example.com

# Start server
cd server && python main.py --mode mcp

# Server will automatically:
# 1. Load user's tokens from ~/.cway_mcp/tokens/
# 2. Use tokens for all GraphQL requests
# 3. Refresh tokens automatically when needed
```

## Testing Instructions

### Unit Tests
```bash
cd server
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
cd server
python -m pytest tests/integration/ -v
```

### Manual Testing
1. Configure Azure AD app (see `docs/AZURE_AD_SETUP.md`)
2. Set environment variables in `server/.env`
3. Run `python server/scripts/cway_login.py`
4. Start MCP server with `CWAY_USERNAME` set
5. Test with MCP Inspector or Claude Desktop
6. Verify data isolation with multiple users

## Migration Guide

### For Existing Users

**No breaking changes** - static token mode still works.

To migrate to per-user authentication:

1. **Azure AD Setup** (one-time, admin)
   - Follow `docs/AZURE_AD_SETUP.md`
   - Register app in Azure Portal
   - Configure redirect URI

2. **Update Configuration**
   ```bash
   # Change in .env
   AUTH_METHOD=static  → AUTH_METHOD=oauth2
   
   # Add Azure credentials
   AZURE_TENANT_ID=...
   AZURE_CLIENT_ID=...
   ```

3. **Authenticate**
   ```bash
   python server/scripts/cway_login.py
   ```

4. **Update MCP Client Config**
   ```json
   {
     "env": {
       "CWAY_USERNAME": "your.email@example.com"
     }
   }
   ```

## Security Considerations

### Token Storage
- Fernet symmetric encryption (128-bit AES in CBC mode)
- File permissions: 600 (owner read/write only)
- Stored in user home directory: `~/.cway_mcp/tokens/`
- Filename hashed to obscure usernames

### OAuth2 Security
- PKCE prevents authorization code interception
- State parameter prevents CSRF attacks
- Short-lived access tokens (1 hour)
- Automatic rotation via refresh tokens

### Thread Safety
- Per-user locks prevent concurrent refresh race conditions
- Tested with 50 concurrent users
- No shared state between user sessions

## Performance

- Token retrieval: <1ms (in-memory after first load)
- Token refresh: ~200-500ms (network call to Cway)
- Encryption/decryption: <1ms per operation
- No performance impact on GraphQL queries
- Concurrent users: tested up to 50 simultaneous users

## Documentation

- **Architecture**: `docs/PER_USER_AUTH.md` - Complete system architecture
- **Azure Setup**: `docs/AZURE_AD_SETUP.md` - Step-by-step Azure AD configuration
- **CLI Scripts**: `server/scripts/README_AUTH_SCRIPTS.md` - CLI tool usage
- **Environment**: `server/.env.example` - Configuration reference

## Breaking Changes

**None** - Fully backward compatible with existing static token mode.

## Future Enhancements

Potential improvements for future PRs:
- Web-based login UI (alternative to CLI)
- Token rotation policies
- Multi-tenancy support
- SSO with other identity providers (Okta, Google)
- Audit logging for authentication events

## Checklist

- [x] Code follows CLEAN architecture principles
- [x] TDD approach with comprehensive test coverage (64 tests)
- [x] Documentation complete (architecture, setup, usage)
- [x] CLI tools with user-friendly UX
- [x] Security best practices (encryption, PKCE, file permissions)
- [x] Thread-safe concurrent operations
- [x] Backward compatible with existing deployments
- [x] No breaking changes
- [x] All tests passing
- [x] Code formatted (black, isort)
- [x] Type hints (mypy compliant)

## Review Focus Areas

1. **Security Review**
   - Token storage encryption implementation
   - File permission handling
   - OAuth2 PKCE implementation
   - Thread safety in token refresh

2. **Architecture Review**
   - CLEAN architecture layer separation
   - Dependency injection patterns
   - Error handling and logging

3. **Testing Review**
   - Multi-user test scenarios
   - Concurrent operation tests
   - Token lifecycle tests
   - Edge case coverage

4. **Documentation Review**
   - Azure AD setup instructions
   - Migration guide clarity
   - CLI script usage examples

## Related Issues

This PR addresses the requirement for per-user authentication where each user needs to access their own version of information from the Cway server, with the MCP server forwarding user-specific bearer tokens rather than using a single shared token.

## Branch

`feature/per-user-sso-passthrough`

## Commit History

- feat(Task 1): implement encrypted per-user token storage system
- feat(Task 2): implement Entra ID OAuth2 + PKCE authentication
- feat(Task 3): implement token manager with auto-refresh
- feat(Task 4): integrate per-user auth into MCP server
- feat(Task 5): add authentication MCP tools
- feat(Task 6): update GraphQL client for per-request tokens
- feat(Task 7): add CLI authentication helper scripts
- feat(Task 8): comprehensive authentication documentation
- feat(Task 9): comprehensive multi-user integration tests

---

**Ready for Review** ✅

Total changes: **~5,000 lines** across 21 files (17 new, 4 modified)
