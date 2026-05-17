from textual.widget import Widget
from rich.panel import Panel
from rich.text import Text

NAV_ITEMS = [
    ("1", "DASHBOARD"),
    ("2", "THREATS"),
    ("3", "AGENTS"),
    ("4", "MODELS"),
    ("5", "TELEMETRY"),
    ("6", "SANDBOX"),
    ("7", "LOGS"),
    ("8", "KEYS"),
    ("9", "MODEL CFG"),
    ("?", "HELP"),
    ("Q", "QUIT"),
]

class NavPanel(Widget):
    DEFAULT_CSS = "NavPanel { width: 14; }"

    def __init__(self, active: str = "DASHBOARD", **kwargs):
        super().__init__(**kwargs)
        self.active = active

    def render(self):
        lines = []
        for key, label in NAV_ITEMS:
            if label == self.active:
                line = Text(f" [{key}] {label}", style="bold #00d4ff")
                line.stylize("on #0a0a25")
            else:
                line = Text(f" [{key}] {label}", style="#505070")
            lines.append(line)
        # Join with newlines for rendering
        from rich.console import Group
        return Panel(Group(*lines), title="NAV", border_style="#1a1a3a", padding=(0, 0))
