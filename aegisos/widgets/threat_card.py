from textual.widget import Widget
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

SEVERITY_COLORS = {
    "CRITICAL": "#ff0066",
    "HIGH": "#ff6600",
    "MEDIUM": "#ffaa00",
    "LOW": "#00aaff",
}

SEVERITY_ICONS = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
}

class ThreatCard(Widget):
    """Display a single threat event as a card."""
    
    DEFAULT_CSS = """
    ThreatCard {
        height: auto;
        margin: 0 1;
    }
    """
    
    def __init__(self, event: dict, **kwargs):
        super().__init__(**kwargs)
        self.event = event
    
    def render(self):
        event = self.event
        severity = event.get("severity", "LOW")
        color = SEVERITY_COLORS.get(severity, "#808090")
        icon = SEVERITY_ICONS.get(severity, "⚪")
        
        # Title line
        title = Text()
        title.append(f"{icon} ", style=f"bold {color}")
        title.append(event.get("type", "Unknown Threat"), style=f"bold {color}")
        title.append(f" [{severity}]", style=f"dim {color}")
        
        # Build content
        lines = []
        
        # Agent and timestamp
        info = Text()
        info.append("Agent: ", style="dim #808090")
        info.append(event.get("agent", "Unknown"), style="#00d4ff")
        info.append(" | ", style="dim #404050")
        info.append("Time: ", style="dim #808090")
        info.append(event.get("timestamp", "N/A"), style="#808090")
        lines.append(info)
        
        # Status and confidence
        status_line = Text()
        status = event.get("status", "DETECTED")
        if status == "BLOCKED":
            status_line.append("Status: ", style="dim #808090")
            status_line.append("BLOCKED", style="bold #ff0066")
        else:
            status_line.append("Status: ", style="dim #808090")
            status_line.append(status, style="#00ff88")
        
        confidence = event.get("confidence", 0)
        if confidence > 0:
            status_line.append(" | ", style="dim #404050")
            status_line.append("Confidence: ", style="dim #808090")
            status_line.append(f"{int(confidence * 100)}%", style="#ffaa00")
        lines.append(status_line)
        
        # AI Summary if available
        summary = event.get("ai_summary", "")
        if summary and summary != "Summary unavailable.":
            lines.append(Text())  # blank line
            summary_text = Text()
            summary_text.append("AI Analysis: ", style="bold #00d4ff")
            summary_text.append(summary, style="#c0c0d0")
            lines.append(summary_text)
        
        # Mitigation
        mitigation = event.get("mitigation", "")
        if mitigation:
            lines.append(Text())  # blank line
            mit_text = Text()
            mit_text.append("→ ", style="bold #00ff88")
            mit_text.append(mitigation, style="#a0ffa0")
            lines.append(mit_text)
        
        # Payload preview (truncated)
        payload = event.get("payload", "")
        if payload:
            lines.append(Text())  # blank line
            payload_preview = payload[:120] + ("..." if len(payload) > 120 else "")
            payload_text = Text()
            payload_text.append("Payload: ", style="dim #606070")
            payload_text.append(payload_preview, style="dim italic #707080")
            lines.append(payload_text)
        
        from rich.console import Group
        content = Group(*lines)
        
        return Panel(
            content,
            title=title,
            border_style=color,
            padding=(0, 1),
        )
