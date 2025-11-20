# ⚡ ChatGPT Desktop - Quick Start

## 🎯 3-Step Setup

### Step 1: Prepare Environment
```bash
cd /Users/fredrik.hultin/Developer/cwayMCP

# Create virtual environment if needed
python -m venv venv
source venv/bin/activate

# Install dependencies
cd server && pip install -r requirements.txt && cd ..

# Configure API token
cp .env.example server/.env
# Edit server/.env and add: CWAY_API_TOKEN=your_token_here
```

### Step 2: Test Server
```bash
# Test the server starts correctly
./start-mcp.sh

# You should see: "Starting Cway MCP Server..."
# Press Ctrl+C to stop
```

### Step 3: Register with ChatGPT
```bash
# Run registration script
./register-chatgpt-mcp.sh

# Restart ChatGPT Desktop App
```

## ✅ Verify It Works

1. Open ChatGPT Desktop App
2. Go to **Settings → Features → Model Context Protocol**
3. Check that "cway" server is listed and enabled
4. Try this prompt: **"Show me all active Cway projects"**

## 🧪 Example Prompts

- "Show me all active Cway projects"
- "What are the critical projects that need attention?"
- "Find user by email: user@example.com"
- "Show me the temporal KPI dashboard"
- "What projects are at risk of stagnation?"
- "Analyze velocity for project ID: [project-id]"

## 🔧 Troubleshooting

**Server won't start?**
```bash
# Check virtual environment
ls venv/bin/python

# Check .env file exists and has token
cat server/.env | grep CWAY_API_TOKEN
```

**ChatGPT can't connect?**
```bash
# Verify paths are correct
cat ~/Library/Application\ Support/ChatGPT/mcp_settings.json

# Re-run registration
./register-chatgpt-mcp.sh
```

**API errors?**
```bash
# Test API connection
source venv/bin/activate
cd server
python -c "from config.settings import settings; print(f'Token configured: {bool(settings.cway_api_token)}')"
```

## 📚 Full Documentation

- **Complete Guide:** [CHATGPT_SETUP.md](CHATGPT_SETUP.md)
- **Remove Dashboard:** [REMOVE_CLIENT.md](REMOVE_CLIENT.md)
- **Project README:** [README.md](README.md)

## 🎓 Key Points

✅ **Server Mode:** Uses stdio (standard input/output)
✅ **Dashboard:** Optional - not needed for ChatGPT Desktop
✅ **Configuration:** All settings in `server/.env`
✅ **Logging:** Check `server/logs/mcp_server.log` for issues
