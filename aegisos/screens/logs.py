from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import datetime

class LogsScreen(Screen):
    """Screen for displaying detailed, filterable audit and system logs."""
    
    CSS = """
    LogsScreen {
        background: #0a0a1a;
    }
    
    #logs_screen_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #logs_filter_panel {
        height: 4;
        width: 100%;
        margin-bottom: 1;
    }
    
    #logs_scroll {
        height: 1fr;
        width: 100%;
    }
    """
    
    BINDINGS = [
        ("a", "filter_all", "Show All Logs"),
        ("t", "filter_threats", "Show Threats Only"),
        ("r", "filter_routing", "Show Routing Only"),
    ]
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self.log_filter = "all"  # "all", "threats", "routing"
        self._refresh_timer = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="logs_screen_container"):
            yield Static(id="logs_filter_panel")
            with VerticalScroll(id="logs_scroll"):
                yield Static("Loading system logs...", id="logs_output")
                
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
        self._refresh_timer = self.set_interval(1.5, self.update_display)
        
    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()
            
    def action_filter_all(self) -> None:
        self.log_filter = "all"
        self.app.notify("Filter set to: ALL LOGS", severity="information")
        self.update_display()
        
    def action_filter_threats(self) -> None:
        self.log_filter = "threats"
        self.app.notify("Filter set to: THREATS ONLY", severity="information")
        self.update_display()
        
    def action_filter_routing(self) -> None:
        self.log_filter = "routing"
        self.app.notify("Filter set to: ROUTING DECISIONS ONLY", severity="information")
        self.update_display()

    def update_display(self) -> None:
        """Update display widgets with latest filtered logs."""
        try:
            self._update_filter_panel()
            self._update_logs_list()
        except Exception:
            pass

    def _update_filter_panel(self) -> None:
        """Render top horizontal filters panel."""
        lbl_all = Text("[A] ALL LOGS", style="bold #00ff88" if self.log_filter == "all" else "dim #808090")
        lbl_threats = Text("[T] THREATS ONLY", style="bold #00ff88" if self.log_filter == "threats" else "dim #808090")
        lbl_routing = Text("[R] ROUTING ONLY", style="bold #00ff88" if self.log_filter == "routing" else "dim #808090")
        
        layout = Table.grid(padding=(0, 6))
        layout.add_column()
        layout.add_column()
        layout.add_column()
        layout.add_row(lbl_all, lbl_threats, lbl_routing)
        
        panel = Panel(
            layout,
            title="[bold #00d4ff]LOG AUDIT FILTERS",
            border_style="#1a1a3a",
            padding=(0, 2)
        )
        self.query_one("#logs_filter_panel", Static).update(panel)

    def _update_logs_list(self) -> None:
        """Combine, filter, and render logs in chronological order."""
        log_entries = []
        
        # 1. Gather threat events
        # Treat event format: timestamp, type, severity, agent, status, payload
        if self.log_filter in ("all", "threats"):
            for ev in self.state.events:
                ts = ev.get("timestamp", "N/A")
                sev = ev.get("severity", "LOW")
                etype = ev.get("type", "Threat Detected")
                agent = ev.get("agent", "Agent")
                status = ev.get("status", "DETECTED")
                
                # Format a rich text line
                line = Text()
                line.append(f"[{ts}] ", style="dim #606070")
                line.append("[THREAT] ", style="bold #ff6600")
                
                # Severity and type
                sev_color = "#ff0066" if sev == "CRITICAL" else ("#ff6600" if sev == "HIGH" else "#ffaa00")
                line.append(f"{sev} ", style=f"bold {sev_color}")
                line.append(f"({etype}) on ", style="#c0c0d0")
                line.append(f"{agent} ", style="#00d4ff")
                
                # Action/status
                status_color = "#ff0066" if status == "BLOCKED" else "#00ff88"
                line.append("--> IMMUNE RESPONSE: ", style="dim #808090")
                line.append(status, style=f"bold {status_color}")
                
                log_entries.append((ts, line))
                
        # 2. Gather routing decisions
        # Routing format: timestamp, task, provider, success, latency_ms, tokens, error
        if self.log_filter in ("all", "routing"):
            for r in self.state.routing_history:
                ts = r.get("timestamp", "Now")
                if not ts or ts == "Now":
                    # Fallback timestamp
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    
                task = r.get("task", "classify").upper()
                provider = r.get("provider", "NONE")
                success = r.get("success", False)
                latency = r.get("latency_ms", 0)
                err = r.get("error", "")
                
                line = Text()
                line.append(f"[{ts}] ", style="dim #606070")
                line.append("[ROUTING] ", style="bold #00d4ff")
                
                if success:
                    line.append("SUCCESS: ", style="bold #00ff88")
                    line.append(f"Routed '{task}' task to ", style="#c0c0d0")
                    line.append(f"{provider} ", style="bold #00d4ff")
                    line.append(f"({latency}ms)", style="#ffaa00")
                else:
                    line.append("FAILED: ", style="bold #ff0066")
                    line.append(f"Attempted to route '{task}' to {provider} ", style="#c0c0d0")
                    line.append(f"| Err: {err}", style="dim #ff0066")
                    
                log_entries.append((ts, line))
                
        # Sort logs by timestamp descending (newest at the top)
        log_entries.sort(key=lambda x: x[0], reverse=True)
        
        if not log_entries:
            panel = Panel(
                Text("No log entries match the selected filter.", style="dim italic #505060", justify="center"),
                title="SYSTEM LOG ENTRIES",
                border_style="#1a1a3a",
            )
            self.query_one("#logs_output", Static).update(panel)
            return
            
        from rich.console import Group
        formatted_lines = [x[1] for x in log_entries]
        
        panel = Panel(
            Group(*formatted_lines),
            title=f"AUDIT LOG ENTRIES ({self.log_filter.upper()})",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        self.query_one("#logs_output", Static).update(panel)