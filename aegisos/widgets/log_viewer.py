from textual.widget import Widget
from textual.widgets import RichLog
from rich.text import Text

class LogViewer(RichLog):
    """Scrollable log viewer for routing events and system messages."""
    
    DEFAULT_CSS = """
    LogViewer {
        height: 100%;
        border: solid #1a1a3a;
        background: #0a0a1a;
    }
    """
    
    def __init__(self, max_lines: int = 500, **kwargs):
        super().__init__(max_lines=max_lines, **kwargs)
    
    def log_routing(self, event: dict):
        """Log an LLM routing event."""
        task = event.get("task", "unknown")
        provider = event.get("provider", "NONE")
        success = event.get("success", False)
        latency = event.get("latency_ms", 0)
        
        line = Text()
        line.append("[ROUTE] ", style="bold #00d4ff")
        line.append(f"{task:12s} ", style="#808090")
        line.append("→ ", style="dim #404050")
        
        if success:
            line.append(f"{provider:10s}", style="bold #00ff88")
            line.append(f" ({latency}ms)", style="dim #00ff88")
        else:
            line.append(f"{provider:10s}", style="bold #ff0066")
            error = event.get("error", "Failed")[:40]
            line.append(f" [{error}]", style="dim #ff6600")
        
        self.write(line)
    
    def log_threat(self, event: dict):
        """Log a threat detection event."""
        threat_type = event.get("type", "Unknown")
        severity = event.get("severity", "LOW")
        agent = event.get("agent", "Unknown")
        
        line = Text()
        line.append("[THREAT] ", style="bold #ff6600")
        
        if severity == "CRITICAL":
            line.append(f"{severity:8s}", style="bold #ff0066")
        elif severity == "HIGH":
            line.append(f"{severity:8s}", style="bold #ff6600")
        elif severity == "MEDIUM":
            line.append(f"{severity:8s}", style="bold #ffaa00")
        else:
            line.append(f"{severity:8s}", style="#00aaff")
        
        line.append(" | ", style="dim #404050")
        line.append(f"{threat_type:20s}", style="#c0c0d0")
        line.append(" on ", style="dim #606070")
        line.append(agent, style="#00d4ff")
        
        self.write(line)
    
    def log_system(self, message: str, level: str = "INFO"):
        """Log a system message."""
        line = Text()
        
        if level == "ERROR":
            line.append("[ERROR] ", style="bold #ff0066")
            line.append(message, style="#ff6600")
        elif level == "WARN":
            line.append("[WARN]  ", style="bold #ffaa00")
            line.append(message, style="#ffaa00")
        elif level == "SUCCESS":
            line.append("[OK]    ", style="bold #00ff88")
            line.append(message, style="#00ff88")
        else:
            line.append("[INFO]  ", style="bold #00d4ff")
            line.append(message, style="#808090")
        
        self.write(line)
