# Real-Time Integration Guide

This guide explains how to integrate AegisOS with your actual AI agents for real-time threat monitoring.

## Overview

AegisOS now includes a **ProxyEngine** that acts as an HTTP middleware between your AI agents and LLM providers. It intercepts requests, analyzes them for threats, and either forwards or blocks them based on threat level.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  AI Agent   │─────▶│ AegisOS Proxy│─────▶│ LLM Provider│
│             │      │   (Port 8000)│      │ (OpenAI etc)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │Threat Analysis│
                     │  & Blocking   │
                     └──────────────┘
```

## Quick Start

### 1. Install Additional Dependencies

```bash
pip install fastapi uvicorn
```

### 2. Start the Proxy Server

```bash
python -m aegisos.engine.proxy_server
```

The server will start on `http://localhost:8000`

### 3. Configure Your AI Agents

Point your AI agents to use the AegisOS proxy instead of calling LLM providers directly.

#### Python (OpenAI SDK)

```python
from openai import OpenAI

# Before (direct to OpenAI)
# client = OpenAI(api_key="sk-...")

# After (through AegisOS proxy)
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-...",  # Your actual OpenAI key
    default_headers={
        "X-Agent-ID": "my-agent-001",
        "X-Agent-Name": "Customer Support Bot",
        "X-Agent-Role": "Support",
    }
)

# Use normally - requests are now monitored
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

#### Python (LangChain)

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sk-...",
    model="gpt-4",
    default_headers={
        "X-Agent-ID": "langchain-agent",
        "X-Agent-Name": "Research Assistant",
        "X-Agent-Role": "Research",
    }
)

# Use in your chains - all requests monitored
response = llm.invoke("What is AI safety?")
```

#### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:8000/v1',
  apiKey: 'sk-...',
  defaultHeaders: {
    'X-Agent-ID': 'js-agent-001',
    'X-Agent-Name': 'Web Chatbot',
    'X-Agent-Role': 'Customer Service',
  },
});

// Use normally
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

#### cURL (Testing)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-..." \
  -H "X-Agent-ID: test-agent" \
  -H "X-Agent-Name: Test Agent" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## API Endpoints

### POST /v1/chat/completions

OpenAI-compatible chat endpoint. Intercepts and analyzes requests.

**Headers:**
- `Authorization`: Bearer token for target LLM provider (required)
- `X-Agent-ID`: Unique agent identifier (optional, defaults to "default")
- `X-Agent-Name`: Human-readable agent name (optional)
- `X-Agent-Role`: Agent role/purpose (optional)

**Request Body:** Standard OpenAI chat completion format

**Response:** 
- Success: Standard OpenAI response
- Blocked: 403 with error details

### GET /v1/agents

List all registered agents.

```bash
curl http://localhost:8000/v1/agents
```

### GET /v1/stats

Get proxy statistics.

```bash
curl http://localhost:8000/v1/stats
```

Response:
```json
{
  "total_requests": 150,
  "blocked_requests": 5,
  "active_agents": 3,
  "suspicious_agents": 1,
  "avg_latency_ms": 245
}
```

### GET /v1/threats

List recent threats.

```bash
curl http://localhost:8000/v1/threats?limit=10
```

### POST /v1/agents/register

Register a new agent.

```bash
curl -X POST http://localhost:8000/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "name": "My AI Agent",
    "role": "Assistant"
  }'
```

### GET /health

Health check endpoint.

```bash
curl http://localhost:8000/health
```

## Threat Detection

### Pattern-Based Pre-Screening

The proxy performs quick pattern matching before LLM analysis:

**Suspicious Patterns:**
- "ignore previous instructions"
- "disregard"
- "system prompt"
- "jailbreak"
- "bypass"
- SQL injection attempts
- Code injection attempts

### LLM-Based Analysis

Suspicious inputs are sent to the LLM router for full analysis:
1. **Classification** - Determine threat type and severity
2. **Confidence Scoring** - Calculate confidence level
3. **Recommendation** - Generate mitigation advice

### Blocking Criteria

Requests are blocked if they contain:
- Critical threat patterns
- Multiple suspicious indicators
- Known attack vectors

## Running Both TUI and Proxy

You can run both the terminal UI and proxy server simultaneously:

### Terminal 1: Start Proxy Server
```bash
python -m aegisos.engine.proxy_server
```

### Terminal 2: Start TUI (with Proxy Engine)

Modify `aegisos/main.py` to use ProxyEngine instead of MockEngine:

```python
# In main.py, replace MockEngine with ProxyEngine
from .engine.proxy import ProxyEngine

# In on_mount method:
self.engine = ProxyEngine(
    self.config,
    self.on_threat_event,
    self.on_metrics_update,
)
```

Then run:
```bash
python -m aegisos
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY aegisos/ ./aegisos/
COPY .env .

EXPOSE 8000

CMD ["python", "-m", "aegisos.engine.proxy_server"]
```

Build and run:
```bash
docker build -t aegisos-proxy .
docker run -p 8000:8000 --env-file .env aegisos-proxy
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aegisos-proxy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aegisos-proxy
  template:
    metadata:
      labels:
        app: aegisos-proxy
    spec:
      containers:
      - name: proxy
        image: aegisos-proxy:latest
        ports:
        - containerPort: 8000
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: aegisos-secrets
              key: groq-key
---
apiVersion: v1
kind: Service
metadata:
  name: aegisos-proxy
spec:
  selector:
    app: aegisos-proxy
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Environment Variables

Add to your `.env` file:

```env
# Proxy Configuration
AEGIS_PROXY_HOST=0.0.0.0
AEGIS_PROXY_PORT=8000
AEGIS_PROXY_WORKERS=4

# Security
AEGIS_BLOCK_THRESHOLD=0.8
AEGIS_ANALYSIS_TIMEOUT=5

# Rate Limiting
AEGIS_RATE_LIMIT_PER_AGENT=100
AEGIS_RATE_LIMIT_WINDOW=60
```

## Monitoring

### View Threats in Real-Time

```bash
# Watch threats endpoint
watch -n 1 'curl -s http://localhost:8000/v1/threats?limit=5 | jq'
```

### View Statistics

```bash
# Watch stats
watch -n 2 'curl -s http://localhost:8000/v1/stats | jq'
```

### Logs

The proxy server logs all activity to stdout:

```
[THREAT] HIGH - Prompt Injection from ChatBot
[THREAT] CRITICAL - SQL Injection from DataAgent
[ProxyEngine] Blocked request from agent_003
```

## Advanced Integration

### Custom Threat Handlers

```python
from aegisos.engine.proxy import ProxyEngine

async def custom_threat_handler(event):
    """Custom handler for threat events."""
    if event['severity'] == 'CRITICAL':
        # Send alert to Slack/PagerDuty
        await send_alert(event)
    
    # Log to database
    await db.threats.insert(event)
    
    # Update agent status
    await update_agent_status(event['agent'], 'compromised')

engine = ProxyEngine(config, custom_threat_handler, on_metrics)
```

### Multi-Provider Support

The proxy automatically detects provider from model name:

```python
# Automatically routes to OpenAI
response = client.chat.completions.create(model="gpt-4", ...)

# Automatically routes to Anthropic
response = client.chat.completions.create(model="claude-3", ...)

# Automatically routes to Groq
response = client.chat.completions.create(model="llama-3-70b", ...)
```

## Troubleshooting

### Proxy Not Starting

```bash
# Check if port 8000 is available
lsof -i :8000

# Try different port
python -m aegisos.engine.proxy_server --port 8001
```

### Requests Being Blocked

Check the threat patterns in `proxy.py`:
- Adjust `_quick_threat_check()` sensitivity
- Modify `_should_block()` criteria
- Review blocked requests in `/v1/threats`

### High Latency

- Reduce LLM analysis timeout
- Use faster models (Groq/Cerebras)
- Enable caching for repeated patterns
- Scale horizontally with load balancer

## Next Steps

1. **Test with one agent** - Start small and verify functionality
2. **Monitor metrics** - Watch for false positives/negatives
3. **Tune thresholds** - Adjust blocking criteria based on your use case
4. **Scale up** - Add more agents gradually
5. **Production hardening** - Add authentication, rate limiting, monitoring

## Support

For issues or questions:
- Check logs: `tail -f aegisos.log`
- View threats: `curl http://localhost:8000/v1/threats`
- Check stats: `curl http://localhost:8000/v1/stats`

---
