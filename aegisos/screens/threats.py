from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static
from ..widgets import ThreatCard

class ThreatsScreen(Screen):
    """Screen showing all detected threats."""
    
    CSS = """
    ThreatsScreen {
        background: #0a0a1a;
    }
    
    #threats_container {
        height: 100%;
        width: 100%;
        padding: 1;
    }
    
    #threats_scroll {
        height: 100%;
        width: 100%;
    }
    
    .empty_message {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: #606070;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="threats_container"):
            yield Static("No threats detected yet.\nSystem is secure.", classes="empty_message", id="empty_msg")
            with VerticalScroll(id="threats_scroll"):
                pass
    
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_display()
    
    def update_display(self) -> None:
        """Refresh threat list."""
        try:
            empty_msg = self.query_one("#empty_msg", Static)
            scroll = self.query_one("#threats_scroll", VerticalScroll)
            
            if not self.state.events:
                empty_msg.display = True
                scroll.display = False
            else:
                empty_msg.display = False
                scroll.display = True
                
                # Clear existing threat cards
                scroll.remove_children()
                
                # Mount new threat cards
                for event in self.state.events:
                    scroll.mount(ThreatCard(event))
        except Exception:
            pass
