# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Cway MCP Server is a comprehensive Model Context Protocol (MCP) server that provides seamless integration with Cway's GraphQL API. It's built as a full-stack application with a Python MCP server backend and React TypeScript dashboard frontend, following CLEAN architecture principles and TDD practices.

## Architecture

### Clean Architecture Structure
The server follows CLEAN architecture with strict layer separation:
- **Domain Layer** (`server/src/domain/`): Core business entities, value objects, and repository interfaces
- **Application Layer** (`server/src/application/`): Use cases and business logic orchestration
- **Infrastructure Layer** (`server/src/infrastructure/`): External integrations (GraphQL client, repositories)
- **Presentation Layer** (`server/src/presentation/`): MCP server implementations and controllers

### Key Components
- **MCP Server**: Python-based server implementing Model Context Protocol
  - **stdio transport**: For Claude Desktop and similar clients
  - **SSE transport**: For ChatGPT custom MCP connector
- **REST API**: FastAPI-based REST API with OpenAPI documentation (for ChatGPT GPT custom actions, NOT MCP)
- **GraphQL Client**: Async client for Cway API integration with connection pooling
- **WebSocket Dashboard**: Real-time monitoring and logging system
- **React Dashboard**: Modern TypeScript frontend with Framer Motion animations

## Development Commands

### Server Development
```bash
# Start MCP server only
cd server && python main.py --mode mcp

# Start MCP server with SSE transport (for ChatGPT MCP connector)
cd server && python main.py --mode sse
# or
cd server && python start_mcp_sse.py

# Start REST API server (for ChatGPT GPT custom actions)
cd server && python main.py --mode rest
# or
cd server && python start_rest_api.py

# Start server with WebSocket dashboard
cd server && python main.py --mode dashboard

# Run tests with coverage (HTML report generated)
cd server && python -m pytest tests/ -v --cov=src --cov-report=html

# Run single test file
cd server && python -m pytest tests/unit/test_domain_entities.py -v

# Format and lint code
cd server && python -m black src/ tests/ && python -m isort src/ tests/ && python -m flake8 src/ tests/

# Type checking
cd server && python -m mypy src/
```

### Client Development
```bash
# Start React dashboard (runs on port 3001)
cd client && npm start

# Build for production
cd client && npm run build

# Run tests
cd client && npm test
```

### Full Stack Development
```bash
# Terminal 1: Start server with dashboard
cd server && python main.py --mode dashboard

# Terminal 2: Start React client
cd client && npm start

# Access points:
# - React Dashboard: http://localhost:3001
# - WebSocket Server: http://localhost:8080
# - Health Check: http://localhost:8080/health
```

### Make Commands (Alternative)
```bash
# Project setup
make install

# Run all validation (format, lint, test)
make validate

# Start MCP server
make run

# Docker build and run
make docker-build && make docker-run
```

### Warp Tasks
Use Warp's task system with pre-configured commands:
- `server:start` - Start MCP server
- `server:start-with-dashboard` - Start with WebSocket dashboard
- `server:test-coverage` - Tests with HTML coverage report
- `client:start` - Start React dashboard
- `project:setup` - Complete project initialization

## Testing Strategy

### Test Structure
- **Unit Tests**: Fast, isolated tests in `server/tests/unit/`
- **Integration Tests**: End-to-end API tests in `server/tests/integration/`
- **Coverage Target**: Maintains >90% coverage

### Running Tests
```bash
# All tests with coverage
cd server && python -m pytest tests/ -v --cov=src --cov-report=html

# Fast unit tests only
cd server && python -m pytest tests/unit/ -v

# Integration tests (requires CWAY_API_TOKEN)
cd server && python -m pytest tests/integration/ -v
```

## Environment Setup

### Required Environment Variables
```bash
# Copy template and configure
cp .env.example server/.env

# Required:
CWAY_API_TOKEN=your_bearer_token_here
CWAY_API_URL=https://app.cway.se/graphql

# Optional:
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

### Virtual Environment
```bash
# Create and activate
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
cd server && pip install -r requirements.txt
cd ../client && npm install
```

## Code Quality Standards

### Python Standards
- **Formatting**: Black (line length: 88)
- **Import sorting**: isort with Black profile
- **Linting**: flake8 with complexity checks
- **Type checking**: mypy with strict settings
- **Testing**: pytest with asyncio support

### TypeScript Standards
- **React**: TypeScript with strict configuration
- **Testing**: React Testing Library
- **Animations**: Framer Motion for smooth transitions
- **UI Icons**: Lucide React

### Pre-commit Hooks
Automatically runs on commit:
- Trailing whitespace removal
- Black formatting
- isort import sorting
- flake8 linting
- mypy type checking
- pytest test execution

## REST API

### Starting the REST API
```bash
# Start REST API server (default port: 8000)
cd server && python main.py --mode rest

# Access points:
# - API Root: http://localhost:8000/
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - OpenAPI Spec: http://localhost:8000/openapi.json
# - Health Check: http://localhost:8000/health
```

### Available Endpoints

#### Projects
- `GET /api/projects` - List all projects
- `GET /api/projects/{project_id}` - Get project by ID
- `GET /api/projects/filter/active` - Get active projects
- `GET /api/projects/filter/completed` - Get completed projects

#### Users
- `GET /api/users` - List all users
- `GET /api/users/{user_id}` - Get user by ID
- `GET /api/users/by-email/{email}` - Get user by email

#### KPIs
- `GET /api/kpis/dashboard` - Get comprehensive KPI dashboard
- `GET /api/kpis/project-health` - Get project health scores
- `GET /api/kpis/critical-projects` - Get projects requiring attention

#### Temporal KPIs
- `GET /api/temporal-kpis/dashboard?analysis_period_days=90` - Get temporal analysis
- `GET /api/temporal-kpis/stagnation-alerts?min_urgency_score=5` - Get stagnation alerts

#### System
- `GET /api/system/status` - Get system status
- `GET /health` - Health check (no auth required)

### Authentication
All API endpoints (except `/health`) require Bearer token authentication:
```bash
# Example with curl
curl -H "Authorization: Bearer YOUR_CWAY_API_TOKEN" \
  http://localhost:8000/api/projects

# Example with httpie
http GET localhost:8000/api/projects \
  Authorization:"Bearer YOUR_CWAY_API_TOKEN"
```

### Export OpenAPI Spec
```bash
# Export OpenAPI specification for ChatGPT GPT integration
cd server && python scripts/export_openapi.py

# Output: server/openapi.json
```

## ChatGPT GPT Integration

### Creating a ChatGPT GPT with Cway Actions

1. **Export the OpenAPI spec**:
   ```bash
   cd server && python scripts/export_openapi.py
   ```

2. **Create or edit a GPT**:
   - Go to https://chat.openai.com/gpts/editor
   - Create new GPT or edit existing

3. **Configure Actions**:
   - Navigate to "Actions" section
   - Click "Import from file" or paste JSON
   - Upload `server/openapi.json`

4. **Set up Authentication**:
   - Type: **Bearer**
   - Token: Your `CWAY_API_TOKEN` from `.env` file

5. **Update Server URL** (if not localhost):
   - Edit the `servers` section in OpenAPI spec
   - Point to your deployed REST API URL

6. **Example GPT Instructions**:
   ```
   You are a Cway project management assistant with access to the Cway API.
   You can:
   - List and search projects
   - Get project details and status
   - List users and find team members
   - Monitor project health and identify risks
   - Track stagnation and velocity trends
   
   Always provide clear, actionable insights from the data.
   ```

### Benefits of REST API + ChatGPT GPT
- Natural language interface to Cway data
- Custom GPT can analyze trends and provide insights
- Shareable with team members (with appropriate auth)
- Works with both local development and production APIs

## MCP Integration

### Available Tools
- `list_projects`: Retrieve all Cway projects
- `get_project`: Get specific project by ID
- `get_active_projects`: List active projects
- `get_completed_projects`: List completed projects
- `list_users`: Retrieve all users
- `get_user`: Get specific user by ID
- `find_user_by_email`: Find user by email
- `get_system_status`: System health check

### Available Resources
- `cway://projects`: All Cway planner projects
- `cway://users`: All Cway users  
- `cway://projects/active`: Currently active projects
- `cway://projects/completed`: Completed projects
- `cway://system/status`: System connection status

## Docker Support

### Development
```bash
# Build and run with docker-compose
docker-compose up --build

# Run with monitoring stack (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### Production
Multi-stage Docker build optimized for production with security best practices and health checks.

## Troubleshooting

### Common Issues
- **API Connection**: Verify CWAY_API_TOKEN is valid and CWAY_API_URL is accessible
- **Port Conflicts**: Default ports are 8000 (MCP), 8080 (WebSocket), 3001 (React)
- **Dependencies**: Ensure Python 3.11+ and Node.js 18+ are installed
- **Virtual Environment**: Always activate venv before running Python commands

### Debugging
- **Logs**: Check `server/logs/` directory for application logs
- **Dashboard**: Use WebSocket dashboard for real-time monitoring
- **Health Checks**: `/health` endpoint for server status
- **Correlation IDs**: End-to-end request tracing in logs

## CI/CD Pipeline

### GitHub Actions
- **Testing**: Multi-Python version matrix (3.11, 3.12)
- **Security**: Safety and Bandit security scans
- **Code Quality**: Black, isort, flake8, mypy checks  
- **Coverage**: Codecov integration
- **Docker**: Automated builds and pushes on main branch

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- Feature branches: `feature/feature-name`
