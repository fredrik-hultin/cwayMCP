# Azure AD / Entra ID Setup Guide

Step-by-step guide to configure Azure AD application for Cway MCP Server per-user authentication.

## Prerequisites

- Azure AD tenant (organization account)
- Admin or Application Developer permissions
- Access to [Azure Portal](https://portal.azure.com)

## Overview

The Cway MCP Server uses OAuth2 Authorization Code flow with PKCE to authenticate users via Entra ID (Azure AD). The authentication flow exchanges an Entra ID authorization code for Cway-specific JWT tokens.

## Step 1: Register Application

### 1.1 Navigate to App Registrations

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Azure Active Directory" or "Microsoft Entra ID"
3. Click **App registrations** in the left menu
4. Click **+ New registration**

### 1.2 Configure Basic Settings

**Name:** `Cway MCP Server`

**Supported account types:** Choose based on your needs:
- **Single tenant** (Recommended): Only users in your organization
- **Multi-tenant**: Users from any Azure AD organization
- **Personal Microsoft accounts**: Include personal Microsoft accounts

**Redirect URI:**
- Platform: **Public client/native (mobile & desktop)**
- URI: `http://localhost:8080/callback`

Click **Register**

## Step 2: Note Application IDs

After registration, you'll see the application overview page.

### Copy These Values

1. **Application (client) ID**
   - Format: `12345678-1234-1234-1234-123456789abc`
   - This is your `AZURE_CLIENT_ID`

2. **Directory (tenant) ID**
   - Format: `abcdef12-3456-7890-abcd-ef1234567890`
   - This is your `AZURE_TENANT_ID`

Save these values - you'll need them for your `.env` file.

## Step 3: Configure Authentication

### 3.1 Navigate to Authentication

1. Click **Authentication** in the left menu
2. Verify the redirect URI is configured:
   - `http://localhost:8080/callback` (Public client)

### 3.2 Advanced Settings

**Allow public client flows:** YES

This enables PKCE (Proof Key for Code Exchange) flow, which is more secure than client secrets for public applications.

**Supported account types:** Verify matches your choice from Step 1

Click **Save**

## Step 4: Configure API Permissions

### 4.1 Add Microsoft Graph Permissions

1. Click **API permissions** in the left menu
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Add these permissions:
   - `User.Read` - Read user profile
   - `openid` - OpenID Connect sign-in
   - `profile` - View user's basic profile
   - `email` - View user's email address

### 4.2 Grant Admin Consent (Optional)

If your organization requires admin consent:

1. Click **Grant admin consent for [Your Organization]**
2. Click **Yes** to confirm

This allows users to authenticate without individual consent prompts.

## Step 5: Optional - Branding

### 5.1 Configure Application Branding

1. Click **Branding & properties** in the left menu
2. Configure:
   - **Name**: Cway MCP Server
   - **Logo**: Upload your logo (optional)
   - **Home page URL**: `https://github.com/yourusername/cwayMCP` (optional)
   - **Terms of service URL**: Your terms URL (optional)
   - **Privacy statement URL**: Your privacy URL (optional)

Users will see this branding during the login flow.

## Step 6: Configure Cway MCP Server

### 6.1 Update `.env` File

Create or update `server/.env`:

```bash
# Authentication Mode
AUTH_METHOD=oauth2

# Azure AD Configuration
AZURE_TENANT_ID=your-directory-tenant-id-here
AZURE_CLIENT_ID=your-application-client-id-here

# Cway API
CWAY_API_URL=https://app.cway.se/graphql
```

### 6.2 Verify Configuration

```bash
cd server
python scripts/cway_login.py
```

If configured correctly, the script will open your browser for authentication.

## Architecture Flow

```
┌──────────┐    1. Authorization Request      ┌─────────────┐
│   User   │───────────────────────────────►  │  Entra ID   │
│          │                                   │  (Azure AD) │
└──────────┘                                   └─────────────┘
     │                                               │
     │  2. User authenticates & grants consent       │
     │                                               │
     └───────────────────────────────────────────────┘
                          │
                          │ 3. Authorization Code
                          ▼
┌──────────────────────────────────────────────────┐
│            Cway MCP Server                       │
│  • Receives code + state                        │
│  • Validates state (CSRF protection)            │
└──────────────────────────────────────────────────┘
                          │
                          │ 4. Exchange Code for Cway Tokens
                          ▼
┌──────────────────────────────────────────────────┐
│            Cway Backend                          │
│  • POST /oauth/token                            │
│  • Validates code with Microsoft Graph          │
│  • Issues Cway JWT tokens                       │
│  • Returns: access_token + refresh_token        │
└──────────────────────────────────────────────────┘
```

## Security Considerations

### PKCE Flow

The application uses **PKCE** (Proof Key for Code Exchange) instead of client secrets:

- **Code Verifier:** 128-byte random string
- **Code Challenge:** BASE64URL(SHA256(verifier))
- Prevents authorization code interception attacks

### State Parameter

- Random 32-byte string generated per login
- Validated on redirect to prevent CSRF attacks
- Mismatch = authentication rejected

### Token Storage

- Tokens encrypted with Fernet (symmetric encryption)
- Stored in `~/.cway_mcp/tokens/` with chmod 600
- Each user has separate encrypted token file

## Multi-Tenant Considerations

If you configured **multi-tenant** application:

### Supported Scenarios

- Users from any Azure AD organization can authenticate
- Useful for partners/contractors with different Azure AD tenants

### Configuration

Update redirect URI to support multiple origins:
```
http://localhost:8080/callback
https://your-server.com/callback
```

### Tenant Verification

The Cway backend validates the user's tenant against allowed tenants. Contact Cway support to whitelist additional tenants.

## Troubleshooting

### "AADSTS50011: The redirect URI specified in the request does not match"

**Problem:** Redirect URI mismatch

**Solution:**
1. Go to Azure Portal → App registrations → Your app
2. Click Authentication
3. Verify redirect URI exactly matches: `http://localhost:8080/callback`
4. Ensure it's configured as **Public client** not **Web**

### "AADSTS65001: The user or administrator has not consented"

**Problem:** Missing permissions or consent

**Solution:**
1. Go to API permissions
2. Verify required permissions are added
3. Click "Grant admin consent"

### "AADSTS700016: Application not found in the directory"

**Problem:** Wrong tenant ID or application not registered

**Solution:**
1. Verify `AZURE_TENANT_ID` in `.env` matches Directory (tenant) ID
2. Verify `AZURE_CLIENT_ID` matches Application (client) ID
3. Check application hasn't been deleted

### "Invalid client secret provided"

**Problem:** Using client secret flow instead of public client

**Solution:**
1. Go to Authentication settings
2. Set "Allow public client flows" to **YES**
3. Remove any client secrets (not needed for PKCE)

### Browser doesn't redirect

**Problem:** Callback server not running or port conflict

**Solution:**
1. Verify `http://localhost:8080` is accessible
2. Check no other service is using port 8080
3. Try different redirect URI (update both Azure and script)

## Testing the Setup

### Quick Test

```bash
# Test authentication
cd server
python scripts/cway_login.py

# Expected flow:
# 1. Script opens browser
# 2. You see Microsoft/Azure login page
# 3. After login, redirected to localhost:8080
# 4. Copy redirect URL back to script
# 5. Success message with token expiry
```

### Verify Token Storage

```bash
# Check tokens are stored
ls -la ~/.cway_mcp/tokens/

# Check authentication status
python scripts/cway_whoami.py
```

## Production Deployment

### Use HTTPS Redirect URI

For production deployments, use HTTPS:

1. **Register HTTPS redirect URI** in Azure:
   ```
   https://your-server.com/callback
   ```

2. **Set up callback server** with SSL certificate

3. **Update scripts** to use HTTPS callback URL

### Environment-Specific Configuration

Development:
```bash
AUTH_METHOD=oauth2
AZURE_TENANT_ID=dev-tenant-id
AZURE_CLIENT_ID=dev-client-id
```

Production:
```bash
AUTH_METHOD=oauth2
AZURE_TENANT_ID=prod-tenant-id
AZURE_CLIENT_ID=prod-client-id
```

## Additional Resources

- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [OAuth 2.0 Authorization Code Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [PKCE Specification (RFC 7636)](https://tools.ietf.org/html/rfc7636)
- [Cway API Documentation](https://app.cway.se/api/docs)

## Support

For Azure AD issues:
- [Microsoft Azure Support](https://azure.microsoft.com/support/)

For Cway integration issues:
- Contact Cway support team
- Check [Cway Server Repository](https://github.com/collabra/cway-server)

## See Also

- [PER_USER_AUTH.md](./PER_USER_AUTH.md) - Architecture overview
- [README_AUTH_SCRIPTS.md](../server/scripts/README_AUTH_SCRIPTS.md) - CLI scripts usage
- [.env.example](../server/.env.example) - Environment variable template
