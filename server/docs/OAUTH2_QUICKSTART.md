# OAuth2 Quick Start

## TL;DR

**Local development:** Use static tokens (current setup)  
**Online deployment:** Use OAuth2 Client Credentials or On-Behalf-Of flow

---

## Quick Setup for Online Deployment

### 1. Choose Your Flow

```bash
# Option A: Server accesses API with its own identity
AUTH_METHOD=oauth2

# Option B: Server accesses API on behalf of users  
AUTH_METHOD=oauth2_obo
```

### 2. Azure AD Setup (5 minutes)

1. **Register app** in Azure AD
2. **Create secret** (Certificates & secrets)
3. **Add permissions** to Cway API
4. **Grant admin consent**

### 3. Configure Environment

```bash
# .env file
AUTH_METHOD=oauth2
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-app-id>
AZURE_CLIENT_SECRET=<your-secret>
OAUTH2_SCOPE=api://cway-api/.default
CWAY_API_URL=https://app.cway.se/graphql
```

### 4. Install & Deploy

```bash
pip install -r requirements.txt
python main.py --mode rest
```

---

## How It Works

### Client Credentials (Simple)
```
Your Server → Azure AD → Get Token → Cway API
```

### On-Behalf-Of (User Context)
```
User → Azure AD → Token → Your Server
Your Server → Azure AD → Exchange Token → Cway API Token
Your Server → Cway API (as user)
```

---

## Architecture Files

New files created:
- `src/infrastructure/auth/token_provider.py` - Token providers
- `src/infrastructure/auth/token_cache.py` - Token caching
- `src/infrastructure/auth/oauth2_flows.py` - OBO & client credentials
- `src/infrastructure/auth/middleware.py` - Request middleware
- `docs/OAUTH2_DEPLOYMENT.md` - Full guide
- `.env.oauth2.example` - Example config

---

## Key Benefits

✅ **Automatic token refresh** - No manual token management  
✅ **Token caching** - Reduced Azure AD calls  
✅ **Secure storage** - Tokens stored in `~/.cway_mcp/token_cache.json`  
✅ **Backward compatible** - Static tokens still work  
✅ **Multi-tenant ready** - Supports per-user tokens with OBO

---

## Migration Path

```bash
# Phase 1: Development (now)
AUTH_METHOD=static

# Phase 2: Test OAuth2
AUTH_METHOD=oauth2  # Test in staging

# Phase 3: Production
AUTH_METHOD=oauth2_obo  # Full user delegation
```

---

## Troubleshooting

**Problem:** "CWAY_API_TOKEN is required"  
**Solution:** Set `AUTH_METHOD=oauth2` and provide Azure credentials

**Problem:** "AADSTS65001: consent required"  
**Solution:** Grant admin consent in Azure AD

**Problem:** Token expires too quickly  
**Solution:** Tokens auto-refresh 5 minutes before expiry

---

## Need Help?

📚 [Full Deployment Guide](./OAUTH2_DEPLOYMENT.md)  
📚 [Microsoft OAuth2 Docs](https://docs.microsoft.com/azure/active-directory/develop/)  
📚 [MSAL Python Docs](https://msal-python.readthedocs.io/)
