# Cway MCP REST API

FastAPI-based REST API with automatic OpenAPI documentation, designed for ChatGPT GPT custom actions and broader API access.

## Quick Start

### Starting the Server

```bash
# Method 1: Using main.py
cd server && python main.py --mode rest

# Method 2: Using dedicated script
cd server && python start_rest_api.py
```

**Default Configuration:**
- **Host**: localhost
- **Port**: 8000
- **Auto-reload**: Enabled in debug mode

### Access Points

- **API Root**: http://localhost:8000/
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Specification**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## Authentication

All endpoints (except `/health`) require Bearer token authentication:

```bash
# Set your token
export CWAY_TOKEN="your_cway_api_token_here"

# Example request with curl
curl -H "Authorization: Bearer $CWAY_TOKEN" \
  http://localhost:8000/api/projects

# Example with httpie
http GET localhost:8000/api/projects \
  Authorization:"Bearer $CWAY_TOKEN"
```

## API Endpoints

### Projects

**List all projects**
```http
GET /api/projects
```

**Get specific project**
```http
GET /api/projects/{project_id}
```

**Get active projects**
```http
GET /api/projects/filter/active
```

**Get completed projects**
```http
GET /api/projects/filter/completed
```

### Users

**List all users**
```http
GET /api/users
```

**Get specific user**
```http
GET /api/users/{user_id}
```

**Get user by email**
```http
GET /api/users/by-email/{email}
```

### KPIs

**Get KPI dashboard**
```http
GET /api/kpis/dashboard
```

**Get project health scores**
```http
GET /api/kpis/project-health
```

**Get critical projects**
```http
GET /api/kpis/critical-projects
```

### Temporal KPIs

**Get temporal dashboard**
```http
GET /api/temporal-kpis/dashboard?analysis_period_days=90
```

**Get stagnation alerts**
```http
GET /api/temporal-kpis/stagnation-alerts?min_urgency_score=5
```

### System

**Get system status** (requires auth)
```http
GET /api/system/status
```

**Health check** (no auth required)
```http
GET /health
```

## Response Format

All successful responses follow this structure:

```json
{
  "projects": [...],
  "total": 10
}
```

Error responses:

```json
{
  "error": "ErrorType",
  "message": "Human readable message",
  "detail": "Technical details (debug mode only)",
  "correlation_id": "req_abc123"
}
```

## ChatGPT GPT Integration

### Step-by-Step Setup

#### 1. Export OpenAPI Specification

```bash
cd server
python scripts/export_openapi.py
```

This creates `server/openapi.json` with your API specification.

#### 2. Create Custom GPT

1. Go to https://chat.openai.com/gpts/editor
2. Click **Create** or edit an existing GPT
3. Fill in basic information:
   - **Name**: Cway Assistant
   - **Description**: AI assistant with access to Cway project management data
   
#### 3. Configure Actions

1. Navigate to the **Actions** section
2. Click **Import from file** or click to paste JSON
3. Upload or paste the contents of `server/openapi.json`
4. The schema will be automatically imported

#### 4. Set Up Authentication

1. In the Actions section, scroll to **Authentication**
2. Select **Bearer** authentication type
3. Enter your `CWAY_API_TOKEN` (from `.env` file)

#### 5. Update Server URL (Production Only)

For local development, keep the default `http://localhost:8000`.

For production:
1. Edit `server/openapi.json`
2. Update the `servers` section:
   ```json
   "servers": [
     {
       "url": "https://your-api-domain.com",
       "description": "Production server"
     }
   ]
   ```
3. Re-import the updated specification

#### 6. Example GPT Instructions

```
You are a Cway project management assistant with real-time access to project data.

Your capabilities:
- List and search projects (active, completed, all)
- Get detailed project information (status, progress, dates)
- List and find users by name or email
- Monitor project health scores and identify risks
- Track project velocity and detect stagnation
- Provide KPI dashboards and analytics

When providing insights:
- Be concise and actionable
- Highlight risks and opportunities
- Compare against benchmarks when relevant
- Suggest next steps or recommendations

Always format data clearly using:
- Tables for comparing multiple items
- Bullet points for lists
- Progress indicators for percentages
- Status emojis (🟢 good, 🟡 warning, 🔴 critical)
```

### Testing Your GPT

Once configured, test with queries like:

- "Show me all active projects"
- "What's the health score for project X?"
- "Which projects are at risk of stagnation?"
- "Find the user with email john@example.com"
- "Give me a KPI dashboard summary"

## Development

### Running Tests

```bash
cd server
python -m pytest tests/integration/test_rest_api.py -v
```

### Code Quality

```bash
# Format
python -m black src/presentation/rest_api.py src/presentation/rest_models.py

# Type check
python -m mypy src/presentation/rest_api.py

# Lint
python -m flake8 src/presentation/rest_api.py
```

### Hot Reload

The server automatically reloads on code changes when `DEBUG=true` in `.env`:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Architecture

### CLEAN Architecture Layers

```
┌─────────────────────────────────────────┐
│    Presentation Layer (REST API)        │
│  - FastAPI endpoints                    │
│  - Pydantic models                      │
│  - Authentication middleware            │
│  - Error handling                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Application Layer (Use Cases)        │
│  - ProjectUseCases                      │
│  - UserUseCases                         │
│  - KPIUseCases                          │
│  - TemporalKPICalculator                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Infrastructure Layer (Repositories)   │
│  - CwayGraphQLClient                    │
│  - CwayProjectRepository                │
│  - CwayUserRepository                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        External Services                │
│  - Cway GraphQL API                     │
└─────────────────────────────────────────┘
```

### Key Components

- **`rest_api.py`**: FastAPI application and endpoints
- **`rest_models.py`**: Pydantic request/response models
- **`start_rest_api.py`**: Standalone server launcher
- **`scripts/export_openapi.py`**: OpenAPI spec exporter

## Security

### Best Practices

1. **Never commit tokens**: Keep `.env` in `.gitignore`
2. **Use environment variables**: Store `CWAY_API_TOKEN` securely
3. **HTTPS in production**: Always use SSL/TLS for production APIs
4. **Rate limiting**: Consider adding rate limiting for production
5. **CORS configuration**: Restrict origins in production

### CORS Configuration

Default (development):
```python
allow_origins=["*"]  # Allow all origins
```

Production:
```python
allow_origins=[
    "https://your-frontend.com",
    "https://chat.openai.com"
]
```

## Troubleshooting

### Server won't start

**Check port availability:**
```bash
lsof -i :8000
```

**Change port:**
```env
# In server/.env
MCP_SERVER_PORT=8080
```

### Authentication fails

**Verify token:**
```bash
# Test with curl
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/health
```

**Check .env file:**
```bash
cat server/.env | grep CWAY_API_TOKEN
```

### CORS errors

Enable CORS for your domain in `rest_api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Import errors

Ensure you're in the virtual environment:
```bash
source venv/bin/activate  # macOS/Linux
pip install -r server/requirements.txt
```

## Production Deployment

### Using Docker

```bash
# Build
docker build -t cway-api server/

# Run
docker run -p 8000:8000 \
  -e CWAY_API_TOKEN=your_token \
  cway-api
```

### Using Uvicorn Directly

```bash
cd server
uvicorn src.presentation.rest_api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Environment Variables

```env
# Required
CWAY_API_TOKEN=your_production_token
CWAY_API_URL=https://app.cway.se/graphql

# Optional
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
DEBUG=false
```

## Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See WARP.md for comprehensive guide
- **Logs**: Check `server/logs/` for detailed error information
