from textual.widget import Widget
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class MetricsWidget(Widget):
    """Display system metrics (CPU, GPU, RAM, VRAM, tokens/sec)."""
    
    DEFAULT_CSS = """
    MetricsWidget {
        height: 8;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics = {
            "cpu": 0,
            "gpu": 0,
            "ram": 0,
            "vram": 0,
            "tokens_sec": 0,
        }
    
    def update_metrics(self, metrics: dict):
        """Update metrics values."""
        self.metrics.update(metrics)
        self.refresh()
    
    def _make_bar(self, value: float, width: int = 20) -> Text:
        """Create a horizontal bar chart."""
        filled = int(value / 100 * width)
        empty = width - filled
        
        bar = Text()
        if value >= 90:
            color = "#ff0066"
        elif value >= 70:
            color = "#ffaa00"
        else:
            color = "#00ff88"
        
        bar.append("█" * filled, style=f"bold {color}")
        bar.append("░" * empty, style="dim #303040")
        bar.append(f" {value:>3.0f}%", style=color)
        return bar
    
    def render(self):
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="left", width=8)
        table.add_column(justify="left")
        
        # CPU
        cpu_label = Text("CPU", style="bold #00d4ff")
        cpu_bar = self._make_bar(self.metrics["cpu"])
        table.add_row(cpu_label, cpu_bar)
        
        # GPU
        gpu_label = Text("GPU", style="bold #00d4ff")
        gpu_bar = self._make_bar(self.metrics["gpu"])
        table.add_row(gpu_label, gpu_bar)
        
        # RAM
        ram_label = Text("RAM", style="bold #00d4ff")
        ram_bar = self._make_bar(self.metrics["ram"])
        table.add_row(ram_label, ram_bar)
        
        # VRAM
        vram_label = Text("VRAM", style="bold #00d4ff")
        vram_bar = self._make_bar(self.metrics["vram"])
        table.add_row(vram_label, vram_bar)
        
        # Tokens/sec
        tokens_label = Text("Tokens", style="bold #00d4ff")
        tokens_value = Text(f"{self.metrics['tokens_sec']:.1f} tok/s", style="#00ff88")
        table.add_row(tokens_label, tokens_value)
        
        return Panel(
            table,
            title="[bold #00d4ff]SYSTEM METRICS",
            border_style="#1a1a3a",
            padding=(0, 1),
        )
