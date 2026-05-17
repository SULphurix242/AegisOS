from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static
import asyncio
from ..widgets import HeaderWidget, MetricsWidget, AgentStatusWidget, LogViewer

class DashboardScreen(Screen):
    """Main dashboard showing overview of system status."""
    
    CSS = """
    DashboardScreen {
        background: #0a0a1a;
    }
    
    #main_container {
        height: 100%;
        width: 100%;
    }
    
    #left_panel {
        width: 60%;
        height: 100%;
    }
    
    #right_panel {
        width: 40%;
        height: 100%;
    }
    
    #metrics_container {
        height: 10;
        margin: 1 0;
    }
    
    #agents_container {
        height: 15;
        margin: 1 0;
    }
    
    #log_container {
        height: 1fr;
        margin: 1 0;
    }
    
    #stats_panel {
        height: 100%;
        padding: 1;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self._refresh_task = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="main_container"):
            with Horizontal():
                # Left panel: Metrics, Agents, Logs
                with Vertical(id="left_panel"):
                    with Container(id="metrics_container"):
                        yield MetricsWidget(id="metrics")
                    
                    with Container(id="agents_container"):
                        yield AgentStatusWidget(id="agents")
                    
                    with Container(id="log_container"):
                        yield LogViewer(id="logs")
                
                # Right panel: Statistics and recent threats
                with Vertical(id="right_panel"):
                    yield Static(self._render_stats(), id="stats_panel")
    
    def _render_stats(self) -> str:
        """Render statistics panel."""
        from rich.panel import Panel
        from rich.text import Text
        from rich.table import Table
        
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left")
        table.add_column(justify="right")
        
        # Total threats
        row1 = Text()
        row1.append("Total Threats Detected", style="#808090")
        count = Text(str(self.state.total_threats), style="bold #ff6600")
        table.add_row(row1, count)
        
        # Recent events
        recent = len(self.state.get_recent_events(10))
        row2 = Text()
        row2.append("Recent Events (10m)", style="#808090")
        recent_count = Text(str(recent), style="bold #00d4ff")
        table.add_row(row2, recent_count)
        
        # Lockdown status
        row3 = Text()
        row3.append("System Status", style="#808090")
        if self.state.in_lockdown:
            status = Text("LOCKDOWN", style="bold #ff0066")
        else:
            status = Text("OPERATIONAL", style="bold #00ff88")
        table.add_row(row3, status)
        
        # Routing mode
        row4 = Text()
        row4.append("Routing Mode", style="#808090")
        mode = Text(self.state.route_mode.upper(), style="bold #00d4ff")
        table.add_row(row4, mode)
        
        return Panel(
            table,
            title="[bold #00d4ff]SYSTEM OVERVIEW",
            border_style="#1a1a3a",
            padding=(1, 2),
        )
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
        # Start auto-refresh using set_interval
        self._refresh_task = self.set_interval(2.0, self.update_display)
    
    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        # Stop auto-refresh
        if self._refresh_task:
            self._refresh_task.stop()
    
    def update_display(self) -> None:
        """Update all widgets with current state."""
        try:
            # Update metrics
            metrics_widget = self.query_one("#metrics", MetricsWidget)
            metrics_widget.update_metrics(self.state.latest_metrics)
        except Exception:
            pass
        
        try:
            # Update agents - will be populated by proxy integration
            agents_widget = self.query_one("#agents", AgentStatusWidget)
            # Agent data is updated via on_agent_update callback in main.py
        except Exception:
            pass
        
        try:
            # Update stats panel
            stats_panel = self.query_one("#stats_panel", Static)
            stats_panel.update(self._render_stats())
        except Exception:
            pass
