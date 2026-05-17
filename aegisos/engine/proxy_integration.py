"""
Integration module for connecting ProxyEngine with AegisOS Dashboard.

This module provides a bridge between the proxy server and the Textual UI,
enabling real-time updates of agent activity, threats, and metrics.
"""

import asyncio
import httpx
from typing import Optional, Callable, Dict, Any
from datetime import datetime


class ProxyIntegration:
    """
    Connects to a running proxy server and streams data to the dashboard.
    
    This allows the dashboard to display real-time information about:
    - Registered AI agents
    - Detected threats
    - Proxy statistics
    - System health
    """
    
    def __init__(
        self,
        proxy_url: str = "http://localhost:8000",
        on_threat: Optional[Callable] = None,
        on_metrics: Optional[Callable] = None,
        on_agent_update: Optional[Callable] = None,
    ):
        """
        Initialize proxy integration.
        
        Args:
            proxy_url: Base URL of the proxy server
            on_threat: Callback for threat events
            on_metrics: Callback for metrics updates
            on_agent_update: Callback for agent status updates
        """
        self.proxy_url = proxy_url.rstrip("/")
        self.on_threat = on_threat
        self.on_metrics = on_metrics
        self.on_agent_update = on_agent_update
        
        self.running = False
        self.client: Optional[httpx.AsyncClient] = None
        self._poll_task: Optional[asyncio.Task] = None
        
        # Cache for tracking changes
        self._last_threat_count = 0
        self._last_agent_count = 0
    
    async def start(self):
        """Start the integration and begin polling."""
        if self.running:
            return
        
        self.running = True
        self.client = httpx.AsyncClient(timeout=10.0)
        
        # Check if proxy is available
        try:
            response = await self.client.get(f"{self.proxy_url}/health")
            if response.status_code == 200:
                print(f"[ProxyIntegration] Connected to proxy at {self.proxy_url}")
            else:
                print(f"[ProxyIntegration] Warning: Proxy returned status {response.status_code}")
        except Exception as e:
            print(f"[ProxyIntegration] Warning: Could not connect to proxy: {e}")
            print("[ProxyIntegration] Will continue trying to connect...")
        
        # Start polling task
        self._poll_task = asyncio.create_task(self._poll_loop())
    
    async def stop(self):
        """Stop the integration."""
        self.running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.aclose()
    
    async def _poll_loop(self):
        """Main polling loop to fetch updates from proxy."""
        while self.running:
            try:
                # Poll for threats
                await self._poll_threats()
                
                # Poll for agents
                await self._poll_agents()
                
                # Poll for stats (includes metrics)
                await self._poll_stats()
                
                # Wait before next poll
                await asyncio.sleep(2.0)  # Poll every 2 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Don't crash on errors, just log and continue
                print(f"[ProxyIntegration] Poll error: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def _poll_threats(self):
        """Poll for new threats."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/threats?limit=50")
            if response.status_code == 200:
                data = response.json()
                threats = data.get("threats", [])
                total = data.get("total", 0)
                
                # Check if there are new threats
                if total > self._last_threat_count:
                    # Get only the new threats
                    new_count = total - self._last_threat_count
                    new_threats = threats[:new_count]
                    
                    # Call callback for each new threat
                    if self.on_threat:
                        for threat in reversed(new_threats):  # Process oldest first
                            await self.on_threat(threat)
                    
                    self._last_threat_count = total
        except Exception as e:
            # Silently ignore connection errors during polling
            pass
    
    async def _poll_agents(self):
        """Poll for agent updates."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/agents")
            if response.status_code == 200:
                data = response.json()
                agents = data.get("agents", [])
                total = data.get("total", 0)
                
                # Always update agents (not just when count changes)
                # This ensures status changes are reflected
                if self.on_agent_update:
                    await self.on_agent_update(agents)
                self._last_agent_count = total
        except Exception as e:
            pass
    
    async def _poll_stats(self):
        """Poll for proxy statistics and metrics."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Extract metrics if available
                if self.on_metrics and "metrics" in stats:
                    await self.on_metrics(stats["metrics"])
        except Exception as e:
            pass
    
    async def get_health(self) -> Dict[str, Any]:
        """Get proxy health status."""
        try:
            response = await self.client.get(f"{self.proxy_url}/health")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
        
        return {"status": "unknown"}
    
    async def get_agents(self) -> list:
        """Get list of registered agents."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/agents")
            if response.status_code == 200:
                data = response.json()
                return data.get("agents", [])
        except Exception:
            return []
    
    async def get_threats(self, limit: int = 50) -> list:
        """Get recent threats."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/threats?limit={limit}")
            if response.status_code == 200:
                data = response.json()
                return data.get("threats", [])
        except Exception:
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get proxy statistics."""
        try:
            response = await self.client.get(f"{self.proxy_url}/v1/stats")
            if response.status_code == 200:
                return response.json()
        except Exception:
            return {}

