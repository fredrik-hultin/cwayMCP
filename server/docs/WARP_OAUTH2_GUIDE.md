# Using OAuth2 with Warp

This guide shows you how to use OAuth2 authentication when developing with Warp.

## Setup (One Time)

### 1. Register Your Application in Azure AD

```bash
# Go to: https://portal.azure.com
# Azure AD > App registrations > New registration

# Name: Cway MCP Dev
# Redirect URI: Leave empty (we'll use device code flow)
# Copy the Application (client) ID
# Copy the Directory (tenant) ID
```

### 2. Configure Your `.env` File

```bash
# In server/.env, add:
AUTH_METHOD=oauth2
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
USE_DEVICE_CODE_FLOW=true

# Keep your existing Cway config:
CWAY_API_URL=https://app.cway.se/graphql

# You can comment out CWAY_API_TOKEN if using OAuth2:
# CWAY_API_TOKEN=...
```

### 3. Grant API Permissions

```bash
# In your Azure AD app registration:
# 1. Go to "API permissions"
# 2. Add permission to your Cway API
# 3. Select DELEGATED permissions
# 4. Grant admin consent (if required)
```

---

## Usage in Warp

### Login (First Time)

When you first use OAuth2, you need to login:

```bash
cd server
python3 scripts/oauth_login.py
```

**What happens:**
1. Script will display a device code and URL
2. Open the URL in your browser
3. Enter the device code
4. Login with your Microsoft/Azure AD account
5. Token is cached to `~/.cway_mcp/token_cache.json`

**Example output:**
```
🔐 Cway MCP Server - OAuth2 Login

📋 Configuration:
  Tenant ID: abc123...
  Client ID: xyz789...
  Auth Method: oauth2
  Device Code Flow: True

🔄 Acquiring token...

To sign in, use a web browser to open the page https://microsoft.com/devicelogin 
and enter the code AB12-CD34 to authenticate.

✅ Login successful!
Token acquired and cached: eyJ0eXAiOiJKV1QiLCJh...

🎉 You can now use the MCP server without re-authenticating
```

### Running the MCP Server

After login, just start the server normally:

```bash
# MCP mode (stdio)
python3 main.py --mode mcp

# REST API mode
python3 main.py --mode rest

# With dashboard
python3 main.py --mode dashboard
```

The server will automatically:
- Load cached token
- Refresh it if needed (5 min before expiry)
- Re-authenticate only if token is expired

### Logout / Clear Cache

To clear your cached token:

```bash
python3 scripts/oauth_logout.py
```

---

## Common Scenarios

### Scenario 1: Quick Development (Device Code Flow)

**Best for:** Local development, testing

```bash
# .env
AUTH_METHOD=oauth2
AZURE_TENANT_ID=your-tenant
AZURE_CLIENT_ID=your-client
USE_DEVICE_CODE_FLOW=true
```

**Usage:**
```bash
# First time
python3 scripts/oauth_login.py

# Then run server
python3 main.py --mode mcp
```

### Scenario 2: Automated/CI (Client Secret)

**Best for:** Deployed servers, CI/CD

```bash
# .env
AUTH_METHOD=oauth2
AZURE_TENANT_ID=your-tenant
AZURE_CLIENT_ID=your-client
AZURE_CLIENT_SECRET=your-secret
```

**Usage:**
```bash
# No login needed, just run
python3 main.py --mode rest
```

### Scenario 3: Keep Using Static Token

**Best for:** If OAuth2 setup is not ready

```bash
# .env
AUTH_METHOD=static
CWAY_API_TOKEN=your-token
```

**Usage:**
```bash
# Works exactly as before
python3 main.py --mode mcp
```

---

## Troubleshooting

### Problem: "AADSTS65001: consent required"

**Solution:**
1. Go to Azure AD > App registrations > Your app
2. API permissions > Grant admin consent
3. Try login again

### Problem: Device code expired

**Solution:**
```bash
# Codes expire after 15 minutes
# Just run login script again
python3 scripts/oauth_login.py
```

### Problem: Token expired

**Solution:**
```bash
# Clear cache and re-login
python3 scripts/oauth_logout.py
python3 scripts/oauth_login.py
```

### Problem: "No module named 'msal'"

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt
```

---

## Token Lifecycle

```
Day 1:
  Login → Token cached → Server uses token (1 hour)
  
After 55 mins:
  Server auto-refreshes token → New token cached
  
After 7 days (refresh token expires):
  Run: python3 scripts/oauth_login.py
```

---

## Security Notes

✅ **DO:**
- Use device code flow for local dev
- Use client secret for production/CI
- Keep `~/.cway_mcp/token_cache.json` secure (chmod 600)
- Add `.env` to `.gitignore`

❌ **DON'T:**
- Commit client secrets to git
- Share your token cache file
- Use device code flow in production

---

## Warp Tasks

Add these to your Warp workflows:

```yaml
# .warp/tasks.yaml
- name: oauth:login
  command: python3 scripts/oauth_login.py
  description: Login to Azure AD with OAuth2

- name: oauth:logout  
  command: python3 scripts/oauth_logout.py
  description: Clear OAuth2 token cache

- name: oauth:test
  command: |
    python3 -c "
    import asyncio
    from src.infrastructure.auth.token_provider import OAuth2TokenProvider
    from config.settings import settings
    async def test():
        provider = OAuth2TokenProvider(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
            use_device_code_flow=True
        )
        token = await provider.get_token()
        print(f'✅ Token: {token[:20]}...')
    asyncio.run(test())
    "
  description: Test OAuth2 token acquisition
```

---

## Migration Checklist

Moving from static tokens to OAuth2:

- [ ] Register app in Azure AD
- [ ] Update `.env` with OAuth2 config
- [ ] Run `python3 scripts/oauth_login.py`
- [ ] Test MCP server connection
- [ ] Update team documentation
- [ ] Notify team members to login
