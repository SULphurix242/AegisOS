from textual.widget import Widget
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class AgentStatusWidget(Widget):
    """Display status of all AI agents being monitored."""
    
    DEFAULT_CSS = """
    AgentStatusWidget {
        height: auto;
    }
    """
    
    def __init__(self, agents: list = None, **kwargs):
        super().__init__(**kwargs)
        self.agents = agents or []
    
    def update_agents(self, agents: list):
        """Update agent list."""
        self.agents = agents
        self.refresh()
    
    def render(self):
        if not self.agents:
            empty = Text("No agents detected", style="dim italic #606070")
            return Panel(
                empty,
                title="[bold #00d4ff]AGENT STATUS",
                border_style="#1a1a3a",
                padding=(1, 2),
            )
        
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", width=20)
        table.add_column(justify="left", width=15)
        table.add_column(justify="left")
        
        # Header
        header_name = Text("AGENT", style="bold #808090")
        header_role = Text("ROLE", style="bold #808090")
        header_status = Text("STATUS", style="bold #808090")
        table.add_row(header_name, header_role, header_status)
        
        # Separator
        sep = Text("─" * 18, style="dim #303040")
        sep2 = Text("─" * 13, style="dim #303040")
        sep3 = Text("─" * 20, style="dim #303040")
        table.add_row(sep, sep2, sep3)
        
        # Agent rows
        for agent in self.agents:
            name = Text(agent.get("name", "Unknown"), style="#00d4ff")
            role = Text(agent.get("role", "Unknown"), style="#808090")
            
            status_text = Text()
            status = agent.get("status", "unknown")
            threat_count = agent.get("threat_count", 0)
            
            if status == "compromised":
                status_text.append("⚠️  COMPROMISED", style="bold #ff0066")
            elif status == "suspicious":
                status_text.append("⚡ SUSPICIOUS", style="bold #ffaa00")
            elif status == "active":
                status_text.append("✓ ACTIVE", style="bold #00ff88")
            else:
                status_text.append("○ IDLE", style="dim #606070")
            
            if threat_count > 0:
                status_text.append(f" ({threat_count} threats)", style="dim #ff6600")
            
            table.add_row(name, role, status_text)
        
        return Panel(
            table,
            title="[bold #00d4ff]AGENT STATUS",
            border_style="#1a1a3a",
            padding=(0, 1),
        )
