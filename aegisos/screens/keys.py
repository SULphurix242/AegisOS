from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Input, Button
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import os
from ..config import load_config
from ..engine.router import LLMRouter

class KeysScreen(Screen):
    """Screen for managing and hot-reloading LLM API provider keys."""
    
    CSS = """
    KeysScreen {
        background: #0a0a1a;
    }
    
    #keys_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #keys_scroll {
        height: 100%;
        width: 100%;
    }
    
    .key_label {
        margin-top: 1;
        color: #00d4ff;
        text-style: bold;
    }
    
    .key_input {
        background: #070715;
        border: tall #1a1a3a;
        color: #00ff88;
        margin-bottom: 1;
    }
    
    #save_keys_btn {
        margin-top: 2;
        width: 100%;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="keys_container"):
            with VerticalScroll(id="keys_scroll"):
                # Description header
                yield Static(self._render_header(), id="keys_desc")
                
                # Groq Key
                yield Static("GROQ API KEY", classes="key_label")
                yield Input(placeholder="gsk_...", password=True, id="groq_input", classes="key_input")
                
                # Cerebras Key
                yield Static("CEREBRAS API KEY", classes="key_label")
                yield Input(placeholder="csk_...", password=True, id="cerebras_input", classes="key_input")
                
                # Gemini Key
                yield Static("GOOGLE GEMINI API KEY", classes="key_label")
                yield Input(placeholder="AIzaSy...", password=True, id="gemini_input", classes="key_input")
                
                # Save button
                yield Button("Save & Hot-Reload API Gateways", id="save_keys_btn", variant="primary")
                
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._load_current_keys()
        
    def _render_header(self) -> Panel:
        """Render keys setup description."""
        content = []
        content.append(Text("AegisOS Live Key Management Portal", style="bold #00d4ff"))
        content.append(Text("Update or enter your API credentials here.", style="#808090"))
        content.append(Text("Saving will immediately hot-reload the underlying LLM consensus routers in real-time.", style="#808090"))
        
        from rich.console import Group
        return Panel(
            Group(*content),
            title="[bold #00d4ff]🔑 PROVIDER API SETTINGS",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        
    def _load_current_keys(self) -> None:
        """Prefill inputs with active keys."""
        config = self.app.config
        
        # We prefill only if they exist, maintaining privacy (passwords are masked in Input)
        if config.groq_key:
            self.query_one("#groq_input", Input).value = config.groq_key
        if config.cerebras_key:
            self.query_one("#cerebras_input", Input).value = config.cerebras_key
        if config.gemini_key:
            self.query_one("#gemini_input", Input).value = config.gemini_key
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save action."""
        if event.button.id == "save_keys_btn":
            self._save_and_reload()
            
    def _save_and_reload(self) -> None:
        """Persist keys to .env and hot-reload active router engines."""
        groq = self.query_one("#groq_input", Input).value.strip()
        cerebras = self.query_one("#cerebras_input", Input).value.strip()
        gemini = self.query_one("#gemini_input", Input).value.strip()
        
        try:
            # Save to dotenv file
            self._save_to_dotenv(groq, cerebras, gemini)
            
            # Hot-reload configuration in the main application instance
            self.app.config = load_config()
            
            # Recreate LLMRouter to load fresh API Keys
            self.app.router = LLMRouter(self.app.config, self.app.on_routing_event)
            self.app.analyzer.router = self.app.router
            
            # Update app provider statuses
            self.app.state.provider_status["Groq"] = {"online": bool(groq), "latency_ms": 0}
            self.app.state.provider_status["Cerebras"] = {"online": bool(cerebras), "latency_ms": 0}
            self.app.state.provider_status["Gemini"] = {"online": bool(gemini), "latency_ms": 0}
            
            # Sync header status
            if hasattr(self.app, "query_one"):
                from ..widgets import HeaderWidget
                try:
                    header = self.app.query_one("#header", HeaderWidget)
                    providers_online = len([p for p in self.app.state.provider_status.values() if p.get("online")])
                    header.update_stats(
                        self.app.state.total_threats,
                        self.app.state.in_lockdown,
                        providers_online,
                        len(self.app.get_current_agents())
                    )
                except Exception:
                    pass
            
            self.app.notify("✓ API Keys saved & Hot-Reloaded successfully!", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Failed to save keys: {e}", severity="error")
            
    def _save_to_dotenv(self, groq: str, cerebras: str, gemini: str) -> None:
        """Write key assignments cleanly into local .env file."""
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                env_lines = f.readlines()
                
        keys_map = {
            "GROQ_API_KEY": groq,
            "CEREBRAS_API_KEY": cerebras,
            "GEMINI_API_KEY": gemini
        }
        
        updated = set()
        new_lines = []
        for line in env_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                continue
            parts = stripped.split("=", 1)
            k = parts[0].strip()
            if k in keys_map:
                new_lines.append(f"{k}={keys_map[k]}\n")
                updated.add(k)
            else:
                new_lines.append(line)
                
        for k, v in keys_map.items():
            if k not in updated:
                new_lines.append(f"{k}={v}\n")
                
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)