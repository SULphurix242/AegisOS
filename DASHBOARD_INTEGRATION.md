# Dashboard Integration Guide

## Overview

The AegisOS dashboard now supports real-time integration with the proxy server, allowing you to monitor actual AI agent activity instead of just mock data.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   AI Agents     │────────▶│  Proxy Server    │◀────────│   Dashboard     │
│  (via OpenAI    │         │  (FastAPI)       │  Polls  │   (Textual UI)  │
│   compatible    │         │  Port 8000       │         │                 │
│   endpoints)    │         └──────────────────┘         └─────────────────┘
└─────────────────┘                  │
                                     │
                              ┌──────▼──────┐
                              │  Threat     │
                              │  Detection  │
                              │  & Analysis │
                              └─────────────┘
```

## Components

### 1. ProxyIntegration (`aegisos/engine/proxy_integration.py`)

Connects the dashboard to the proxy server via HTTP polling:

- **Polls every 2 seconds** for:
  - New threats (`/v1/threats`)
  - Agent updates (`/v1/agents`)
  - Statistics and metrics (`/v1/stats`)

- **Callbacks**:
  - `on_threat`: Called when new threats are detected
  - `on_metrics`: Called with updated system metrics
  - `on_agent_update`: Called when agent list changes

### 2. Main Application (`aegisos/main.py`)

Enhanced with dual-mode operation:

- **Proxy Mode**: Connects to running proxy server at `http://localhost:8000`
- **Mock Mode**: Falls back to mock data if proxy is unavailable

Key features:
- Auto-detects proxy availability on startup
- Handles proxy events and updates dashboard in real-time
- Maintains backward compatibility with mock engine

### 3. Dashboard Screen (`aegisos/screens/dashboard.py`)

Now includes:
- **Auto-refresh**: Updates every 2 seconds
- **Real-time metrics**: CPU, GPU, RAM, VRAM, tokens/sec
- **Live agent status**: Shows actual registered agents
- **Threat statistics**: Total threats, recent events, system status

## Usage

### Running with Proxy Integration

1. **Start the Proxy Server** (in one terminal):
   ```bash
   python -m aegisos.engine.proxy_server
   ```
   
   Or using the installed command:
   ```bash
   aegis-proxy
   ```

2. **Start the Dashboard** (in another terminal):
   ```bash
   python -m aegisos
   ```
   
   Or:
   ```bash
   aegis
   ```

3. **Configure AI Agents** to use the proxy:
   ```python
   from openai import OpenAI
   
   client = OpenAI(
       base_url="http://localhost:8000/v1",
       api_key="your-openai-key"
   )
   
   # Add custom headers for agent identification
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{"role": "user", "content": "Hello!"}],
       extra_headers={
           "X-Agent-ID": "my-agent-1",
           "X-Agent-Name": "Research Assistant",
           "X-Agent-Role": "Information Gathering"
       }
   )
   ```

### Running with Mock Data (Fallback)

If the proxy server is not running, the dashboard automatically falls back to mock mode:

```bash
python -m aegisos
```

You'll see: `⚠️ Proxy not available, using mock data`

## API Endpoints

The proxy server exposes these endpoints that the dashboard polls:

### GET `/v1/threats?limit=50`
Returns recent threat events:
```json
{
  "threats": [
    {
      "id": "threat-123",
      "type": "prompt_injection",
      "severity": "HIGH",
      "agent": "agent-1",
      "timestamp": "2024-01-15T10:30:00Z",
      "details": "..."
    }
  ],
  "total": 42
}
```

### GET `/v1/agents`
Returns registered agents:
```json
{
  "agents": [
    {
      "id": "agent-1",
      "name": "Research Assistant",
      "role": "Information Gathering",
      "status": "active",
      "threat_count": 2
    }
  ],
  "total": 3
}
```

### GET `/v1/stats`
Returns proxy statistics and metrics:
```json
{
  "total_requests": 150,
  "blocked_requests": 5,
  "agents_count": 3,
  "metrics": {
    "cpu": 45.2,
    "gpu": 78.5,
    "ram": 62.1,
    "vram": 85.3,
    "tokens_sec": 125
  }
}
```

### GET `/health`
Health check endpoint:
```json
{
  "status": "healthy",
  "proxy_running": true,
  "agents_registered": 3
}
```

## Dashboard Features

### Real-Time Updates

The dashboard automatically updates every 2 seconds with:

1. **Metrics Panel**: System resource usage
   - CPU, GPU, RAM, VRAM percentages
   - Tokens per second throughput

2. **Agent Status Panel**: Live agent monitoring
   - Agent name and role
   - Current status (ACTIVE, IDLE, SUSPICIOUS, COMPROMISED)
   - Threat count per agent

3. **System Overview Panel**: Statistics
   - Total threats detected
   - Recent events (last 10 minutes)
   - System status (OPERATIONAL/LOCKDOWN)
   - Routing mode

4. **Log Viewer**: Real-time event stream
   - Threat detections with severity
   - LLM routing events
   - System messages

### Notifications

Critical events trigger notifications:
- 🔴 **CRITICAL threats**: Red alert with 5-second timeout
- ⚠️ **Connection issues**: Warning when proxy disconnects
- ✓ **Status updates**: Info messages for system changes

## Configuration

### Environment Variables

Create a `.env` file with your LLM API keys:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Groq
GROQ_API_KEY=gsk_...

# Google Gemini
GOOGLE_API_KEY=AI...

# Cerebras
CEREBRAS_API_KEY=csk-...
```

### Proxy Server Settings

Edit `aegisos/engine/proxy_server.py` to customize:

```python
# Change host/port
run_server(host="0.0.0.0", port=8000)

# Adjust polling interval in proxy_integration.py
await asyncio.sleep(2.0)  # Poll every 2 seconds
```

## Troubleshooting

### Dashboard shows "No agents detected"

**Cause**: No AI agents have made requests through the proxy yet.

**Solution**: 
1. Ensure proxy server is running
2. Configure your AI agents to use `http://localhost:8000/v1` as base URL
3. Make a test request

### "Proxy not available" warning

**Cause**: Proxy server is not running or not accessible.

**Solution**:
1. Start the proxy server: `python -m aegisos.engine.proxy_server`
2. Check if port 8000 is available
3. Verify no firewall is blocking localhost:8000

### Metrics not updating

**Cause**: Proxy server not sending metrics data.

**Solution**:
1. Check proxy server logs for errors
2. Verify `/v1/stats` endpoint returns metrics
3. Restart both proxy and dashboard

### High CPU usage

**Cause**: Polling interval too aggressive or too many agents.

**Solution**:
1. Increase polling interval in `proxy_integration.py`
2. Reduce auto-refresh frequency in `dashboard.py`
3. Limit number of threats stored (adjust `maxlen` in `AppState`)

## Performance Considerations

- **Polling Interval**: 2 seconds balances responsiveness and resource usage
- **Event History**: Limited to 200 threats, 60 metrics samples, 100 routing events
- **Auto-refresh**: Dashboard updates every 2 seconds
- **Memory Usage**: Bounded by deque maxlen settings

## Security Notes

⚠️ **Important**: The proxy server currently runs without authentication. For production use:

1. Add API key authentication
2. Use HTTPS/TLS encryption
3. Implement rate limiting
4. Add request validation
5. Enable CORS only for trusted origins

## Next Steps

1. **Add Authentication**: Implement API key validation
2. **WebSocket Support**: Replace polling with WebSocket for real-time updates
3. **Persistent Storage**: Save threat history to database
4. **Alert System**: Email/Slack notifications for critical threats
5. **Multi-Proxy Support**: Connect to multiple proxy instances
