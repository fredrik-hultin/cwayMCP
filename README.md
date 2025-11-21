# 🔄 Cway MCP Server (SSE)

> A Model Context Protocol (MCP) server with SSE transport for seamless ChatGPT MCP connector integration with Cway GraphQL API.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-orange.svg)](https://modelcontextprotocol.io/)
[![SSE](https://img.shields.io/badge/transport-SSE-green.svg)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## ✨ Features

### 🚀 SSE Transport
- **Server-Sent Events** - Persistent HTTP connections for real-time MCP protocol
- **ChatGPT Compatible** - Works with ChatGPT's custom MCP connector
- **Token Passthrough** - Per-user authentication via Bearer tokens
- **OAuth2 Support** - MSAL integration for Azure AD authentication

### 📊 Cway API Integration
- **GraphQL Client** - Direct connection to Cway's GraphQL endpoint
- **Resource Management** - Structured access to projects, users, and system data
- **Tool Framework** - Extensible tool system for data operations
- **Type Safety** - Full Python type definitions with Pydantic

### 🎯 Data Access
- **Project Management** - List, filter, and access Cway planner projects
- **User Operations** - Comprehensive user data retrieval and management
- **KPI Dashboards** - Project health scores and temporal analytics
- **System Status** - Connection health and API status monitoring

## 🏛️ Architecture

### Clean Architecture
```
server/src/
├── 🎭 presentation/     # MCP server (SSE transport)
├── 🧠 application/      # Use cases, business logic
├── 🏭 infrastructure/   # GraphQL client, auth, repositories
└── 🏛️ domain/          # Entities, value objects
```

## 📋 Prerequisites

- **Python 3.11+** with pip and venv
- **Cway API Access Token** (Bearer token) or OAuth2 setup
- **Virtual Environment** (recommended)

## ⚡ Quick Start

### 1️⃣ Project Setup
```bash
# Clone the repository
git clone <repository-url>
cd cwayMCP

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2️⃣ Install Dependencies
```bash
# Install server dependencies
cd server && pip install -r requirements.txt
```

### 3️⃣ Environment Configuration
```bash
# Copy environment template
cp .env.example server/.env

# Edit server/.env with your Cway API token:
echo "CWAY_API_TOKEN=your_bearer_token_here" >> server/.env
```

### 4️⃣ Start the Server
```bash
# Start MCP server with SSE transport
cd server && python main.py
```

### 5️⃣ Access Points
- **SSE Endpoint**: http://localhost:8000/sse
- **Messages Endpoint**: http://localhost:8000/messages

### 6️⃣ ChatGPT Integration
Add this MCP server to ChatGPT:
1. Go to ChatGPT settings
2. Add custom MCP server
3. URL: `http://localhost:8000/sse`
4. Authentication: Bearer token (your CWAY_API_TOKEN)

## 🛠️ Development

### 🧪 Testing

**IMPORTANT**: Read [TESTING_POLICY.md](TESTING_POLICY.md) - We NEVER run tests against the live Cway server.

```bash
# Run all tests with coverage (all use mocks)
cd server && python -m pytest tests/ -v --cov=src --cov-report=html

# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests (mocked, no real API calls)
python -m pytest tests/integration/ -v
```

### 🎨 Code Quality
```bash
# Format and lint code
cd server
python -m black src/ tests/
python -m isort src/ tests/
python -m flake8 src/ tests/
python -m mypy src/
```

### 📁 Project Structure
```
server/
├── src/
│   ├── presentation/    # MCP server (SSE)
│   ├── application/     # Use cases
│   ├── infrastructure/  # GraphQL, auth, repos
│   └── domain/          # Entities, interfaces
├── config/              # Settings
├── tests/               # Unit + integration tests
├── logs/                # Application logs
├── main.py              # Entry point
├── start_mcp_sse.py     # SSE server
└── requirements.txt     # Dependencies
```


## 🔧 Configuration

### Environment Variables
```bash
# Cway API (Required)
CWAY_API_TOKEN=your_bearer_token_here
CWAY_API_URL=https://app.cway.se/graphql

# Server Settings
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO

# OAuth2 (Optional - for Azure AD auth)
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
```

## 🚀 MCP API

### Available Resources
- `cway://projects` - All Cway planner projects
- `cway://users` - All Cway users
- `cway://projects/active` - Active projects only
- `cway://projects/completed` - Completed projects only
- `cway://kpis/dashboard` - KPI dashboard with health scores
- `cway://system/status` - System connection status

### Available Tools
- `list_projects` - Retrieve all projects
- `get_project(project_id)` - Get specific project
- `get_active_projects` - List active projects
- `list_users` - Retrieve all users
- `get_user(user_id)` - Get specific user
- `find_user_by_email(email)` - Find user by email
- `get_kpi_dashboard` - System KPI dashboard
- `get_system_status` - System health check

## 🐳 Docker Support

```bash
# Build and run
docker build -t cway-mcp-sse .
docker run -p 8000:8000 --env-file server/.env cway-mcp-sse
```

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Built with MCP + Python for ChatGPT integration**
