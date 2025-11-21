# Multi-User Authentication Setup

This guide explains how to set up the Cway MCP Server for multiple users with ChatGPT's MCP connector.

## Overview

The server now supports **per-request authentication** where each user sends their own Cway API token with every request. Users can also register tokens for multiple organizations and query across them.

## Architecture

1. **User creates API token** in Cway UI (https://app.cway.se/settings/api)
2. **User configures ChatGPT** MCP connector with:
   - Server URL: `http://your-server:8000/sse`
   - Authentication: Bearer token (their Cway API token)
3. **ChatGPT sends requests** with `Authorization: Bearer <user_token>` header
4. **Server extracts token** and validates with Cway API
5. **Per-request GraphQL client** created with user's token
6. **Complete data isolation** - each user sees only their data

## Setup Instructions

### 1. Generate Encryption Key

Generate a Fernet encryption key for storing user tokens:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Configure Environment

Create `server/.env` from `server/.env.example`:

```bash
# For multi-user mode, this is optional (used as fallback for local dev)
CWAY_API_TOKEN=your_dev_token_here

# Required for token encryption
TOKEN_ENCRYPTION_KEY=<key_from_step_1>

# Optional: custom database path
TOKEN_DB_PATH=data/tokens.db
```

### 3. Start MCP Server with SSE Transport

```bash
cd server
python start_mcp_sse.py
```

The server will start on `http://localhost:8000` with endpoints:
- `/sse` - SSE connection for MCP protocol
- `/messages` - POST endpoint for MCP messages

### 4. User Configures ChatGPT

Each user configures their ChatGPT MCP connector:

```json
{
  "name": "Cway MCP",
  "url": "http://your-server:8000/sse",
  "auth": {
    "type": "bearer",
    "token": "<their_cway_api_token>"
  }
}
```

## Multi-Organization Support

Users who belong to multiple Cway organizations can register additional tokens:

### Register Additional Organization

```
User: @cway register_org_token("CustomerCo", "token_for_customer_co")
```

The server will:
1. Validate the token with Cway API
2. Encrypt and store it in the database
3. Associate it with the user's identity

### List Registered Organizations

```
User: @cway list_my_organizations()
```

Returns:
```json
{
  "organizations": [
    {
      "name": "Collabra",
      "org_id": "uuid-1234",
      "primary": true
    },
    {
      "name": "CustomerCo",
      "org_id": null,
      "primary": false
    }
  ],
  "count": 2
}
```

### Query Multiple Organizations

```
User: @cway list_projects(orgs=["Collabra", "CustomerCo"])
```

Returns projects from both organizations with an `organization` field identifying the source.

### Remove Organization Token

```
User: @cway remove_org_token("CustomerCo")
```

## Security

- **Token Encryption**: All stored tokens are encrypted using Fernet (AES-128)
- **User Isolation**: Each request creates a new GraphQL client with the user's token
- **No Token Leakage**: User identities and tokens are stored in request context (thread-safe)
- **Cway Scoping**: Tokens are already scoped to user+org by Cway's API
- **Identity Caching**: User identities cached for 5 minutes to reduce API calls

## Token Flow

```
1. ChatGPT → HTTP Request
   Authorization: Bearer user_token_abc123
   
2. SSE Middleware → Extract Token
   - Validate with Cway API (GET /me)
   - Extract user_id, org_id, org_name
   - Load registered org tokens from database
   - Set request context
   
3. Tool Execution → Per-Request Client
   - Create CwayGraphQLClient(api_token=user_token)
   - Execute GraphQL query
   - Return user-specific data
   
4. Cleanup
   - Disconnect GraphQL client
   - Clear request context
```

## Backward Compatibility

The server maintains backward compatibility for local development:

- **STDIO Transport** (Claude Desktop): Uses `CWAY_API_TOKEN` from `.env`
- **SSE without Auth header**: Falls back to `.env` token
- **Single-user mode**: Works exactly as before

## Production Deployment

For production deployment:

1. **Use HTTPS**: Tokens are sent in headers (use TLS/SSL)
2. **Set TOKEN_ENCRYPTION_KEY**: Use a strong, randomly generated key
3. **Secure the database**: `TOKEN_DB_PATH` should be on encrypted storage
4. **Monitor logs**: Watch for authentication failures
5. **Backup tokens.db**: Users will lose org tokens if database is lost

## Troubleshooting

### User gets "No authentication token available"

- User hasn't configured Bearer token in ChatGPT MCP connector
- Server `.env` doesn't have `CWAY_API_TOKEN` fallback

### User gets "Invalid token or API error"

- Token is expired or invalid
- Cway API is unreachable
- User doesn't have permission to access the organization

### Multi-org query returns empty results

- User hasn't registered tokens for those organizations
- Use `list_my_organizations()` to see registered orgs
- Register missing tokens with `register_org_token()`

### "No user identity in request context"

- SSE middleware failed to extract token
- Token validation with Cway API failed
- Check server logs for details

## API Reference

### MCP Tools

#### `register_org_token(org_name: str, token: str)`
Register an additional organization token for the current user.

#### `list_my_organizations()`
List all organizations registered for the current user.

#### `remove_org_token(org_name: str)`
Remove a previously registered organization token.

#### `list_projects(orgs: Optional[List[str]])`
List projects, optionally from multiple organizations.

## Development

### Run Tests

```bash
cd server
python -m pytest tests/ -v --cov=src
```

### Generate New Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Inspect Token Database

```bash
sqlite3 data/tokens.db
.tables
.schema user_tokens
SELECT user_id, org_name, created_at FROM user_tokens;
```

Note: Tokens are encrypted, so you'll see ciphertext in the `encrypted_token` column.
