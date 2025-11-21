# Cway Authentication CLI Scripts

Interactive command-line tools for managing per-user authentication with Entra ID.

## Prerequisites

- Python 3.11+
- Configured `.env` file with Azure AD settings:
  ```bash
  AUTH_METHOD=oauth2
  AZURE_TENANT_ID=your-tenant-id
  AZURE_CLIENT_ID=your-client-id
  CWAY_API_URL=https://app.cway.se/graphql
  ```

## Available Scripts

### 1. `cway_login.py` - User Login

Interactive script to authenticate with Entra ID and obtain Cway tokens.

**Usage:**
```bash
cd server
python scripts/cway_login.py
```

**Flow:**
1. Enter your email address
2. Script opens browser for Entra ID authentication
3. After auth, copy the full redirect URL from browser
4. Paste URL into terminal
5. Script exchanges authorization code for Cway JWT tokens
6. Tokens are encrypted and stored in `~/.cway_mcp/tokens/`

**Example:**
```
============================================================
  Cway MCP Server - User Authentication
============================================================

Enter your email address:
> user@example.com

ℹ️  Initiating login for user@example.com...

------------------------------------------------------------
📋 Authorization URL:
https://login.microsoftonline.com/...
------------------------------------------------------------

Opening browser for authentication...
✅ Browser opened!

After authenticating in your browser:
1. You will be redirected to a URL
2. Copy the FULL redirect URL from your browser
3. Paste it below

Enter the redirect URL (or press Ctrl+C to cancel):
> http://localhost:8080/callback?code=...&state=...

ℹ️  Exchanging authorization code for tokens...

✅ User user@example.com successfully authenticated! Token expires in 60 minutes.

------------------------------------------------------------
👤 User: user@example.com
🔐 Status: Authenticated
⏰ Token expires in: 60 minutes
------------------------------------------------------------

You can now use the Cway MCP Server with your credentials.
Set CWAY_USERNAME=user@example.com in your environment to use this account.
```

### 2. `cway_logout.py` - User Logout

Interactive script to remove stored tokens (logout).

**Usage:**
```bash
cd server
python scripts/cway_logout.py
```

**Flow:**
1. Lists all authenticated users
2. Choose specific user or "all" to logout everyone
3. Confirmation prompt for bulk logout
4. Removes encrypted token files

**Example:**
```
============================================================
  Cway MCP Server - Logout
============================================================

Found 2 authenticated user(s):

  1. user1@example.com
  2. user2@example.com

Options:
  • Enter a number to logout specific user
  • Enter 'all' to logout all users
  • Press Ctrl+C to cancel

> 1

ℹ️  Logging out user1@example.com...

✅ user1@example.com logged out successfully

============================================================
  ✅ Successfully logged out 1 user(s)
============================================================
```

### 3. `cway_whoami.py` - Check Auth Status

Check authentication status for current or all users.

**Usage:**
```bash
cd server
python scripts/cway_whoami.py
```

**With CWAY_USERNAME set:**
```bash
export CWAY_USERNAME=user@example.com
python scripts/cway_whoami.py
```

**Output (specific user):**
```
============================================================
  Cway MCP Server - Authentication Status
============================================================

Checking authentication status for: user@example.com

------------------------------------------------------------
👤 User: user@example.com
🔐 Status: ✅ Authenticated
⏰ Token expires in: 45 minutes
📅 Expires at: 2025-11-21T10:30:00
------------------------------------------------------------
```

**Output (all users):**
```
============================================================
  Cway MCP Server - Authentication Status
============================================================

No CWAY_USERNAME environment variable set.
Showing all authenticated users...

Found 2 authenticated user(s):

  1. ✅ user1@example.com (expires in 45m)
  2. ✅ user2@example.com (expires in 58m)

------------------------------------------------------------
To use a specific user, set CWAY_USERNAME environment variable:
  export CWAY_USERNAME=user1@example.com
------------------------------------------------------------
```

## Environment Variables

### `CWAY_USERNAME`

Specifies which user account to use for MCP server operations.

```bash
# Set for current session
export CWAY_USERNAME=user@example.com

# Or add to your shell profile (~/.zshrc, ~/.bashrc)
echo 'export CWAY_USERNAME=user@example.com' >> ~/.zshrc
```

## Token Storage

Tokens are stored encrypted in:
```
~/.cway_mcp/tokens/{username_hash}.json
```

- **Encryption:** Fernet (symmetric encryption)
- **Permissions:** `600` (owner read/write only)
- **Contents:** Access token, refresh token, expiry timestamp
- **Lifetime:** 
  - Access token: 1 hour
  - Refresh token: 40 hours

## Security Notes

1. **Encryption Key:** Stored in `~/.cway_mcp/.token_key` (chmod 600)
2. **Token Files:** Restricted to owner access only
3. **State Parameter:** Validated during OAuth2 flow to prevent CSRF
4. **PKCE:** Used in authorization code flow for added security

## Troubleshooting

### "Authentication method is 'static', but oauth2 is required"
**Solution:** Update your `.env` file:
```bash
AUTH_METHOD=oauth2
```

### "Azure AD configuration is missing"
**Solution:** Ensure `.env` has:
```bash
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
```

### "No authorization code found in redirect URL"
**Problem:** Invalid or incomplete redirect URL
**Solution:** Copy the ENTIRE URL from browser address bar, including `http://localhost:8080/callback?code=...&state=...`

### "State parameter mismatch"
**Problem:** Security validation failed
**Solution:** Restart login process - don't reuse old authorization URLs

### Browser doesn't open automatically
**Solution:** Copy the authorization URL from terminal and paste into your browser manually

## Integration with MCP Server

Once authenticated, the MCP server automatically:
1. Detects `CWAY_USERNAME` environment variable
2. Loads encrypted tokens for that user
3. Refreshes tokens automatically when < 5 minutes remaining
4. Creates per-request GraphQL clients with user-specific tokens

No manual token management needed!

## See Also

- [PER_USER_AUTH.md](../../docs/PER_USER_AUTH.md) - Architecture overview
- [AZURE_AD_SETUP.md](../../docs/AZURE_AD_SETUP.md) - Azure AD configuration
- [.env.example](../.env.example) - Environment variable examples
