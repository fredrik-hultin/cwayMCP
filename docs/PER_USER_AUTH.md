# Per-User SSO Authentication Architecture

Comprehensive guide to the per-user authentication system with Entra ID (Azure AD) integration.

## Overview

The Cway MCP Server supports per-user authentication via Entra ID SSO, enabling multiple users to authenticate independently while maintaining data isolation and automatic token refresh.

### Key Features

- **Per-User Isolation:** Each user has their own encrypted token storage
- **Automatic Token Refresh:** Tokens refreshed automatically when < 5 minutes remaining
- **40-Hour Sessions:** Refresh tokens valid for 40 hours (access tokens: 1 hour)
- **Zero Manual Token Management:** Fully automated token lifecycle
- **Security:** Fernet encryption, PKCE flow, state validation
- **Multi-User Support:** Multiple users can be authenticated simultaneously

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User / MCP Client                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 1. MCP Tool Calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   CwayMCPServer                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ _execute_tool()                                     │     │
│  │  • Get current username (CWAY_USERNAME)            │     │
│  │  • Call TokenManager.get_valid_token(username)     │     │
│  │  • Create GraphQLClient(api_token=user_jwt)        │     │
│  │  • Execute tool with per-user client               │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 2. Get Valid Token
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    TokenManager                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ get_valid_token(username)                          │     │
│  │  • Check token cache (thread-safe locks)           │     │
│  │  • If expired/missing: get from TokenStore         │     │
│  │  • If < 5 min remaining: refresh via Entra Auth   │     │
│  │  • Return valid access token                       │     │
│  └────────────────────────────────────────────────────┘     │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
           │ 3a. Load Tokens               │ 3b. Refresh Token
           ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│     TokenStore            │    │   EntraIDAuthenticator       │
│  • Encrypted storage      │    │  • POST /oauth/token         │
│  • ~/.cway_mcp/tokens/    │    │  • grant_type=refresh_token  │
│  • Fernet encryption      │    │  • Returns new Cway JWT      │
│  • chmod 600              │    │  • Updates TokenStore        │
└──────────────────────────┘    └──────────────────────────────┘
```

### Authentication Flow

#### Initial Login (via CLI or MCP Tool)

```
1. User → login(username="user@example.com")
   ↓
2. EntraIDAuthenticator.get_authorization_url()
   • Generates PKCE code_verifier + code_challenge
   • Creates state parameter for CSRF protection
   • Returns: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?...
   ↓
3. User opens URL in browser → Authenticates with Entra ID
   ↓
4. Entra ID redirects → http://localhost:8080/callback?code=XXX&state=YYY
   ↓
5. User → complete_login(username, code, state)
   ↓
6. EntraIDAuthenticator.exchange_code_for_cway_tokens()
   • POST https://app.cway.se/oauth/token
   • Body: { grant_type: "azure", token: "code_from_entra" }
   • Cway validates with Microsoft Graph
   • Returns: { access_token, refresh_token, expires_in }
   ↓
7. TokenStore.save_tokens(username, tokens)
   • Encrypts with Fernet
   • Saves to ~/.cway_mcp/tokens/{username_hash}.json
   • chmod 600 for security
   ↓
8. ✅ User authenticated! Valid for 40 hours
```

#### Per-Request Token Retrieval

```
1. MCP Tool Call (e.g., list_projects)
   ↓
2. MCP Server: username = os.environ.get("CWAY_USERNAME")
   ↓
3. TokenManager.get_valid_token(username)
   ├─ Check in-memory cache
   ├─ If expired or missing: load from TokenStore
   ├─ If < 5 min remaining: refresh_cway_token()
   │  └─ POST /oauth/token (grant_type=refresh_token)
   └─ Return valid access_token
   ↓
4. Create GraphQLClient(api_token=access_token)
   ↓
5. Execute query with user-specific client
   ↓
6. ✅ Response with per-user data
```

#### Automatic Token Refresh

```
TokenManager (background check on each request):
  
  expires_at = token_data["expires_at"]
  now = datetime.now()
  time_remaining = expires_at - now
  
  if time_remaining < 5 minutes:
    # Auto-refresh triggered
    new_tokens = await entra_auth.refresh_cway_token(refresh_token)
    token_store.save_tokens(username, new_tokens)
    return new_tokens["access_token"]
  else:
    # Token still valid
    return cached_access_token
```

## Data Flow

### Static Token Mode (Legacy)

```
┌─────────┐
│ .env    │
│ file    │──► CWAY_API_TOKEN=static_jwt_token
└─────────┘
     │
     ▼
┌─────────────────────────┐
│ CwayMCPServer.__init__  │
│ • token_manager = None  │
│ • graphql_client shared │
└─────────────────────────┘
     │
     ▼
All users share same token (no isolation)
```

### OAuth2 Per-User Mode (New)

```
┌─────────┐
│ .env    │
│ file    │──► AUTH_METHOD=oauth2
│         │    AZURE_TENANT_ID=...
│         │    AZURE_CLIENT_ID=...
└─────────┘
     │
     ▼
┌─────────────────────────────────┐
│ CwayMCPServer.__init__          │
│ • token_manager = TokenManager  │
│ • graphql_client = None (!)     │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ _execute_tool()                 │
│ • Per-request:                  │
│   - Get username from env       │
│   - Get valid token for user    │
│   - Create new client instance  │
│   - Execute with user's token   │
└─────────────────────────────────┘
     │
     ▼
Each user gets isolated GraphQL client per request
```

## Security

### Encryption

**Token Storage:**
- Algorithm: Fernet (symmetric encryption)
- Key derivation: PBKDF2-HMAC-SHA256
- Key storage: `~/.cway_mcp/.token_key` (chmod 600)
- Token files: `~/.cway_mcp/tokens/{sha256_username}.json` (chmod 600)

**What's Encrypted:**
```json
{
  "username": "user@example.com",
  "access_token": "eyJ...",  // Cway JWT (1 hour)
  "refresh_token": "eyJ...", // Cway JWT (40 hours)
  "expires_at": "2025-11-21T12:00:00",
  "created_at": "2025-11-21T11:00:00"
}
```

### OAuth2 Security

**PKCE (Proof Key for Code Exchange):**
- Code verifier: 128 bytes random
- Code challenge: BASE64URL(SHA256(verifier))
- Prevents authorization code interception attacks

**State Parameter:**
- Random 32-byte string
- Validated on redirect to prevent CSRF
- Mismatch = rejected authentication

**Token Exchange:**
- Entra ID code → Cway JWT via Cway's `/oauth/token` endpoint
- Cway validates with Microsoft Graph before issuing tokens
- No direct token passthrough (Cway acts as token issuer)

## Configuration

### Environment Variables

```bash
# Authentication Mode
AUTH_METHOD=oauth2  # Required for per-user auth

# Azure AD Configuration (Required for oauth2)
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here

# Cway API
CWAY_API_URL=https://app.cway.se/graphql

# User Selection (Runtime)
CWAY_USERNAME=user@example.com  # Which user's tokens to use
```

### `.env` Example

```bash
# Per-User Authentication (oauth2)
AUTH_METHOD=oauth2
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=abcdef12-3456-7890-abcd-ef1234567890
CWAY_API_URL=https://app.cway.se/graphql

# Static Token Authentication (legacy - not recommended for multi-user)
# AUTH_METHOD=static
# CWAY_API_TOKEN=your_static_jwt_token_here
```

## Usage Patterns

### CLI Authentication

```bash
# 1. Authenticate user
cd server
python scripts/cway_login.py
# Follow prompts, authenticate in browser

# 2. Check authentication status
python scripts/cway_whoami.py

# 3. Set active user for MCP server
export CWAY_USERNAME=user@example.com

# 4. Start MCP server
python main.py --mode mcp
```

### MCP Tools (Programmatic)

```python
# From MCP client (Claude Desktop, Warp, etc.)

# Login flow
result = await mcp_client.call_tool("login", {
    "username": "user@example.com"
})
# Open authorization_url in browser

# Complete login
result = await mcp_client.call_tool("complete_login", {
    "username": "user@example.com",
    "authorization_code": "code_from_redirect",
    "state": "state_from_login"
})

# Check status
result = await mcp_client.call_tool("whoami", {
    "username": "user@example.com"
})

# Use other tools (automatically uses user's tokens)
projects = await mcp_client.call_tool("list_projects", {})
```

### Multi-User Scenarios

**Scenario 1: Multiple users on same machine**

```bash
# User 1 authenticates
export CWAY_USERNAME=alice@example.com
python scripts/cway_login.py

# User 2 authenticates
export CWAY_USERNAME=bob@example.com
python scripts/cway_login.py

# Both have separate token storage:
# ~/.cway_mcp/tokens/alice_hash.json
# ~/.cway_mcp/tokens/bob_hash.json

# Switch between users
export CWAY_USERNAME=alice@example.com  # Use Alice's tokens
export CWAY_USERNAME=bob@example.com    # Use Bob's tokens
```

**Scenario 2: Team shared server**

Each developer sets `CWAY_USERNAME` in their environment:
```bash
# Alice's ~/.zshrc
export CWAY_USERNAME=alice@example.com

# Bob's ~/.bashrc  
export CWAY_USERNAME=bob@example.com
```

MCP server automatically uses correct tokens per user.

## Token Lifecycle

### Timeline

```
T=0:00    User authenticates
          ├─ Access token issued (expires T+1:00)
          └─ Refresh token issued (expires T+40:00)

T=0:55    Token refresh triggered (5 min remaining)
          ├─ New access token issued (expires T+1:55)
          └─ New refresh token issued (expires T+40:55)

T+39:55   Final token refresh (5 min remaining)
          ├─ New access token issued (expires T+40:55)
          └─ New refresh token issued (expires T+80:55)

T+40:00   Original refresh token expired (but new one valid)

T+80:00   User must re-authenticate (all tokens expired)
```

### Token Refresh Logic

```python
def should_refresh(expires_at: datetime) -> bool:
    """Check if token should be refreshed."""
    time_remaining = expires_at - datetime.now()
    return time_remaining < timedelta(minutes=5)

async def get_valid_token(username: str) -> str:
    """Get valid access token (auto-refresh if needed)."""
    tokens = token_store.get_tokens(username)
    
    if not tokens:
        raise TokenManagerError("Not authenticated")
    
    expires_at = datetime.fromisoformat(tokens["expires_at"])
    
    if should_refresh(expires_at):
        # Refresh token
        new_tokens = await entra_auth.refresh_cway_token(
            tokens["refresh_token"]
        )
        token_store.save_tokens(username, new_tokens)
        return new_tokens["access_token"]
    
    return tokens["access_token"]
```

## Thread Safety

The TokenManager uses per-user locks to ensure thread-safe token refresh:

```python
class TokenManager:
    def __init__(self):
        self._user_locks: Dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()
    
    async def get_valid_token(self, username: str) -> str:
        # Get or create user-specific lock
        async with self._lock:
            if username not in self._user_locks:
                self._user_locks[username] = asyncio.Lock()
        
        user_lock = self._user_locks[username]
        
        # Only one refresh per user at a time
        async with user_lock:
            return await self._get_or_refresh_token(username)
```

This prevents:
- Race conditions during concurrent token refresh
- Multiple refresh requests for same user
- Token file corruption from parallel writes

## Troubleshooting

### Common Issues

**"User not authenticated"**
- Solution: Run `python scripts/cway_login.py`

**"CWAY_USERNAME not set"**
- Solution: `export CWAY_USERNAME=your@email.com`

**"Token expired" after 40+ hours**
- Expected: Re-authenticate with `cway_login.py`

**"State parameter mismatch"**
- Security feature: Start fresh login flow

**"Permission denied: ~/.cway_mcp/tokens/"**
- Solution: `chmod 600 ~/.cway_mcp/tokens/*`

### Debug Logging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py --mode mcp
```

Check logs:
```bash
tail -f server/logs/mcp_server.log
```

## Migration Guide

### From Static Token to Per-User Auth

1. **Update `.env`:**
   ```bash
   # Before
   AUTH_METHOD=static
   CWAY_API_TOKEN=your_token
   
   # After
   AUTH_METHOD=oauth2
   AZURE_TENANT_ID=your_tenant
   AZURE_CLIENT_ID=your_client_id
   ```

2. **Authenticate users:**
   ```bash
   python scripts/cway_login.py
   ```

3. **Set username:**
   ```bash
   export CWAY_USERNAME=your@email.com
   ```

4. **Restart MCP server** (picks up new auth_method)

### Backward Compatibility

Static token mode still works:
```bash
AUTH_METHOD=static
CWAY_API_TOKEN=your_legacy_token
```

Server automatically uses static mode when `AUTH_METHOD != oauth2`.

## Performance

### Token Caching

- In-memory cache per user
- No disk I/O on every request (only when refreshing)
- Thread-safe concurrent access

### Token Refresh Overhead

- Only triggered when < 5 min remaining
- ~100-200ms HTTP request to Cway
- Transparent to MCP client (automatic)

### Memory Usage

- ~1KB per authenticated user (in-memory cache)
- Minimal impact even with 100+ users

## See Also

- [AZURE_AD_SETUP.md](./AZURE_AD_SETUP.md) - Azure AD app registration guide
- [README_AUTH_SCRIPTS.md](../server/scripts/README_AUTH_SCRIPTS.md) - CLI scripts usage
- [.env.example](../server/.env.example) - Environment variable examples
