from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class TelemetryScreen(Screen):
    """Screen for displaying detailed system performance telemetry and sparklines."""
    
    CSS = """
    TelemetryScreen {
        background: #0a0a1a;
    }
    
    #telemetry_screen_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #telemetry_scroll {
        height: 100%;
        width: 100%;
    }
    
    #metrics_dashboard {
        margin-bottom: 1;
    }
    
    #sparklines_panel {
        margin-top: 1;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        self._refresh_timer = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="telemetry_screen_container"):
            with VerticalScroll(id="telemetry_scroll"):
                yield Static(id="metrics_dashboard")
                yield Static(id="sparklines_panel")
                
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
        # Set periodic refresh
        self._refresh_timer = self.set_interval(1.5, self.update_display)
        
    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        if self._refresh_timer:
            self._refresh_timer.stop()
            
    def _make_bar(self, value: float, width: int = 30) -> Text:
        """Create a styled horizontal progress bar."""
        filled = int(max(0.0, min(1.0, value / 100.0)) * width)
        empty = width - filled
        
        bar = Text()
        if value >= 85:
            color = "#ff0066"  # CRITICAL
        elif value >= 60:
            color = "#ffaa00"  # HIGH/WARNING
        else:
            color = "#00ff88"  # SECURE/OK
            
        bar.append("█" * filled, style=f"bold {color}")
        bar.append("░" * empty, style="dim #303040")
        bar.append(f" {value:>3.1f}%", style=f"bold {color}")
        return bar

    def _make_sparkline(self, values: list, max_val: float = 100.0) -> Text:
        """Create a styled single-line unicode sparkline trend chart."""
        if not values:
            return Text("Collecting performance data...", style="dim italic #505060")
            
        spark_chars = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        sparkline = Text()
        
        for val in values:
            scaled = max(0.0, min(1.0, float(val) / max_val))
            idx = int(scaled * (len(spark_chars) - 1))
            char = spark_chars[idx]
            
            # Colorize sparkline points based on intensity
            if val >= max_val * 0.85:
                color = "#ff0066"
            elif val >= max_val * 0.60:
                color = "#ffaa00"
            else:
                color = "#00d4ff"
                
            sparkline.append(char, style=color)
            
        return sparkline

    def update_display(self) -> None:
        """Update telemetry widgets with latest metrics."""
        try:
            metrics = self.state.latest_metrics or {"cpu": 0, "gpu": 0, "ram": 0, "vram": 0, "tokens_sec": 0}
            self._update_metrics_dashboard(metrics)
            self._update_sparklines_panel()
        except Exception:
            pass

    def _update_metrics_dashboard(self, metrics: dict) -> None:
        """Render live system gauges and metrics values."""
        table = Table.grid(padding=(1, 4))
        table.add_column(justify="left", width=15)
        table.add_column(justify="left")
        
        # CPU
        table.add_row(
            Text("CPU CORE UTILS", style="bold #00d4ff"),
            self._make_bar(metrics.get("cpu", 0))
        )
        # GPU
        table.add_row(
            Text("GPU CORE UTILS", style="bold #00d4ff"),
            self._make_bar(metrics.get("gpu", 0))
        )
        # RAM
        table.add_row(
            Text("RAM ALLOCATED", style="bold #00d4ff"),
            self._make_bar(metrics.get("ram", 0))
        )
        # VRAM
        table.add_row(
            Text("VRAM ALLOCATED", style="bold #00d4ff"),
            self._make_bar(metrics.get("vram", 0))
        )
        # Tokens/sec
        tokens_val = metrics.get("tokens_sec", 0)
        table.add_row(
            Text("TOKEN RATE", style="bold #00d4ff"),
            Text(f"{tokens_val:.1f} tokens/second", style="bold #00ff88")
        )
        
        panel = Panel(
            table,
            title="[bold #00d4ff]LIVE SYSTEM PERFORMANCE CENTER",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        self.query_one("#metrics_dashboard", Static).update(panel)

    def _update_sparklines_panel(self) -> None:
        """Render scrolling sparkline history trend logs."""
        # Convert deque history to oldest-first list
        history = list(self.state.metrics_history)
        history.reverse()
        
        cpu_history = [h.get("cpu", 0) for h in history]
        gpu_history = [h.get("gpu", 0) for h in history]
        ram_history = [h.get("ram", 0) for h in history]
        vram_history = [h.get("vram", 0) for h in history]
        tok_history = [h.get("tokens_sec", 0) for h in history]
        
        max_tok = max(tok_history) if tok_history else 200.0
        max_tok = max(max_tok, 100.0) # ensure non-zero scaling floor
        
        table = Table.grid(padding=(0, 4))
        table.add_column(justify="left", width=25)
        table.add_column(justify="left")
        
        table.add_row(
            Text("CPU UTILS HIST (2m)", style="bold #808090"),
            self._make_sparkline(cpu_history, 100.0)
        )
        table.add_row(
            Text("GPU UTILS HIST (2m)", style="bold #808090"),
            self._make_sparkline(gpu_history, 100.0)
        )
        table.add_row(
            Text("RAM ALLOC HIST (2m)", style="bold #808090"),
            self._make_sparkline(ram_history, 100.0)
        )
        table.add_row(
            Text("VRAM ALLOC HIST (2m)", style="bold #808090"),
            self._make_sparkline(vram_history, 100.0)
        )
        table.add_row(
            Text("TOKEN RATE HIST (2m)", style="bold #808090"),
            self._make_sparkline(tok_history, max_tok)
        )
        
        panel = Panel(
            table,
            title="[bold #00d4ff]HISTORICAL TELEMETRY TRENDS",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        self.query_one("#sparklines_panel", Static).update(panel)