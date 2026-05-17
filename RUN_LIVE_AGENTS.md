# Running AegisOS Live with Real Agents

This guide shows you how to run AegisOS with your actual AI agents using Groq, Cerebras, and Google Gemini.

## Prerequisites

✅ You have API keys for:
- Groq (llama-3.3-70b-versatile)
- Cerebras (gpt-oss-120b)
- Google AI Studio / Gemini (gemini-1.5-flash)

## Step 1: Configure Your API Keys

Your `.env` file should have your actual API keys:

```env
# LLM Provider API Keys
GROQ_API_KEY=gsk_your_actual_groq_key_here
CEREBRAS_API_KEY=your_actual_cerebras_key_here
GEMINI_API_KEY=AIza_your_actual_gemini_key_here

# Model Selection (correct models for your keys)
GROQ_MODEL=llama-3.3-70b-versatile
CEREBRAS_MODEL=gpt-oss-120b
GEMINI_MODEL=gemini-1.5-flash

# Routing Strategy
AEGIS_ROUTE_MODE=balanced
```

## Step 2: Start the AegisOS Proxy Server

Open a new terminal and run:

```powershell
python -m aegisos.engine.proxy_server
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal running!** This is your security proxy that monitors all AI agent requests.

## Step 3: Test Individual Providers

### Test Groq Agent

```powershell
python test_groq_agent.py
```

This will:
- ✅ Send a safe request (should succeed)
- ✅ Send a malicious request (should be blocked)

### Test Cerebras Agent

```powershell
python test_cerebras_agent.py
```

### Test Google Gemini Agent

```powershell
python test_gemini_agent.py
```

## Step 4: Run Comprehensive Test

Test all three providers at once:

```powershell
python test_all_agents.py
```

This will:
1. Check if proxy is running
2. Test each provider (safe + malicious requests)
3. Show detailed results
4. Display proxy statistics

## Step 5: Monitor Real-Time Threats

### Option A: Use the Terminal UI

In Terminal 2 (already running):
- Press `2` to view threats
- Press `3` to view agents
- Press `5` to view telemetry
- Press `?` for help

### Option B: Use PowerShell Commands

**View recent threats:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/threats?limit=10"
```

**View statistics:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/stats"
```

**View registered agents:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/agents"
```

## Step 6: Integrate Your Own Agents

Now that the proxy is working, configure your actual AI agents to use it:

### Python Example

```python
import httpx

# Your agent makes requests through AegisOS
response = httpx.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer your-api-key",
        "X-Agent-ID": "my-agent-001",
        "X-Agent-Name": "My Custom Agent",
        "X-Agent-Role": "Assistant",
        "Content-Type": "application/json",
    },
    json={
        "model": "llama-3.3-70b-versatile",  # or gpt-oss-120b or gemini-1.5-flash
        "messages": [
            {"role": "user", "content": "Your prompt here"}
        ]
    }
)

print(response.json())
```

### Using Groq SDK

```python
from groq import Groq

client = Groq(
    base_url="http://localhost:8000/v1",
    api_key="your-groq-key",
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## What Happens When a Threat is Detected?

1. **Request Intercepted**: AegisOS proxy receives the request
2. **Pattern Analysis**: Quick check for suspicious patterns
3. **LLM Analysis**: Full threat analysis using your configured LLMs
4. **Decision**: Block (403) or Forward to provider
5. **Logging**: Threat logged and visible in TUI/API

### Example Blocked Response

```json
{
  "error": {
    "message": "Request blocked: Prompt Injection detected",
    "type": "security_violation",
    "code": "threat_detected"
  }
}
```

## Troubleshooting

### "Cannot connect to proxy"
- Make sure proxy server is running: `python -m aegisos.engine.proxy_server`
- Check if port 8000 is available

### "API key not configured"
- Verify your `.env` file has actual API keys (not placeholder values)
- Make sure there are no extra spaces in the keys

### "All LLM providers failed"
- Check your API keys are valid
- Verify you have internet connection
- Check API quotas aren't exceeded

### Requests not being blocked
- Check the threat patterns in the proxy logs
- Try more obvious malicious patterns
- Verify LLM analysis is working (check logs)

## Architecture

```
┌─────────────────┐
│  Your AI Agent  │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  AegisOS Proxy  │ ← Analyzes with Groq/Cerebras/Gemini
│  (Port 8000)    │
└────────┬────────┘
         │ Safe requests only
         ▼
┌─────────────────┐
│  LLM Provider   │
│ (Groq/Cerebras/ │
│    Gemini)      │
└─────────────────┘
```

## Next Steps

1. ✅ Run `python test_all_agents.py` to verify everything works
2. ✅ Monitor threats in the Terminal UI (Terminal 2)
3. ✅ Integrate your actual AI agents to use the proxy
4. ✅ Watch real-time threat detection in action!

## Files Created

- `test_groq_agent.py` - Test Groq integration
- `test_cerebras_agent.py` - Test Cerebras integration
- `test_gemini_agent.py` - Test Gemini integration
- `test_all_agents.py` - Comprehensive test runner
- `RUN_LIVE_AGENTS.md` - This guide

## Support

For issues:
- Check proxy logs in Terminal 1
- View threats: `Invoke-RestMethod -Uri "http://localhost:8000/v1/threats"`
- Check stats: `Invoke-RestMethod -Uri "http://localhost:8000/v1/stats"`

---
