from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class ModelsScreen(Screen):
    """Screen for monitoring LLM providers and routing logic."""
    
    CSS = """
    ModelsScreen {
        background: #0a0a1a;
    }
    
    #models_screen_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #top_row {
        height: 10;
        width: 100%;
        margin-bottom: 1;
    }
    
    #routing_panel_container {
        width: 40%;
        height: 100%;
    }
    
    #providers_panel_container {
        width: 60%;
        height: 100%;
    }
    
    #history_panel_container {
        height: 1fr;
        width: 100%;
    }
    """
    
    BINDINGS = [
        ("m", "cycle_mode", "Cycle Routing Mode"),
    ]
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self._refresh_timer = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="models_screen_container"):
            with Horizontal(id="top_row"):
                with Container(id="routing_panel_container"):
                    yield Static(id="routing_mode_panel")
                with Container(id="providers_panel_container"):
                    yield Static(id="providers_status_panel")
            
            with Container(id="history_panel_container"):
                yield Static(id="routing_history_panel")
                
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
        # Set periodic refresh
        self._refresh_timer = self.set_interval(1.5, self.update_display)
        # Periodically check LLM provider latencies in background every 8 seconds
        self._latency_timer = self.set_interval(8.0, self.check_provider_latencies)
        # Trigger immediate check on mount
        self.check_provider_latencies()
        
    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()
        if hasattr(self, "_latency_timer") and self._latency_timer:
            self._latency_timer.stop()

    def check_provider_latencies(self) -> None:
        """Trigger background worker to check live latencies."""
        self.run_worker(self._async_check_latencies())

    async def _async_check_latencies(self) -> None:
        """Ping LLM providers to measure live latency in a non-blocking background thread."""
        import asyncio
        providers = ["Groq", "Cerebras", "Gemini"]
        tasks = [self.app.router.test_provider(p) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for p, res in zip(providers, results):
            if isinstance(res, dict) and res.get("success"):
                self.state.provider_status[p] = {
                    "online": True,
                    "latency_ms": res.get("latency_ms", 0),
                    "last_check": __import__("time").monotonic(),
                }
            else:
                # If configured but failed, mark offline. If not configured, leave as ○ NOT CONFIG.
                is_configured = False
                cfg = self.app.config
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
            
    def action_cycle_mode(self) -> None:
        """Cycle through the routing modes."""
        modes = ["balanced", "cheapest", "fastest", "smartest"]
        current = self.state.route_mode
        try:
            next_idx = (modes.index(current) + 1) % len(modes)
        except ValueError:
            next_idx = 0
            
        next_mode = modes[next_idx]
        self.state.route_mode = next_mode
        
        # Proactively update proxy server config if proxy server is active
        # (This is local to the session, but we can also notify)
        self.app.notify(f"Routing Mode updated to: {next_mode.upper()}", severity="information")
        self.update_display()

    def update_display(self) -> None:
        """Update display widgets with latest data."""
        try:
            self._update_routing_panel()
            self._update_providers_panel()
            self._update_history_panel()
        except Exception:
            pass

    def _update_routing_panel(self) -> None:
        """Render the routing mode panel."""
        mode = self.state.route_mode.upper()
        
        content = []
        content.append(Text.assemble(("Current Mode: ", "dim #808090"), (f"{mode}", "bold #00ff88")))
        content.append(Text())
        content.append(Text("Press [M] to cycle routing mode", style="italic dim #505060"))
        
        # Add visual description of active mode
        desc = ""
        if mode == "BALANCED":
            desc = "Balances query speed, api cost, and threat detection accuracy."
        elif mode == "CHEAPEST":
            desc = "Prioritizes Groq & Cerebras Llama-3 models to minimize API tokens cost."
        elif mode == "FASTEST":
            desc = "Routes prompts dynamically to the provider with the lowest measured latency."
        elif mode == "SMARTEST":
            desc = "Routes to the highest-reasoning models (Gemini-1.5-flash / Gemini-Pro)."
            
        content.append(Text(desc, style="#808090"))
        
        from rich.console import Group
        panel = Panel(
            Group(*content),
            title="[bold #00d4ff]INTELLIGENT AI ROUTER",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        self.query_one("#routing_mode_panel", Static).update(panel)

    def _update_providers_panel(self) -> None:
        """Render the providers status panel."""
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", width=15)
        table.add_column(justify="left", width=12)
        table.add_column(justify="right", width=15)
        table.add_column(justify="left")
        
        # Headers
        table.add_row(
            Text("PROVIDER", style="bold #808090"),
            Text("STATUS", style="bold #808090"),
            Text("LATENCY", style="bold #808090"),
            Text("BASE MODEL USED", style="bold #808090")
        )
        table.add_row(
            Text("─" * 12, style="dim #303040"),
            Text("─" * 10, style="dim #303040"),
            Text("─" * 12, style="dim #303040"),
            Text("─" * 22, style="dim #303040")
        )
        
        # Get active model names from config dynamically
        groq_model = "llama3-70b-8192"
        cerebras_model = "llama3.1-70b"
        gemini_model = "gemini-1.5-flash"
        
        if hasattr(self.app, "config"):
            groq_model = self.app.config.groq_model or groq_model
            cerebras_model = self.app.config.cerebras_model or cerebras_model
            gemini_model = self.app.config.gemini_model or gemini_model
            
        providers = [
            ("Groq", groq_model),
            ("Cerebras", cerebras_model),
            ("Gemini", gemini_model)
        ]
        
        for name, def_model in providers:
            # Check status from state
            status_info = self.state.provider_status.get(name, {})
            is_configured = False
            
            # Check config to see if key is configured
            if hasattr(self.app, "config"):
                cfg = self.app.config
                if name == "Groq" and cfg.groq_key:
                    is_configured = True
                elif name == "Cerebras" and cfg.cerebras_key:
                    is_configured = True
                elif name == "Gemini" and cfg.gemini_key:
                    is_configured = True
            else:
                is_configured = bool(status_info.get("online"))
                
            status_text = Text()
            latency_text = Text()
            
            if not is_configured:
                status_text.append("○ NOT CONFIG", style="dim #505060")
                latency_text.append("N/A", style="dim #505060")
            elif status_info.get("online", True):
                status_text.append("✓ ONLINE", style="bold #00ff88")
                lat = status_info.get("latency_ms", 0)
                if lat > 0:
                    latency_text.append(f"{lat} ms", style="#ffaa00")
                else:
                    latency_text.append("Active", style="#00ff88")
            else:
                status_text.append("🔴 OFFLINE", style="bold #ff0066")
                latency_text.append("Timeout", style="bold #ff0066")
                
            table.add_row(
                Text(name, style="#00d4ff"),
                status_text,
                latency_text,
                Text(def_model, style="#808090")
            )
            
        panel = Panel(
            table,
            title="[bold #00d4ff]LLM APIS GATEWAYS",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        self.query_one("#providers_status_panel", Static).update(panel)

    def _update_history_panel(self) -> None:
        """Render the recent routing decision history."""
        table = Table(title="[bold #00d4ff]REAL-TIME ROUTING & CONSENSUS DECISIONS HISTORY", title_justify="left", expand=True, border_style="#1a1a3a")
        table.add_column("TIMESTAMP", style="dim #808090", width=12)
        table.add_column("TASK", style="#00d4ff", width=12)
        table.add_column("ROUTED TO", style="bold #c0c0d0", width=12)
        table.add_column("STATUS", width=12)
        table.add_column("LATENCY", justify="right", style="#ffaa00", width=12)
        table.add_column("TOKENS USED", justify="right", style="#00ff88", width=12)
        table.add_column("ERROR/MESSAGE", style="#808090", ratio=1)
        
        # Get routing events from state
        events = list(self.state.routing_history)[:12]
        
        if not events:
            table.add_row("", "No decisions logged yet.", "", "", "", "", "")
        else:
            for ev in events:
                timestamp = ev.get("timestamp", "Now")
                if not timestamp or timestamp == "Now":
                    # Fallback timestamp if not present
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    
                task = ev.get("task", "classify").upper()
                provider = ev.get("provider", "NONE")
                success = ev.get("success", False)
                latency = ev.get("latency_ms", 0)
                tokens = ev.get("tokens", 0)
                error_msg = ev.get("error", "")
                
                status_text = Text("SUCCESS", style="bold #00ff88") if success else Text("FAILED", style="bold #ff0066")
                latency_str = f"{latency} ms" if latency > 0 else "N/A"
                tokens_str = str(tokens) if tokens > 0 else "N/A"
                
                table.add_row(
                    timestamp,
                    task,
                    provider,
                    status_text,
                    latency_str,
                    tokens_str,
                    error_msg or "OK"
                )
                
        self.query_one("#routing_history_panel", Static).update(table)