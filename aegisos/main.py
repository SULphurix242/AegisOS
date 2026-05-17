#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AegisOS - AI Agent Immune System Terminal UI."""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.binding import Binding

from .config import load_config
from .store.state import AppState
from .engine.mock import MockEngine
from .engine.proxy_integration import ProxyIntegration
from .engine.router import LLMRouter
from .llm.analyzer import ThreatAnalyzer
from .widgets import NavPanel, HeaderWidget
from .screens import (
    DashboardScreen,
    ThreatsScreen,
    HelpScreen,
    AgentsScreen,
    ModelsScreen,
    TelemetryScreen,
    SandboxScreen,
    LogsScreen,
    KeysScreen,
    ModelConfigScreen,
)


class AegisApp(App):
    """Main AegisOS application."""
    
    CSS = """
    Screen {
        background: #0a0a1a;
    }
    
    #app_container {
        width: 100%;
        height: 100%;
    }
    
    #nav_container {
        width: 16;
        height: 100%;
    }
    
    #content_container {
        width: 1fr;
        height: 100%;
    }
    """
    
    BINDINGS = [
        Binding("1", "switch_screen('dashboard')", "Dashboard", show=False),
        Binding("2", "switch_screen('threats')", "Threats", show=False),
        Binding("3", "switch_screen('agents')", "Agents", show=False),
        Binding("4", "switch_screen('models')", "Models", show=False),
        Binding("5", "switch_screen('telemetry')", "Telemetry", show=False),
        Binding("6", "switch_screen('sandbox')", "Sandbox", show=False),
        Binding("7", "switch_screen('logs')", "Logs", show=False),
        Binding("8", "switch_screen('keys')", "Keys", show=False),
        Binding("9", "switch_screen('modelcfg')", "ModelCfg", show=False),
        Binding("?", "switch_screen('help')", "Help", show=False),
        Binding("q", "quit", "Quit", show=False),
        Binding("escape", "quit", "Quit", show=False),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("l", "toggle_lockdown", "Lockdown", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.state = AppState()
        self.router = LLMRouter(self.config, self.on_routing_event)
        self.analyzer = ThreatAnalyzer(self.router)
        self.engine = None
        self.proxy_integration = None
        self.current_screen_name = "dashboard"
        self.use_proxy = False  # Flag to determine if using proxy or mock
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="app_container"):
            # Header
            yield HeaderWidget(id="header")
            
            # Main content area
            with Horizontal():
                # Navigation panel
                with Container(id="nav_container"):
                    yield NavPanel(active="DASHBOARD", id="nav")
                
                # Content area (screens will be pushed here)
                with Container(id="content_container"):
                    pass
    
    async def on_mount(self) -> None:
        """Called when app is mounted."""
        # Check if any LLM providers are configured
        if not self.config.has_any_key():
            self.notify(
                "⚠️  No LLM API keys configured. Add keys to .env file.",
                severity="warning",
                timeout=10,
            )
        else:
            providers = ", ".join(self.config.available_providers())
            self.notify(f"✓ LLM providers configured: {providers}", severity="information")
        
        # Try to connect to proxy server first
        try:
            self.proxy_integration = ProxyIntegration(
                proxy_url="http://localhost:8000",
                on_threat=self.on_proxy_threat_event,
                on_metrics=self.on_metrics_update,
                on_agent_update=self.on_agent_update,
            )
            await self.proxy_integration.start()
            
            # Check if proxy is actually running
            health = await self.proxy_integration.get_health()
            if health.get("status") == "healthy":
                self.use_proxy = True
                self.notify("✓ Connected to AegisOS Proxy Server", severity="information")
            else:
                raise Exception("Proxy not healthy")
        except Exception as e:
            # Fall back to mock engine
            self.notify("⚠️  Proxy not available, using mock data", severity="warning")
            self.use_proxy = False
            self.proxy_integration = None
        
        # Start mock engine if not using proxy
        if not self.use_proxy:
            self.engine = MockEngine(
                self.config,
                self.on_threat_event,
                self.on_metrics_update,
            )
            asyncio.create_task(self.engine.start())
        
        # Install screens so they can be switched to without recreating them!
        self.install_screen(DashboardScreen(self.state), "dashboard")
        self.install_screen(ThreatsScreen(self.state), "threats")
        self.install_screen(AgentsScreen(self.state), "agents")
        self.install_screen(ModelsScreen(self.state), "models")
        self.install_screen(TelemetryScreen(self.state), "telemetry")
        self.install_screen(SandboxScreen(self.state), "sandbox")
        self.install_screen(LogsScreen(self.state), "logs")
        self.install_screen(KeysScreen(self.state), "keys")
        self.install_screen(ModelConfigScreen(self.state), "modelcfg")
        self.install_screen(HelpScreen(), "help")
        
        # Push initial screen
        await self.push_screen("dashboard")
        
        # Start global background LLM provider latency polling every 12 seconds
        self.set_interval(12.0, self.check_provider_latencies)
        asyncio.create_task(self._async_check_latencies())
        
        self.notify("AegisOS initialized. Press ? for help.", severity="information")
    
    async def on_threat_event(self, event: dict) -> None:
        """Handle new threat event from mock engine."""
        # Analyze threat with LLM
        analyzed = await self.analyzer.analyze_event(event)
        
        # Add to state
        self.state.add_event(analyzed)
        
        # Update header
        header = self.query_one("#header", HeaderWidget)
        providers_online = len([p for p in self.state.provider_status.values() if p.get("online")])
        header.update_stats(
            self.state.total_threats,
            self.state.in_lockdown,
            providers_online,
            3,
        )
        
        # Log to console
        if hasattr(self.screen, "query_one"):
            try:
                from .widgets import LogViewer
                log = self.screen.query_one(LogViewer)
                log.log_threat(analyzed)
            except:
                pass
        
        # Notify user for critical threats
        if analyzed.get("severity") == "CRITICAL":
            self.notify(
                f"🔴 CRITICAL: {analyzed.get('type')} on {analyzed.get('agent')}",
                severity="error",
                timeout=5,
            )
    
    async def on_proxy_threat_event(self, event: dict) -> None:
        """Handle new threat event from proxy server."""
        # Proxy events are already analyzed, just add to state
        self.state.add_event(event)
        
        # Update header
        header = self.query_one("#header", HeaderWidget)
        providers_online = len([p for p in self.state.provider_status.values() if p.get("online")])
        header.update_stats(
            self.state.total_threats,
            self.state.in_lockdown,
            providers_online,
            3,
        )
        
        # Log to console
        if hasattr(self.screen, "query_one"):
            try:
                from .widgets import LogViewer
                log = self.screen.query_one(LogViewer)
                log.log_threat(event)
            except:
                pass
        
        # Notify user for critical threats
        if event.get("severity") == "CRITICAL":
            self.notify(
                f"🔴 CRITICAL: {event.get('type')} on {event.get('agent')}",
                severity="error",
                timeout=5,
            )
        
        # Refresh dashboard if visible
        if self.current_screen_name == "dashboard" and hasattr(self.screen, "update_display"):
            self.screen.update_display()
    
    def get_current_agents(self) -> list:
        """Get the current list of agents, from proxy or mock engine."""
        if self.use_proxy and self.state.agents_list:
            return self.state.agents_list
        elif self.engine:
            return self.engine.get_agents()
        return []

    async def on_agent_update(self, agents: list) -> None:
        """Handle agent status update from proxy."""
        self.state.agents_list = agents
        # Update agent status widget if visible
        if hasattr(self.screen, "query_one"):
            try:
                from .widgets import AgentStatusWidget
                agent_widget = self.screen.query_one(AgentStatusWidget)
                # Update with real agent data
                agent_widget.update_agents(agents)
            except:
                pass
    
    async def on_routing_event(self, event: dict) -> None:
        """Handle LLM routing event."""
        self.state.add_routing_event(event)
        
        # Log to console
        if hasattr(self.screen, "query_one"):
            try:
                from .widgets import LogViewer
                log = self.screen.query_one(LogViewer)
                log.log_routing(event)
            except:
                pass
    
    async def on_metrics_update(self, metrics: dict) -> None:
        """Handle metrics update from engine."""
        self.state.latest_metrics = metrics
        self.state.metrics_history.appendleft(metrics)
        
        # Update metrics widget if visible
        if hasattr(self.screen, "query_one"):
            try:
                from .widgets import MetricsWidget
                metrics_widget = self.screen.query_one(MetricsWidget)
                metrics_widget.update_metrics(metrics)
            except:
                pass
    
    def action_switch_screen(self, screen_name: str) -> None:
        """Switch to a different screen."""
        self.current_screen_name = screen_name
        
        # Update nav panel
        nav = self.query_one("#nav", NavPanel)
        nav.active = screen_name.upper()
        nav.refresh()
        
        # Switch to the registered screen
        valid_screens = ["dashboard", "threats", "agents", "models", "telemetry", "sandbox", "logs", "keys", "modelcfg", "help"]
        if screen_name in valid_screens:
            self.switch_screen(screen_name)
        else:
            self.notify(f"Screen '{screen_name}' not yet implemented", severity="warning")
    
    def action_refresh(self) -> None:
        """Force refresh current screen."""
        if hasattr(self.screen, "update_display"):
            self.screen.update_display()
        self.notify("Display refreshed", severity="information")
    
    def action_toggle_lockdown(self) -> None:
        """Toggle system lockdown mode."""
        self.state.in_lockdown = not self.state.in_lockdown
        
        # Update header
        header = self.query_one("#header", HeaderWidget)
        providers_online = len([p for p in self.state.provider_status.values() if p.get("online")])
        header.update_stats(
            self.state.total_threats,
            self.state.in_lockdown,
            providers_online,
            3,
        )
        
        if self.state.in_lockdown:
            self.notify("🔒 LOCKDOWN ACTIVATED - All agents blocked", severity="error", timeout=5)
        else:
            self.notify("✓ Lockdown deactivated", severity="information")

    def check_provider_latencies(self) -> None:
        """Trigger global background worker to check live latencies."""
        asyncio.create_task(self._async_check_latencies())

    async def _async_check_latencies(self) -> None:
        """Ping LLM providers globally to measure live latency in a non-blocking task."""
        providers = ["Groq", "Cerebras", "Gemini"]
        tasks = [self.router.test_provider(p) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for p, res in zip(providers, results):
            if isinstance(res, dict) and res.get("success"):
                self.state.provider_status[p] = {
                    "online": True,
                    "latency_ms": res.get("latency_ms", 0),
                    "last_check": __import__("time").monotonic(),
                }
            else:
                is_configured = False
                cfg = self.config
                if p == "Groq" and cfg.groq_key:
                    is_configured = True
                elif p == "Cerebras" and cfg.cerebras_key:
                    is_configured = True
                elif p == "Gemini" and cfg.gemini_key:
                    is_configured = True
                
                if is_configured:
                    self.state.provider_status[p] = {
                        "online": False,
                        "latency_ms": 0,
                        "last_check": __import__("time").monotonic(),
                    }


def run():
    """Entry point for the application."""
    app = AegisApp()
    app.run()


if __name__ == "__main__":
    run()
