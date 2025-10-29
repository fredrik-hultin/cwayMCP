# 🔄 Cway MCP Server

> A comprehensive Model Context Protocol (MCP) server for seamless Cway GraphQL API integration with real-time dashboard monitoring.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-orange.svg)](https://modelcontextprotocol.io/)

## ✨ Features

### 🚀 Core MCP Integration
- **GraphQL API Integration** - Direct connection to Cway's GraphQL endpoint
- **Resource Management** - Structured access to projects, users, and system data  
- **Tool Framework** - Extensible tool system for data operations
- **Type Safety** - Full TypeScript/Python type definitions

### 📊 Real-time Dashboard
- **Live Flow Visualization** - See data requests flow MCP Client → Server → Cway API
- **WebSocket Updates** - Real-time log streaming and status monitoring
- **Interactive UI** - Modern React dashboard with animations and responsive design
- **Request Tracking** - Correlation IDs for end-to-end request tracing

### 🎯 Data Access
- **Project Management** - List, filter, and access Cway planner projects
- **User Operations** - Comprehensive user data retrieval and management
- **System Status** - Connection health and API status monitoring
- **Pagination Support** - Efficient handling of large datasets

## 🏗️ Architecture

### Clean Architecture Design
```
🏛️ Presentation Layer    │ 🧠 Application Layer     │ 🏭 Infrastructure Layer
├── MCP Server           │ ├── Use Cases            │ ├── GraphQL Client
├── WebSocket Server     │ ├── Services             │ ├── Repositories  
└── Dashboard API        │ └── DTOs                  │ └── External APIs
                         │                           │
📁 Project Structure:
server/src/
├── 🎭 presentation/     # MCP server, WebSocket server
├── 🧠 application/      # Use cases, business services
├── 🏛️ domain/          # Entities, value objects, interfaces
├── 🏭 infrastructure/   # GraphQL client, repositories
└── 🛠️ utils/           # Logging, configuration
```

## 📋 Prerequisites

- **Python 3.9+** with pip and venv
- **Node.js 18+** with npm
- **Cway API Access Token** (Bearer token)
- **Virtual Environment** (strongly recommended)

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

# Install client dependencies  
cd ../client && npm install && cd ..
```

### 3️⃣ Environment Configuration
```bash
# Copy environment template
cp .env.example server/.env

# Edit server/.env with your Cway API token:
echo "CWAY_API_TOKEN=your_bearer_token_here" >> server/.env
```

### 4️⃣ Launch Application

**🎯 Full Stack (Recommended) - Single Command**
```bash
# Use the convenient start script (starts both backend and React dashboard)
./start-dashboard.sh
```

**🎯 Full Stack (Manual)**
```bash
# Terminal 1: Start server with dashboard
cd server && python main.py --mode dashboard

# Terminal 2: Start React client  
cd client && npm start
```

**🚀 MCP Server Only**
```bash
# Use the start script
./start-mcp.sh

# Or manually
cd server && python main.py --mode mcp
```

### 5️⃣ Access Dashboard
- **📊 React Dashboard**: http://localhost:3001
- **🔌 WebSocket Server**: http://localhost:8080  
- **❤️ Health Check**: http://localhost:8080/health

## 🛠️ Development Workflow

### 🧪 Testing
```bash
# Server tests with coverage
cd server && python -m pytest tests/ -v --cov=src --cov-report=html

# Client tests
cd client && npm test
```

### 🎨 Code Quality
```bash
# Python formatting & linting
cd server
python -m black src/ tests/
python -m isort src/ tests/  
python -m flake8 src/ tests/
python -m mypy src/

# TypeScript checking
cd client && npm run type-check
```

### 📁 Project Structure
```
cwayMCP/
├── 🐍 server/              # Python MCP Server
│   ├── 📦 src/            # Source code (Clean Architecture)
│   ├── ⚙️ config/        # Configuration management
│   ├── 🧪 tests/         # Comprehensive test suite
│   ├── 📊 logs/          # Application logs
│   ├── 📋 requirements.txt
│   ├── ⚙️ pyproject.toml
│   └── 🚀 main.py        # Entry point
├── ⚛️ client/             # React Dashboard  
│   ├── 📦 src/           # React components & services
│   ├── 🌐 public/       # Static assets
│   ├── 📋 package.json
│   └── ⚙️ tsconfig.json
├── 📚 docs/               # Documentation
├── 🔧 .warp/             # Warp terminal configuration
├── 🌍 .env.example       # Environment template
└── 📖 README.md          # This file
```

## 🎛️ Warp Terminal Integration

This project includes Warp terminal configuration for enhanced development experience:

### 🚀 Quick Launch Profiles
- **🚀 MCP Server Only** - Launch server without dashboard
- **📊 Full Stack** - Launch server with WebSocket dashboard 
- **⚛️ Dashboard Client** - Launch React client only
- **🧪 Run Tests** - Execute test suite with coverage
- **⚙️ Setup Project** - Complete project initialization

### ⚡ Development Tasks
Access via Warp's command palette:
- `server:start` - Start MCP server
- `server:test-coverage` - Run tests with HTML coverage
- `client:build` - Build production client
- `project:clean` - Clean build artifacts
- `api:test-connection` - Test Cway API connectivity

## 📊 Dashboard Features

### 🔄 Real-time Monitoring
- **📈 Live Metrics** - Success rates, response times, request counts
- **🌊 Flow Visualization** - Animated request path tracking  
- **🔗 Connection Status** - WebSocket health monitoring
- **📝 Live Logs** - Streaming logs with filtering and correlation IDs

### 🎨 Interactive Elements
- **✨ Animations** - Smooth transitions with Framer Motion
- **📱 Responsive Design** - Desktop and mobile optimized
- **🎯 Request Correlation** - End-to-end request tracking
- **🔍 Advanced Filtering** - Filter logs by level, source, time

## 🔧 Configuration

### 🌍 Environment Variables
```bash
# 🔑 Cway API Configuration (Required)
CWAY_API_TOKEN=your_bearer_token_here
CWAY_API_URL=https://app.cway.se/graphql

# 🚀 Server Configuration  
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000

# 🛠️ Development Settings
LOG_LEVEL=INFO
DEBUG=false

# 📊 Dashboard Settings
WEBSOCKET_PORT=8080
REACT_PORT=3001
```

### ⚙️ Advanced Configuration
- **🔍 Logging** - Structured logging with multiple outputs
- **🔌 WebSocket** - Real-time communication settings
- **🚦 Rate Limiting** - API request throttling
- **📊 Monitoring** - Health checks and metrics

## 🚦 API Operations

### 📋 Available Resources
| Resource | Description |
|----------|-------------|
| `cway://projects` | All Cway planner projects |
| `cway://users` | All Cway users |
| `cway://projects/active` | Currently active projects |
| `cway://projects/completed` | Completed projects |
| `cway://system/status` | System connection status |

### 🛠️ Available Tools
| Tool | Parameters | Description |
|------|------------|-------------|
| `list_projects` | - | Retrieve all projects with metadata |
| `get_project` | `project_id` | Get specific project by ID |
| `get_active_projects` | - | List currently active projects |
| `get_completed_projects` | - | List completed projects |
| `list_users` | - | Retrieve all users |
| `get_user` | `user_id` | Get specific user by ID |
| `find_user_by_email` | `email` | Find user by email address |
| `get_users_page` | `page`, `size` | Paginated user retrieval |
| `get_system_status` | - | System health and connection info |

## 🧪 Testing Strategy

### 🏗️ Test Structure
```
server/tests/
├── 🧪 unit/              # Fast, isolated tests
│   ├── test_domain_entities.py
│   ├── test_use_cases.py  
│   ├── test_graphql_client.py
│   └── test_repositories.py
├── 🔗 integration/       # End-to-end tests
│   ├── test_cway_repositories.py
│   └── test_mcp_server.py
└── ⚙️ conftest.py       # Test configuration
```

### 🚀 Running Tests
```bash
# All tests with HTML coverage report
cd server && python -m pytest tests/ -v --cov=src --cov-report=html

# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests (requires API token)
python -m pytest tests/integration/ -v

# Specific test file
python -m pytest tests/unit/test_domain_entities.py -v
```

## 🐳 Docker Support

### 🔨 Build & Deploy
```bash
# Build Docker image
docker build -t cway-mcp-server .

# Run with docker-compose
docker-compose up -d

# Development with hot reload
docker-compose -f docker-compose.dev.yml up
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `📖 docs/api.md` | API documentation and examples |
| `🏗️ docs/architecture.md` | Detailed architecture guide |
| `🚀 docs/deployment.md` | Production deployment guide |
| `🤝 docs/contributing.md` | Contributing guidelines |
| `🔧 docs/configuration.md` | Advanced configuration options |

## 🤝 Contributing

### 🚀 Getting Started
1. **🍴 Fork** the repository
2. **🌿 Branch**: `git checkout -b feature/amazing-feature`
3. **✨ Code**: Make your changes and add tests
4. **🧪 Test**: Ensure all tests pass
5. **🎨 Format**: Run code formatters
6. **💾 Commit**: Use conventional commit format
7. **📤 Push**: `git push origin feature/amazing-feature`
8. **🔄 PR**: Open a Pull Request

### 📏 Code Standards
- **🐍 Python**: Black formatting, isort imports, flake8 linting, mypy typing
- **📝 TypeScript**: Prettier formatting, ESLint rules, strict TypeScript
- **💬 Commits**: Conventional commits format (`feat:`, `fix:`, `docs:`)
- **🧪 Testing**: Required for all new features
- **📚 Documentation**: Update docs for API changes

## 🗺️ Roadmap

### 🎯 Short Term (v0.2)
- [ ] **🔍 Enhanced Filtering** - Advanced search and filter capabilities
- [ ] **📊 Analytics Dashboard** - Request metrics and performance insights
- [ ] **🔄 Auto-reconnection** - Robust WebSocket reconnection logic
- [ ] **📱 Mobile Optimization** - Improved mobile dashboard experience

### 🚀 Medium Term (v0.3)
- [ ] **🔌 Plugin System** - Custom integrations and extensions
- [ ] **⚡ Real-time Collaboration** - Multi-user dashboard features  
- [ ] **🏢 Multi-tenancy** - Support for multiple Cway instances
- [ ] **📈 Advanced Analytics** - Historical data and trend analysis

### 🌟 Long Term (v1.0)
- [ ] **🤖 AI Integration** - Smart insights and predictions
- [ ] **🌐 GraphQL Federation** - Multi-service integration
- [ ] **☁️ Cloud Native** - Kubernetes deployment options
- [ ] **🛡️ Enterprise Security** - Advanced auth and compliance

## 🆘 Support & Community

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/your-repo/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **📖 Documentation**: Check the `docs/` directory
- **❓ Questions**: Use GitHub Discussions Q&A
- **💬 Community**: Join our Discord/Slack community

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **🏗️ MCP Framework** - For the excellent protocol specification
- **🎨 Lucide React** - For beautiful icons
- **✨ Framer Motion** - For smooth animations
- **⚛️ React Community** - For the amazing ecosystem
- **🐍 Python Community** - For robust tooling and libraries

---

<div align="center">

**Built with ❤️ using MCP, Python, React, and TypeScript**

[⭐ Star this repo](https://github.com/your-repo) • [🐛 Report Bug](https://github.com/your-repo/issues) • [💡 Request Feature](https://github.com/your-repo/discussions)

</div>