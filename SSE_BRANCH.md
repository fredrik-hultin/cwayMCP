# SSE-Only Branch

This is a simplified version of the Cway MCP Server that **only** supports SSE (Server-Sent Events) transport for ChatGPT MCP connector integration.

## What's Included

### ✅ Core Features
- **SSE Transport** - MCP server with Server-Sent Events for ChatGPT
- **Token Passthrough** - Per-user authentication via Bearer tokens
- **OAuth2 Support** - Azure AD integration via MSAL
- **Full MCP Implementation** - All tools and resources
- **Clean Architecture** - Domain, application, infrastructure layers
- **GraphQL Client** - Cway API integration
- **Comprehensive Tests** - Unit and integration test suites

### 📁 Code Structure
```
server/
├── src/
│   ├── presentation/       # MCP server + SSE transport
│   ├── application/        # Use cases, business logic
│   ├── infrastructure/     # GraphQL, auth, repos
│   └── domain/            # Entities, value objects
├── config/                # Settings
├── tests/                 # Tests
├── main.py               # Simple entry point (just starts SSE)
├── start_mcp_sse.py      # SSE server implementation
└── requirements.txt      # Minimal dependencies
```

## What's Removed

- ❌ **stdio mode** - No `python main.py --mode mcp`
- ❌ **REST API** - No FastAPI endpoints or OpenAPI
- ❌ **Dashboard** - No WebSocket server or React client
- ❌ **client/ directory** - Removed completely
- ❌ **Multi-mode main.py** - Simplified to SSE-only
- ❌ **Unnecessary dependencies** - No fastapi, python-socketio

## Starting the Server

```bash
# Simple way
cd server && python main.py

# Or directly
cd server && python start_mcp_sse.py
```

Server will start on `http://localhost:8000`:
- SSE endpoint: `http://localhost:8000/sse`
- Messages endpoint: `http://localhost:8000/messages`

## ChatGPT Integration

1. Go to ChatGPT settings
2. Add custom MCP server
3. URL: `http://localhost:8000/sse`
4. Auth: Bearer token (your `CWAY_API_TOKEN`)

## Environment Setup

```bash
# Required
CWAY_API_TOKEN=your_bearer_token_here
CWAY_API_URL=https://app.cway.se/graphql

# Optional
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
```

## Dependencies

Minimal set for SSE operation:
- `mcp` - MCP framework
- `gql[all]` - GraphQL client
- `starlette` + `uvicorn` - SSE server
- `sse-starlette` - SSE transport
- `pydantic` - Configuration
- `msal` + `httpx` - OAuth2

## Testing

```bash
# All tests
cd server && python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Branching Strategy

- **main** - Full-featured version (stdio + REST + dashboard)
- **feature/sse-only** - This branch (SSE only)

Use this branch when you want:
- Clean SSE-only deployment
- ChatGPT MCP connector integration
- Minimal dependencies
- Simplified codebase for SSE use case
