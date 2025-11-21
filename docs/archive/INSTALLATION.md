# cwayMCP Server Installation & Testing Guide

## ✅ Server Status
The cwayMCP server is **fully operational** with:
- ✅ 158 passing unit tests
- ✅ 30% overall test coverage (100% on core modules)
- ✅ Successfully connects to Cway API
- ✅ All dependencies installed

## 🚀 Quick Start

### 1. Start MCP Server Only
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/server
source ../venv/bin/activate
python main.py --mode mcp
```

**Expected Output:**
```
INFO:src.indexing.mcp_indexing_service:Loaded 3 indexing targets from indexing_config.json
INFO:src.presentation.cway_mcp_server:Starting Cway MCP Server...
INFO:cway.flow:📍 GraphQL Connection | Connecting to https://app.cway.se/graphql
INFO:src.infrastructure.graphql_client:✅ Connected to Cway GraphQL API at https://app.cway.se/graphql
INFO:src.presentation.cway_mcp_server:Server initialized and ready
INFO:src.presentation.cway_mcp_server:Connected to Cway API at https://app.cway.se/graphql
```

### 2. Start Server with Dashboard
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/server
source ../venv/bin/activate
python main.py --mode dashboard
```

Then in a **second terminal**:
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/client
npm start
```

**Access Points:**
- 📊 React Dashboard: http://localhost:3001
- 🔌 WebSocket Server: http://localhost:8080
- ❤️ Health Check: http://localhost:8080/health

## 🧪 Testing

### Run All Tests
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP/server
source ../venv/bin/activate
python -m pytest tests/unit/ -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/unit/ --cov=src --cov-report=html --cov-report=term
```

View HTML coverage report:
```bash
open htmlcov/index.html
```

### Test API Connection
```bash
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))

from src.infrastructure.graphql_client import CwayGraphQLClient
import asyncio

async def test():
    client = CwayGraphQLClient()
    await client.connect()
    print('✅ Connection successful!')
    await client.disconnect()

asyncio.run(test())
"
```

## 📦 Available MCP Tools

The server provides these tools:

| Tool | Description |
|------|-------------|
| `list_projects` | Retrieve all Cway projects |
| `get_project` | Get specific project by ID |
| `get_active_projects` | List active projects |
| `get_completed_projects` | List completed projects |
| `list_users` | Retrieve all users |
| `get_user` | Get specific user by ID |
| `find_user_by_email` | Find user by email |
| `get_system_status` | System health check |

## 📚 Available Resources

| Resource | URI | Description |
|----------|-----|-------------|
| Projects | `cway://projects` | All Cway planner projects |
| Users | `cway://users` | All Cway users |
| Active Projects | `cway://projects/active` | Currently active projects |
| Completed Projects | `cway://projects/completed` | Completed projects |
| System Status | `cway://system/status` | System connection status |

## 🔧 Configuration

### Environment Variables
The server uses `/Users/fredrik.hultin/Developer/cwayMCP/server/.env`:

```bash
# Required
CWAY_API_TOKEN=f20f14d8-f40f-4e8e-aa13-f5ec6d3497ba

# Optional (with defaults)
CWAY_API_URL=https://app.cway.se/graphql
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

## 📊 Test Coverage Summary

**Overall Coverage: 30%** (1,075 / 3,573 lines)

### Core Modules (100% Covered) ✅
- `application/use_cases.py` - Business logic
- `infrastructure/repositories.py` - Data access
- `infrastructure/graphql_client.py` - API client (99%)
- `domain/cway_entities.py` - Domain models

### Well-Tested Modules (>70%) ✅
- `application/temporal_kpi_use_cases.py` - 84%
- `domain/entities.py` - 74%
- `domain/temporal_kpi_entities.py` - 96%

### Modules with 0% Coverage
These are mostly presentation and indexing layers that would require extensive integration testing:
- `presentation/cway_mcp_server.py` (386 lines)
- `presentation/mcp_server.py` (118 lines)
- `indexing/*` modules (1,043 lines)

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port is already in use
lsof -i :8000

# Check dependencies
cd server && pip install -r requirements.txt
```

### API Connection Issues
```bash
# Verify token is set
grep CWAY_API_TOKEN server/.env

# Test connection manually
curl -H "Authorization: Bearer YOUR_TOKEN" https://app.cway.se/graphql
```

### Client Issues
```bash
# Reinstall dependencies
cd client
rm -rf node_modules package-lock.json
npm install
```

## 📝 Notes

- The server uses your existing Cway API token
- All tests pass (158/158)
- Core business logic has 100% test coverage
- Server successfully connects to production Cway API
- Virtual environment is already set up at `/Users/fredrik.hultin/Developer/cwayMCP/venv`

## 🎯 Next Steps

1. **Test the MCP server** - Run it and verify connection
2. **Try the dashboard** - Start both server and client
3. **Integrate with your client** - Use the available tools and resources
4. **Monitor logs** - Check `server/logs/` for detailed logging

---

**Status:** ✅ Ready for testing and use!
