# 🚀 Cway MCP Server

[![CI/CD Pipeline](https://github.com/yourusername/cwayMCP/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/yourusername/cwayMCP/actions)
[![codecov](https://codecov.io/gh/yourusername/cwayMCP/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/cwayMCP)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready Model Context Protocol (MCP) server for seamless integration with the Cway platform via GraphQL API. Built with CLEAN Architecture, comprehensive testing, and enterprise-grade tooling.

## ✨ Features

- 🔐 **Secure Authentication** - Bearer token authentication with Cway GraphQL API
- 🏗️ **CLEAN Architecture** - Maintainable and testable code with clear separation of concerns
- 🧪 **Test-Driven Development** - 91% test coverage with comprehensive test suite
- ⚡ **High Performance** - Async/await throughout with connection pooling
- 🐳 **Docker Ready** - Multi-stage builds with security best practices
- 🔧 **Developer Experience** - Pre-commit hooks, auto-formatting, and comprehensive tooling
- 📊 **Monitoring Ready** - Health checks, metrics, and structured logging
- 🚀 **CI/CD Pipeline** - GitHub Actions with automated testing and deployment

## 🏗️ Architecture

Follows **CLEAN Architecture** principles with dependency inversion:

```
src/
├── domain/           # 🎯 Business entities & rules (innermost layer)
│   ├── entities.py         # Core business entities
│   ├── cway_entities.py    # Cway-specific entities
│   └── repositories.py     # Repository interfaces
├── application/      # 📋 Use cases & business logic
│   └── use_cases.py        # Business operations orchestration
├── infrastructure/   # 🔌 External integrations (outermost layer)
│   ├── graphql_client.py   # GraphQL API client
│   ├── repositories.py     # Repository implementations
│   └── cway_repositories.py # Cway-specific repositories
└── presentation/     # 🌐 MCP server & controllers
    ├── mcp_server.py       # Generic MCP server
    └── cway_mcp_server.py  # Cway-specific MCP server

tests/
├── unit/            # 🧪 Unit tests (91% coverage)
└── integration/     # 🔗 Integration tests
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ 🐍
- Cway API token 🔑
- Make (optional, for convenience) 🛠️

### 1. Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/cwayMCP.git
cd cwayMCP

# One-command setup using Make
make install

# Or manual setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your Cway API token
echo "CWAY_API_TOKEN=your_token_here" > .env
```

### 3. Validate Setup

```bash
# Validate installation and API connection
make validate-setup

# Or manually
python validate_setup.py
```

### 4. Run the Server

```bash
# Start the MCP server
make run

# Or manually
source venv/bin/activate
python run_server.py
```

### 5. Development Workflow

```bash
# Run tests
make test

# Format code
make format

# Run all checks (lint, format, test)
make validate

# Start development server with auto-reload
make dev-server
```

## 🐳 Docker Deployment

### Quick Docker Run

```bash
# Build and run with docker-compose
docker-compose up --build

# Or manually
docker build -t cway-mcp-server .
docker run --env-file .env -p 8000:8000 cway-mcp-server
```

### Production Deployment

```bash
# Build optimized production image
make docker-build

# Deploy with monitoring (optional)
docker-compose --profile monitoring up -d
```

## Configuration

Set the following environment variables:

- `CWAY_API_TOKEN`: Bearer token for Cway GraphQL API
- `CWAY_API_URL`: GraphQL endpoint (default: https://app.cway.se/graphql)
- `MCP_SERVER_PORT`: Port for MCP server (default: 8000)

## MCP Tools Available

The server provides the following tools for AI agents:

### Project Management
- **`list_projects`**: List all Cway projects
- **`get_project`**: Get a specific project by ID
- **`create_project`**: Create a new project
- **`update_project`**: Update an existing project

### User Management
- **`list_users`**: List all Cway users
- **`get_user`**: Get a specific user by ID
- **`get_user_by_email`**: Get a user by email address
- **`create_user`**: Create a new user

### Resources
- **`cway://projects`**: Access to all projects data
- **`cway://users`**: Access to all users data
- **`cway://schema`**: GraphQL API schema information

## Usage with AI Agents

This MCP server can be connected to AI agents like:
- Claude Desktop
- Custom MCP clients
- Other MCP-compatible tools

Example tool usage:
```json
{
  "tool": "create_project",
  "arguments": {
    "name": "My New Project",
    "description": "A project created via MCP",
    "status": "active"
  }
}
```

## Development

This project uses:
- **FastMCP** for MCP server framework
- **GraphQL-core** for GraphQL client operations
- **Pytest** for testing
- **MyPy** for type checking
- **Black** for code formatting

## License

MIT