# OAuth2 Deployment Guide

This guide explains how to deploy the Cway MCP Server online with OAuth2 authentication.

## Architecture Overview

When the MCP server is deployed online, there are two main OAuth2 flows to choose from:

### 1. Client Credentials Flow (Server-to-Server)
**Use when:** The MCP server accesses the Cway API with its own identity
- Server has its own permissions/service account
- No user context needed
- Simplest to set up

### 2. On-Behalf-Of (OBO) Flow (User Delegation)
**Use when:** The MCP server needs to access the Cway API on behalf of users
- User identity is preserved through the chain
- Server acts as a middleman
- Better for user-specific permissions

## Setup Guide

### Prerequisites
1. Azure AD tenant
2. Cway API registered in Azure AD (or supporting OAuth2)
3. MCP Server registered as an Azure AD application

---

## Option 1: Client Credentials Flow

### Azure AD Configuration

#### 1. Register MCP Server Application
```bash
# In Azure Portal:
# 1. Go to Azure AD > App registrations > New registration
# 2. Name: "Cway MCP Server"
# 3. Supported account types: Choose based on your needs
# 4. Redirect URI: Not needed for client credentials
```

#### 2. Create Client Secret
```bash
# In your app registration:
# 1. Go to "Certificates & secrets"
# 2. New client secret
# 3. Description: "MCP Server Production"
# 4. Copy the secret value (shown only once!)
```

#### 3. Grant API Permissions
```bash
# In your app registration:
# 1. Go to "API permissions"
# 2. Add a permission > APIs my organization uses
# 3. Find your Cway API
# 4. Select application permissions (not delegated)
# 5. Grant admin consent
```

### Server Configuration

Create `.env` file:
```bash
# Authentication
AUTH_METHOD=oauth2

# OAuth2 - Client Credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret-value
OAUTH2_SCOPE=api://cway-api/.default

# Cway API
CWAY_API_URL=https://app.cway.se/graphql

# Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### Deploy and Test

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python main.py --mode rest

# Test with curl
curl http://localhost:8000/api/projects
# No Authorization header needed - server uses its own credentials
```

---

## Option 2: On-Behalf-Of (OBO) Flow

### Azure AD Configuration

#### 1. Register MCP Server Application
Same as above, but with additional configuration.

#### 2. Expose an API (Optional)
If clients need to authenticate to your MCP server:
```bash
# In your app registration:
# 1. Go to "Expose an API"
# 2. Add a scope: "api://your-mcp-server-client-id/access_as_user"
# 3. Who can consent: Admins and users
```

#### 3. Grant API Permissions for OBO
```bash
# In your app registration:
# 1. Go to "API permissions"
# 2. Add permission > APIs my organization uses
# 3. Find your Cway API
# 4. Select DELEGATED permissions (not application)
# 5. Grant admin consent
```

#### 4. Configure Cway API to Trust MCP Server
```bash
# In Cway API app registration:
# 1. Go to "Expose an API"
# 2. Add authorized client application
# 3. Client ID: Your MCP server client ID
# 4. Authorized scopes: Select all relevant scopes
```

### Server Configuration

Update `.env` file:
```bash
# Authentication
AUTH_METHOD=oauth2_obo

# OAuth2 - On-Behalf-Of
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-mcp-server-client-id
AZURE_CLIENT_SECRET=your-client-secret
OAUTH2_SCOPE=api://cway-api/.default

# Cway API
CWAY_API_URL=https://app.cway.se/graphql

# Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### Update Settings

Edit `config/settings.py` to add OBO mode:
```python
auth_method: str = Field(
    default="static", 
    description="Authentication method: 'static', 'oauth2', or 'oauth2_obo'"
)
```

### Update REST API

Edit `src/presentation/rest_api.py` to add middleware:
```python
from src.infrastructure.auth.middleware import UserTokenExtractorMiddleware
from src.infrastructure.auth.oauth2_flows import OnBehalfOfTokenProvider

# Initialize OBO provider
obo_provider = OnBehalfOfTokenProvider(
    tenant_id=settings.azure_tenant_id,
    client_id=settings.azure_client_id,
    client_secret=settings.azure_client_secret,
    target_scope=settings.oauth2_scope,
)

# Add middleware
app.add_middleware(UserTokenExtractorMiddleware)

# Update endpoints to use OBO client
@app.get("/api/projects")
async def list_projects():
    from src.infrastructure.auth.middleware import current_user_token
    user_token = current_user_token.get()
    api_token = await obo_provider.get_token_for_user(user_token)
    
    # Use api_token with GraphQL client
    # ... rest of implementation
```

### Client Authentication Flow

Clients must authenticate and pass their token:

```bash
# 1. Client gets token from Azure AD
# (User logs in via web browser, device code, etc.)

# 2. Client calls MCP server with their token
curl -H "Authorization: Bearer USER_TOKEN_HERE" \
  http://your-server.com/api/projects

# 3. MCP server exchanges user token for Cway API token (OBO)
# 4. MCP server calls Cway API with new token
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Azure AD applications registered
- [ ] API permissions granted and consented
- [ ] Client secrets created and secured
- [ ] Environment variables configured
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Security
- [ ] Use HTTPS in production (required for OAuth2)
- [ ] Store secrets in Azure Key Vault or similar
- [ ] Enable token validation in middleware
- [ ] Implement rate limiting
- [ ] Log authentication failures
- [ ] Set up monitoring/alerts

### Testing
- [ ] Test token acquisition
- [ ] Test token refresh
- [ ] Test with expired tokens
- [ ] Test error handling
- [ ] Load test with multiple users (OBO)

---

## Environment-Specific Configuration

### Development
```bash
AUTH_METHOD=static
CWAY_API_TOKEN=dev-token-here
```

### Staging
```bash
AUTH_METHOD=oauth2
AZURE_TENANT_ID=staging-tenant
# ... OAuth2 credentials for staging
```

### Production
```bash
AUTH_METHOD=oauth2_obo
AZURE_TENANT_ID=prod-tenant
# ... OAuth2 credentials from Key Vault
```

---

## Troubleshooting

### Common Issues

#### 1. "AADSTS65001: The user or administrator has not consented"
**Solution:** Grant admin consent in Azure AD for the required permissions.

#### 2. "AADSTS50013: Assertion failed signature validation"
**Solution:** Check that tenant IDs match and client secret is correct.

#### 3. "Invalid token" errors
**Solution:** 
- Ensure scope is correct (e.g., `api://your-api/.default`)
- Verify API permissions are granted
- Check token expiration

#### 4. OBO flow fails with "AADSTS50013"
**Solution:**
- Verify Cway API trusts your MCP server (authorized client)
- Check delegated permissions (not application permissions)
- Ensure user has consented to original permissions

### Debug Logging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

Check logs for:
- Token acquisition attempts
- Token expiration times
- API permission issues
- HTTP errors from Azure AD

---

## Migration from Static Tokens

### Step-by-Step Migration

1. **Set up OAuth2 in parallel**
   ```bash
   # Support both methods temporarily
   AUTH_METHOD=static  # Keep working
   # Add OAuth2 config for testing
   ```

2. **Test OAuth2 authentication**
   ```bash
   # Update a test instance
   AUTH_METHOD=oauth2
   # Verify it works
   ```

3. **Update clients gradually**
   - Deploy OAuth2 endpoints alongside static token endpoints
   - Migrate clients one by one
   - Monitor for issues

4. **Deprecate static tokens**
   - Set deprecation date
   - Notify users
   - Remove static token support

---

## Best Practices

1. **Use Managed Identity** (Azure)
   - If deploying to Azure, use Managed Identity
   - No secrets to manage
   - Automatic token rotation

2. **Token Caching**
   - Always cache tokens (already implemented)
   - Refresh 5 minutes before expiry
   - Implement per-user caching for OBO

3. **Monitoring**
   - Track token acquisition failures
   - Monitor token refresh rates
   - Alert on authentication errors

4. **Security**
   - Never log full tokens
   - Use HTTPS only
   - Implement CORS properly
   - Validate token audience and issuer

---

## Additional Resources

- [Microsoft Identity Platform Docs](https://docs.microsoft.com/azure/active-directory/develop/)
- [On-Behalf-Of Flow](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [OAuth2 Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
