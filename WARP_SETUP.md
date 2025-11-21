# Warp MCP Server Setup Guide - Per-User Authentication

This guide shows how to configure the Cway MCP Server in Warp with per-user SSO authentication.

## Prerequisites

1. **Azure AD app configured** (see `docs/AZURE_AD_SETUP.md`)
2. **Server environment configured** (`server/.env` with AUTH_METHOD=oauth2)
3. **Virtual environment activated**

## Step-by-Step Setup

### 1. Configure Server Environment

First, ensure your `server/.env` has OAuth2 enabled:

```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/server

# Edit .env file
cat >> .env << 'EOF'

# Per-User Authentication
AUTH_METHOD=oauth2
AZURE_TENANT_ID=your-tenant-id-from-azure
AZURE_CLIENT_ID=your-client-id-from-azure
CWAY_API_URL=https://app.cway.se/graphql
EOF
```

### 2. Authenticate Your User

Run the interactive login script:

```bash
cd /Users/fredrik.hultin/Developer/cwayMCP
python server/scripts/cway_login.py
```

This will:
- Open your browser for Entra ID authentication
- Exchange the authorization code for Cway tokens
- Store encrypted tokens in `~/.cway_mcp/tokens/`

Verify authentication:

```bash
python server/scripts/cway_whoami.py
# Should show:
# ✅ Authenticated as: fredrik.hultin@example.com
# 📅 Token expires: [timestamp]
# ⏰ Time remaining: ~40h
```

### 3. Update Warp Configuration

Edit your Warp MCP config file:

```bash
# Open the config file
code /Users/fredrik.hultin/Developer/cwayMCP/warp-mcp-config.json
```

**Replace your email address** in the `CWAY_USERNAME` field:

```json
{
  "mcpServers": {
    "cway": {
      "name": "Cway MCP Server",
      "description": "MCP server for Cway GraphQL API integration",
      "command": "/Users/fredrik.hultin/Developer/cwayMCP/venv/bin/python",
      "args": [
        "/Users/fredrik.hultin/Developer/cwayMCP/server/main.py",
        "--mode",
        "mcp"
      ],
      "env": {
        "PYTHONPATH": "/Users/fredrik.hultin/Developer/cwayMCP/server/src",
        "CWAY_USERNAME": "your.actual@email.com",  ← CHANGE THIS
        "CWAY_API_URL": "https://app.cway.se/graphql"
      }
    }
  }
}
```

**⚠️ Important:** Use the same email you authenticated with in Step 2.

### 4. Test the Configuration

Test that the server starts correctly:

```bash
cd /Users/fredrik.hultin/Developer/cwayMCP
source venv/bin/activate
CWAY_USERNAME=your@email.com python server/main.py --mode mcp
```

You should see:
```
INFO - Cway MCP Server starting...
INFO - Authentication method: oauth2
INFO - Current user: your@email.com
INFO - Token valid until: [timestamp]
INFO - MCP Server initialized successfully
```

Press `Ctrl+C` to stop the test.

### 5. Restart Warp

For Warp to pick up the new configuration:

1. Quit Warp completely (`Cmd+Q`)
2. Reopen Warp
3. The MCP server will automatically start with your user context

### 6. Verify in Warp

In Warp's Agent Mode (AI chat), try:

```
List all Cway projects
```

The MCP server will automatically use your authenticated tokens!

## How It Works

```
┌─────────────┐
│    Warp     │
│ (MCP Client)│
└──────┬──────┘
       │ CWAY_USERNAME=your@email.com
       ▼
┌─────────────────────────────────┐
│    Cway MCP Server              │
│  • Loads your tokens            │
│  • Auto-refreshes when needed   │
│  • Uses tokens for API calls    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  ~/.cway_mcp/tokens/            │
│    your_email_hash.json         │
│    (encrypted with Fernet)      │
└─────────────────────────────────┘
```

## Token Lifecycle

- **Access token:** Valid for 1 hour
- **Refresh token:** Valid for 40 hours
- **Auto-refresh:** Happens automatically when < 5 minutes remaining
- **Re-authentication:** Required after 40 hours

## Troubleshooting

### "User not authenticated" error

**Solution:** Run the login script:
```bash
python server/scripts/cway_login.py
```

### "CWAY_USERNAME not set" error

**Solution:** Update `CWAY_USERNAME` in `warp-mcp-config.json` to match your email.

### "Token expired" after 40+ hours

**Solution:** Re-authenticate:
```bash
python server/scripts/cway_login.py
# Then restart Warp
```

### Server not starting in Warp

**Check logs:**
```bash
# Test manually:
cd /Users/fredrik.hultin/Developer/cwayMCP
source venv/bin/activate
CWAY_USERNAME=your@email.com python server/main.py --mode mcp
```

## Quick Reference Commands

```bash
# Login (authenticate)
python server/scripts/cway_login.py

# Check authentication status
python server/scripts/cway_whoami.py

# Logout (clear tokens)
python server/scripts/cway_logout.py

# Test server manually
CWAY_USERNAME=your@email.com python server/main.py --mode mcp

# View Warp config
cat /Users/fredrik.hultin/Developer/cwayMCP/warp-mcp-config.json
```

## Configuration Summary

**What changed from static token:**

| Old (Static Token) | New (Per-User OAuth2) |
|-------------------|----------------------|
| `CWAY_API_TOKEN=abc123...` | `CWAY_USERNAME=your@email.com` |
| Token in config file (insecure) | Token encrypted in `~/.cway_mcp/tokens/` |
| Manual token refresh | Automatic token refresh |
| Single shared token | Per-user personalized access |

---

**You're all set!** 🎉

Your MCP server now uses your personal Cway account with automatic token refresh for 40-hour sessions.
