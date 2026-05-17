from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts and usage information."""
    
    CSS = """
    HelpScreen {
        background: #0a0a1a;
    }
    
    #help_container {
        height: 100%;
        width: 100%;
        padding: 2;
    }
    
    #help_scroll {
        height: 100%;
        width: 100%;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="help_container"):
            with VerticalScroll(id="help_scroll"):
                yield Static(self._render_help())
    
    def _render_help(self) -> Panel:
        """Render help content."""
        content = []
        
        # Title
        title = Text("AegisOS - AI Agent Immune System", style="bold #00d4ff")
        content.append(title)
        content.append(Text())
        
        # Description
        desc = Text(
            "AegisOS monitors AI agents in real-time, detecting and blocking malicious inputs "
            "using multi-LLM threat analysis with intelligent routing.",
            style="#c0c0d0"
        )
        content.append(desc)
        content.append(Text())
        content.append(Text())
        
        # Keyboard shortcuts
        shortcuts_title = Text("KEYBOARD SHORTCUTS", style="bold #00ff88")
        content.append(shortcuts_title)
        content.append(Text("─" * 60, style="dim #303040"))
        
        shortcuts = [
            ("1", "Dashboard", "System overview and live metrics"),
            ("2", "Threats", "View all detected threats"),
            ("3", "Agents", "Monitor AI agent status"),
            ("4", "Models", "LLM provider status and routing"),
            ("5", "Telemetry", "System performance metrics"),
            ("6", "Sandbox", "Test threat detection & simulation"),
            ("7", "Logs", "View system logs"),
            ("8", "Keys", "Manage LLM API credentials"),
            ("9", "Model Cfg", "Configure LLM models & trigger hot-reload"),
            ("?", "Help", "Show this help screen"),
            ("Q/ESC", "Quit", "Exit AegisOS"),
            ("L", "Lockdown", "Toggle system lockdown"),
            ("R", "Refresh", "Force refresh display"),
            ("S (in Sand.)", "Simulate", "Run background test agents traffic"),
        ]
        
        for key, name, desc in shortcuts:
            line = Text()
            line.append(f"  [{key}]", style="bold #00d4ff")
            line.append(f"  {name:15s}", style="bold #00ff88")
            line.append(f"  {desc}", style="#808090")
            content.append(line)
        
        content.append(Text())
        content.append(Text())
        
        # Features
        features_title = Text("KEY FEATURES", style="bold #00ff88")
        content.append(features_title)
        content.append(Text("─" * 60, style="dim #303040"))
        
        features = [
            "• Real-time threat detection and classification",
            "• Multi-LLM routing (Groq, Cerebras, Gemini)",
            "• Intelligent fallback and load balancing",
            "• AI-powered threat analysis and recommendations",
            "• Agent behavior monitoring",
            "• System lockdown for critical threats",
            "• Comprehensive logging and telemetry",
        ]
        
        for feature in features:
            content.append(Text(f"  {feature}", style="#c0c0d0"))
        
        content.append(Text())
        content.append(Text())
        
        # Routing modes
        routing_title = Text("ROUTING MODES", style="bold #00ff88")
        content.append(routing_title)
        content.append(Text("─" * 60, style="dim #303040"))
        
        modes = [
            ("balanced", "Balance between speed, cost, and quality"),
            ("cheapest", "Prioritize lowest cost providers"),
            ("fastest", "Prioritize lowest latency providers"),
            ("smartest", "Prioritize most capable models"),
        ]
        
        for mode, desc in modes:
            line = Text()
            line.append(f"  {mode:12s}", style="bold #00d4ff")
            line.append(f"  {desc}", style="#808090")
            content.append(line)
        
        content.append(Text())
        content.append(Text())
        
        # Footer
        footer = Text()
        footer.append("Made with ", style="dim #606070")
        footer.append("❤️", style="#ff0066")
        footer.append("", style="dim #606070")
        content.append(footer)
        
        from rich.console import Group
        return Panel(
            Group(*content),
            title="[bold #00d4ff]HELP & DOCUMENTATION",
            border_style="#1a1a3a",
            padding=(1, 2),
        )
