"""
FastAPI HTTP Server for AegisOS Proxy

This server exposes the ProxyEngine as an HTTP API that AI agents can call.
It provides OpenAI-compatible endpoints for easy integration.

Usage:
    python -m aegisos.engine.proxy_server
    
Then configure your AI agents to use:
    base_url = "http://localhost:8000/v1"
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import asyncio
import uvicorn
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config
from engine.proxy import ProxyEngine
from store.state import AppState

# Create FastAPI app
app = FastAPI(
    title="AegisOS Proxy API",
    description="AI Agent Security Proxy with Real-Time Threat Detection",
    version="1.0.0",
)

# Global state
proxy_engine: Optional[ProxyEngine] = None
app_state: Optional[AppState] = None


@app.on_event("startup")
async def startup_event():
    """Initialize proxy engine on startup."""
    global proxy_engine, app_state
    
    print("[AegisOS Proxy] Starting up...")
    
    # Load config
    config = load_config()
    
    # Create state
    app_state = AppState()
    
    # Create proxy engine
    async def on_threat(event):
        app_state.add_event(event)
        print(f"[THREAT] {event['severity']} - {event['type']} from {event['agent']}")
    
    async def on_metrics(metrics):
        app_state.latest_metrics = metrics
    
    proxy_engine = ProxyEngine(config, on_threat, on_metrics)
    
    # Register some example agents (in production, agents would register themselves)
    proxy_engine.register_agent("default", {"name": "Default Agent", "role": "General"})
    
    # Start engine
    await proxy_engine.start()
    
    print("[AegisOS Proxy] Ready to intercept requests")
    print("[AegisOS Proxy] Listening on http://localhost:8000")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global proxy_engine
    if proxy_engine:
        await proxy_engine.stop()
    print("[AegisOS Proxy] Shut down")


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    x_agent_id: Optional[str] = Header(None),
    x_agent_name: Optional[str] = Header(None),
    x_agent_role: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    """
    OpenAI-compatible chat completions endpoint.
    
    Headers:
        X-Agent-ID: Unique agent identifier (optional, defaults to 'default')
        X-Agent-Name: Human-readable agent name (optional)
        X-Agent-Role: Agent role/purpose (optional)
        Authorization: Bearer token for target LLM provider
    """
    if not proxy_engine:
        raise HTTPException(status_code=503, detail="Proxy engine not initialized")
    
    # Get request body
    body = await request.json()
    
    # Extract agent info
    agent_id = x_agent_id or "default"
    
    # Register agent if new
    if agent_id not in proxy_engine.agents:
        proxy_engine.register_agent(agent_id, {
            "name": x_agent_name or agent_id,
            "role": x_agent_role or "Unknown",
        })
    
    # Determine provider from model
    model = body.get("model", "")
    model_lower = model.lower()
    
    # Detect provider based on model name
    if "llama" in model_lower or "mixtral" in model_lower:
        provider = "groq"
    elif "gpt-oss" in model_lower or "cerebras" in model_lower:
        provider = "cerebras"
    elif "gemini" in model_lower:
        provider = "gemini"
    elif "gpt" in model_lower:
        provider = "openai"
    elif "claude" in model_lower:
        provider = "anthropic"
    else:
        provider = "groq"  # Default to Groq
    
    # Prepare headers for forwarding
    forward_headers = {}
    if authorization:
        forward_headers["Authorization"] = authorization
    
    # Intercept and analyze request
    result = await proxy_engine.intercept_request(
        agent_id=agent_id,
        provider=provider,
        request_data=body,
        headers=forward_headers,
    )
    
    # Return response or error
    if result.get("blocked"):
        return JSONResponse(
            status_code=403,
            content=result["error"],
        )
    
    if "error" in result:
        return JSONResponse(
            status_code=500,
            content=result["error"],
        )
    
    return result["response"]


@app.get("/v1/agents")
async def list_agents():
    """List all registered agents."""
    if not proxy_engine:
        raise HTTPException(status_code=503, detail="Proxy engine not initialized")
    
    return {
        "agents": proxy_engine.get_agents(),
        "total": len(proxy_engine.agents),
    }


@app.get("/v1/stats")
async def get_stats():
    """Get proxy statistics."""
    if not proxy_engine:
        raise HTTPException(status_code=503, detail="Proxy engine not initialized")
    
    stats = proxy_engine.get_stats()
    
    # Add current metrics if available
    if app_state and app_state.latest_metrics:
        stats["metrics"] = app_state.latest_metrics
    
    return stats


@app.get("/v1/threats")
async def list_threats(limit: int = 50):
    """List recent threats."""
    if not app_state:
        raise HTTPException(status_code=503, detail="State not initialized")
    
    return {
        "threats": list(app_state.events)[:limit],
        "total": app_state.total_threats,
    }


@app.post("/v1/agents/register")
async def register_agent(
    agent_id: str,
    name: str,
    role: str = "Unknown",
):
    """Register a new agent for monitoring."""
    if not proxy_engine:
        raise HTTPException(status_code=503, detail="Proxy engine not initialized")
    
    proxy_engine.register_agent(agent_id, {"name": name, "role": role})
    
    return {
        "success": True,
        "agent_id": agent_id,
        "message": f"Agent '{name}' registered successfully",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "proxy_running": proxy_engine is not None and proxy_engine.running,
        "agents_registered": len(proxy_engine.agents) if proxy_engine else 0,
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the proxy server."""
    print(f"""
+-----------------------------------------------------------+
|                    AegisOS Proxy Server                   |
|                                                           |
|  AI Agent Security Proxy with Real-Time Threat Detection  |
+-----------------------------------------------------------+

Starting server on {host}:{port}

Configure your AI agents to use:
  base_url = "http://localhost:{port}/v1"

Example (Python):
  from openai import OpenAI
  client = OpenAI(
      base_url="http://localhost:{port}/v1",
      api_key="your-openai-key"
  )

Endpoints:
  POST /v1/chat/completions  - OpenAI-compatible chat endpoint
  GET  /v1/agents            - List registered agents
  GET  /v1/stats             - Get proxy statistics
  GET  /v1/threats           - List detected threats
  POST /v1/agents/register   - Register new agent
  GET  /health               - Health check

Press Ctrl+C to stop
""")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
