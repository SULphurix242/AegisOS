from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import time

class AgentsScreen(Screen):
    """Screen for monitoring and controlling AI agents status."""
    
    CSS = """
    AgentsScreen {
        background: #0a0a1a;
    }
    
    #agents_screen_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #agents_scroll {
        height: 1fr;
        width: 100%;
        margin-top: 1;
    }
    
    #agents_summary_panel {
        height: 5;
        width: 100%;
        margin-bottom: 1;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self._refresh_timer = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="agents_screen_container"):
            yield Static("", id="agents_summary_panel")
            with VerticalScroll(id="agents_scroll"):
                yield Static("Loading agents...", id="agents_list_static")
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
        # Set periodic refresh
        self._refresh_timer = self.set_interval(1.5, self.update_display)
    
    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()
            
    def _get_agents(self) -> list:
        """Helper to get current agent list from app."""
        if hasattr(self.app, "get_current_agents"):
            return self.app.get_current_agents()
        # Fallback to state agents_list or some default structure
        return getattr(self.state, "agents_list", []) or []

    def update_display(self) -> None:
        """Update display with latest agent statuses."""
        try:
            agents = self._get_agents()
            self._update_summary(agents)
            self._update_list(agents)
        except Exception:
            pass

    def _update_summary(self, agents: list) -> None:
        """Update top summary statistics panel."""
        total = len(agents)
        active = sum(1 for a in agents if a.get("state", "ACTIVE").upper() in ("ACTIVE", "RUNNING"))
        isolated = sum(1 for a in agents if a.get("state", "").upper() == "ISOLATED")
        compromised = sum(1 for a in agents if a.get("status", "").lower() in ("compromised", "suspicious"))
        
        summary_table = Table.grid(padding=(0, 4))
        summary_table.add_column()
        summary_table.add_column()
        summary_table.add_column()
        summary_table.add_column()
        
        summary_table.add_row(
            Text.assemble(("TOTAL AGENTS: ", "dim #808090"), (f"{total}", "bold #00d4ff")),
            Text.assemble(("✓ ACTIVE: ", "dim #808090"), (f"{active}", "bold #00ff88")),
            Text.assemble(("🔒 ISOLATED: ", "dim #808090"), (f"{isolated}", "bold #ffaa00")),
            Text.assemble(("🔴 COMPROMISED: ", "dim #808090"), (f"{compromised}", "bold #ff0066")),
        )
        
        panel = Panel(
            summary_table,
            title="[bold #00d4ff]AGENT IMMUNE SYSTEM SUMMARY",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        
        self.query_one("#agents_summary_panel", Static).update(panel)

    def _update_list(self, agents: list) -> None:
        """Update the main scrollable list of agent cards."""
        if not agents:
            self.query_one("#agents_list_static", Static).update(
                Panel(
                    Text("No agents are currently registered with AegisOS Proxy Server.", style="dim italic #606070", justify="center"),
                    border_style="#1a1a3a",
                    title="ACTIVE AGENTS",
                )
            )
            return
            
        content = []
        for agent in agents:
            # Gather attributes
            name = agent.get("name", "Unknown-Agent")
            role = agent.get("role", "General Task")
            model = agent.get("model", "N/A")
            state = agent.get("state", "ACTIVE").upper()
            status = agent.get("status", "active").lower()
            threat_count = agent.get("threat_count", 0)
            risk = agent.get("risk", 0.0)
            uptime_s = agent.get("uptime_seconds", 0)
            
            # Format status and state
            state_text = Text()
            if state == "ISOLATED":
                state_text.append("🔒 ISOLATED", style="bold #ffaa00")
            elif state == "PAUSED":
                state_text.append("⏸ PAUSED", style="bold #ffff00")
            elif state == "KILLED":
                state_text.append("💀 KILLED", style="bold #ff0066")
            else:
                state_text.append("✓ ACTIVE", style="bold #00ff88")
                
            status_text = Text()
            if status == "compromised":
                status_text.append("CRITICAL RISK", style="bold #ff0066")
            elif status == "suspicious":
                status_text.append("SUSPICIOUS", style="bold #ffaa00")
            else:
                status_text.append("SECURE", style="bold #00ff88")
                
            # Build Uptime String
            h, remainder = divmod(uptime_s, 3600)
            m, sec = divmod(remainder, 60)
            uptime_str = f"{h:02d}:{m:02d}:{sec:02d}"
            
            # Risk bar (10 blocks)
            filled = int(risk * 10)
            empty = 10 - filled
            risk_color = "#00ff88"
            if risk >= 0.7:
                risk_color = "#ff0066"
            elif risk >= 0.4:
                risk_color = "#ffaa00"
                
            risk_bar = Text()
            risk_bar.append("█" * filled, style=f"bold {risk_color}")
            risk_bar.append("░" * empty, style="dim #303040")
            risk_bar.append(f" {int(risk * 100)}%", style=f"bold {risk_color}")
            
            # Create a nice layout grid for agent info
            grid = Table.grid(padding=(0, 4))
            grid.add_column(width=25)
            grid.add_column(width=30)
            grid.add_column(width=25)
            
            grid.add_row(
                Text.assemble(("Role: ", "dim #808090"), (role, "#c0c0d0")),
                Text.assemble(("Uptime: ", "dim #808090"), (uptime_str, "#00d4ff")),
                Text.assemble(("Agent State: ", "dim #808090"), state_text)
            )
            grid.add_row(
                Text.assemble(("LLM Base: ", "dim #808090"), (model, "#808090")),
                Text.assemble(("Risk Level: ", "dim #808090"), risk_bar),
                Text.assemble(("Health Index: ", "dim #808090"), status_text)
            )
            grid.add_row(
                Text.assemble(("Threats Blocked: ", "dim #808090"), (str(threat_count), "bold #ff6600")),
                Text("", style="dim"),
                Text.assemble(("ID: ", "dim #808090"), (agent.get("id", "N/A"), "dim #606070"))
            )
            
            # Draw individual panel
            border_style = "#1a1a3a"
            if state == "ISOLATED":
                border_style = "#ffaa00"
            elif status == "compromised":
                border_style = "#ff0066"
                
            agent_panel = Panel(
                grid,
                title=f"[bold #00d4ff]🤖 {name.upper()}",
                border_style=border_style,
                padding=(1, 2)
            )
            content.append(agent_panel)
            
        from rich.console import Group
        self.query_one("#agents_list_static", Static).update(Group(*content))