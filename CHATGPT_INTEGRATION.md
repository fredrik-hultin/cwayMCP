# ChatGPT Integration Guide

There are **two different ways** to integrate Cway with ChatGPT, depending on what you want to achieve:

## Option 1: Custom MCP Connector (Recommended for AI Features)

**Use this for:** Full MCP protocol support with tools, resources, and prompts

### What is it?
ChatGPT's custom MCP connector allows ChatGPT to connect to any MCP server using the standard Model Context Protocol over SSE (Server-Sent Events).

### Setup

1. **Start the MCP SSE server:**
   ```bash
   cd server
   python main.py --mode sse
   # or
   python start_mcp_sse.py
   ```

2. **In ChatGPT, configure the custom MCP connector:**
   - **Name**: Cway
   - **Description**: Connection to the cway server
   - **MCP Server URL**: `http://localhost:8000/sse`
   - **Authentication**: None (or OAuth if you add it)

3. **What ChatGPT can do:**
   - List all projects, users, and system data
   - Get specific projects or users by ID
   - Access KPI dashboards and health scores
   - Monitor temporal metrics and stagnation alerts
   - Use all MCP tools and resources defined in your server

### Architecture
```
ChatGPT ←→ [SSE/HTTP] ←→ MCP Server (SSE Transport) ←→ Cway GraphQL API
```

### Pros
- ✅ Full MCP protocol support
- ✅ All tools and resources available
- ✅ Follows standard MCP specification
- ✅ Works with any MCP-compatible client

### Cons
- ❌ Requires running a server
- ❌ Local only (unless you deploy publicly)

---

## Option 2: GPT Custom Actions (For Sharing)

**Use this for:** Shareable GPTs with custom functionality via REST API

### What is it?
ChatGPT GPT custom actions allow you to create a custom GPT that calls your REST API endpoints. This is **NOT** MCP - it's OpenAPI/REST.

### Setup

1. **Start the REST API server:**
   ```bash
   cd server
   python main.py --mode rest
   # or
   python start_rest_api.py
   ```

2. **Export the OpenAPI specification:**
   ```bash
   cd server
   python scripts/export_openapi.py
   ```

3. **Create a custom GPT:**
   - Go to https://chat.openai.com/gpts/editor
   - Create new GPT
   - Configure basic info (name, description, instructions)

4. **Add Actions:**
   - Go to Actions section
   - Import `server/openapi.json`
   - Configure Bearer authentication with your `CWAY_API_TOKEN`

5. **Example GPT Instructions:**
   ```
   You are a Cway project management assistant.
   
   You can:
   - List and search projects
   - Get project details and status
   - Monitor project health
   - Track stagnation and velocity
   - Find users by email
   
   Always provide actionable insights.
   ```

### Architecture
```
ChatGPT GPT ←→ [REST/HTTPS] ←→ FastAPI Server ←→ Cway GraphQL API
```

### Pros
- ✅ Shareable with team members
- ✅ Works on mobile and web
- ✅ No client software needed
- ✅ Can be made public

### Cons
- ❌ Not MCP protocol (just REST)
- ❌ Limited to predefined endpoints
- ❌ Requires deployed server for sharing

---

## Comparison Table

| Feature | MCP Connector | GPT Actions |
|---------|---------------|-------------|
| **Protocol** | MCP over SSE | REST/OpenAPI |
| **Transport** | Server-Sent Events | HTTP/HTTPS |
| **Auth** | Optional OAuth | Bearer Token |
| **Dynamic Tools** | ✅ Yes | ❌ No |
| **Shareable** | ❌ No | ✅ Yes |
| **Mobile Support** | ❌ No | ✅ Yes |
| **Standard Protocol** | ✅ MCP Spec | ✅ OpenAPI Spec |
| **Setup Complexity** | Medium | Medium |
| **Best For** | Personal use, full features | Team sharing, mobile |

---

## Which Should You Use?

### Use MCP Connector if:
- You want full MCP protocol support
- You're using it personally (not sharing)
- You want dynamic tool discovery
- You want resource providers
- You're on desktop only

### Use GPT Custom Actions if:
- You want to share with team members
- You need mobile access
- You want a public GPT
- You only need specific endpoints
- You're okay with predefined actions

### Use Both if:
- You want personal full MCP access
- AND you want a shareable team GPT
- They can run simultaneously on different ports!

---

## Running Both Simultaneously

You can run both the MCP SSE server and REST API at the same time:

```bash
# Terminal 1: MCP SSE Server (port 8000)
cd server && python main.py --mode sse

# Terminal 2: REST API (port 8001)
cd server && MCP_SERVER_PORT=8001 python main.py --mode rest
```

Then:
- Use `http://localhost:8000/sse` for ChatGPT MCP connector
- Use `http://localhost:8001` for GPT custom actions

---

## Security Considerations

### For MCP Connector (Local Only)
- Runs on localhost by default
- No authentication by default
- Safe for personal use
- Don't expose publicly without adding OAuth

### For GPT Actions (Can Be Public)
- Requires Bearer token authentication
- Should use HTTPS in production
- Can configure CORS restrictions
- Consider rate limiting for public GPTs

---

## Deployment

### Local Development
Both options work great locally with no deployment needed.

### Production Deployment

**For MCP Connector:**
- Deploy to a cloud server (AWS, GCP, Azure)
- Add OAuth authentication
- Use HTTPS
- Consider using ngrok for testing

**For GPT Actions:**
- Deploy REST API to cloud
- Use managed service (Railway, Fly.io, Vercel)
- Configure environment variables
- Update OpenAPI spec with production URL
- Re-import to ChatGPT GPT

---

## Troubleshooting

### MCP Connector Issues

**Connection fails:**
```bash
# Check if server is running
curl http://localhost:8000/sse

# Check logs
tail -f server/logs/mcp_sse.log
```

**Tools not showing up:**
- Verify MCP server is running in SSE mode
- Check that ChatGPT has connected successfully
- Restart the connection in ChatGPT

### GPT Actions Issues

**Authentication fails:**
```bash
# Test authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/projects
```

**Actions not working:**
- Re-export and re-import OpenAPI spec
- Verify token is correct
- Check server logs for errors

---

## Summary

- **MCP Connector** = Full MCP protocol for personal use
- **GPT Actions** = REST API for shareable GPTs
- Both are valid, serve different purposes
- Can run both simultaneously
- Choose based on your needs!
