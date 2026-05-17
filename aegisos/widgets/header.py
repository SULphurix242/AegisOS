from textual.widget import Widget
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class HeaderWidget(Widget):
    """Top header showing system status and key metrics."""
    
    DEFAULT_CSS = """
    HeaderWidget {
        height: 3;
        dock: top;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.threat_count = 0
        self.lockdown = False
        self.providers_online = 0
        self.providers_total = 3
    
    def update_stats(self, threat_count: int, lockdown: bool, providers_online: int, providers_total: int = 3):
        """Update header statistics."""
        self.threat_count = threat_count
        self.lockdown = lockdown
        self.providers_online = providers_online
        self.providers_total = providers_total
        self.refresh()
    
    def render(self):
        # Create header table
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="center", ratio=1)
        table.add_column(justify="right", ratio=1)
        
        # Left: Logo and title
        title = Text()
        title.append("⚔️  ", style="bold #ff0066")
        title.append("AEGIS", style="bold #00d4ff")
        title.append("OS", style="bold #00ff88")
        title.append(" v1.0", style="dim #505070")
        
        # Center: Status
        if self.lockdown:
            status = Text("🔒 LOCKDOWN ACTIVE", style="bold #ff0066 on #330011")
        else:
            status = Text("✓ OPERATIONAL", style="bold #00ff88")
        
        # Right: Metrics
        metrics = Text()
        metrics.append(f"Threats: ", style="#808090")
        metrics.append(f"{self.threat_count}", style="bold #ff6600")
        metrics.append(" | ", style="dim #404050")
        metrics.append(f"LLMs: ", style="#808090")
        
        if self.providers_online == 0:
            metrics.append(f"{self.providers_online}/{self.providers_total}", style="bold #ff0066")
        elif self.providers_online < self.providers_total:
            metrics.append(f"{self.providers_online}/{self.providers_total}", style="bold #ffaa00")
        else:
            metrics.append(f"{self.providers_online}/{self.providers_total}", style="bold #00ff88")
        
        table.add_row(title, status, metrics)
        
        return Panel(
            table,
            border_style="#1a1a3a",
            style="on #0a0a1a"
        )
