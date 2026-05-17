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

class ModelConfigScreen(Screen):
    """Screen for managing and hot-reloading LLM model assignments."""
    
    CSS = """
    ModelConfigScreen {
        background: #0a0a1a;
    }
    
    #modelcfg_container {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    
    #modelcfg_scroll {
        height: 100%;
        width: 100%;
    }
    
    .cfg_label {
        margin-top: 1;
        color: #00d4ff;
        text-style: bold;
    }
    
    .cfg_input {
        background: #070715;
        border: tall #1a1a3a;
        color: #00ff88;
        margin-bottom: 1;
    }
    
    #save_modelcfg_btn {
        margin-top: 2;
        width: 100%;
    }
    """
    
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Container(id="modelcfg_container"):
            with VerticalScroll(id="modelcfg_scroll"):
                # Description header
                yield Static(self._render_header(), id="modelcfg_desc")
                
                # Groq Model
                yield Static("GROQ MODEL NAME", classes="cfg_label")
                yield Input(placeholder="e.g. llama-3.3-70b-versatile", id="groq_model_input", classes="cfg_input")
                
                # Cerebras Model
                yield Static("CEREBRAS MODEL NAME", classes="cfg_label")
                yield Input(placeholder="e.g. llama3.1-70b", id="cerebras_model_input", classes="cfg_input")
                
                # Gemini Model
                yield Static("GOOGLE GEMINI MODEL NAME", classes="cfg_label")
                yield Input(placeholder="e.g. gemini-2.5-flash", id="gemini_model_input", classes="cfg_input")
                
                # Save button
                yield Button("Save & Hot-Reload Models", id="save_modelcfg_btn", variant="primary")
                
    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._load_current_models()
        
    def _render_header(self) -> Panel:
        """Render model config setup description."""
        content = []
        content.append(Text("AegisOS Live Model Configuration Portal", style="bold #00d4ff"))
        content.append(Text("Define custom LLM models for each provider here.", style="#808090"))
        content.append(Text("Saving will immediately hot-reload the underlying LLM consensus routers in real-time.", style="#808090"))
        
        from rich.console import Group
        return Panel(
            Group(*content),
            title="[bold #00d4ff]⚙️ ROUTER MODEL SETTINGS",
            border_style="#1a1a3a",
            padding=(1, 2)
        )
        
    def _load_current_models(self) -> None:
        """Prefill inputs with active models."""
        config = self.app.config
        
        # Pre-fill active model strings
        self.query_one("#groq_model_input", Input).value = config.groq_model or "llama3-70b-8192"
        self.query_one("#cerebras_model_input", Input).value = config.cerebras_model or "llama3.1-70b"
        self.query_one("#gemini_model_input", Input).value = config.gemini_model or "gemini-1.5-flash"
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save action."""
        if event.button.id == "save_modelcfg_btn":
            self._save_and_reload()
            
    def _save_and_reload(self) -> None:
        """Persist model settings to .env and hot-reload active router engines."""
        groq_m = self.query_one("#groq_model_input", Input).value.strip()
        cerebras_m = self.query_one("#cerebras_model_input", Input).value.strip()
        gemini_m = self.query_one("#gemini_model_input", Input).value.strip()
        
        try:
            # Save to dotenv file
            self._save_to_dotenv(groq_m, cerebras_m, gemini_m)
            
            # Hot-reload configuration in the main application instance
            self.app.config = load_config()
            
            # Recreate LLMRouter to load fresh Models
            self.app.router = LLMRouter(self.app.config, self.app.on_routing_event)
            self.app.analyzer.router = self.app.router
            
            self.app.notify("✓ Models saved & Hot-Reloaded successfully!", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Failed to save models: {e}", severity="error")
            
    def _save_to_dotenv(self, groq_m: str, cerebras_m: str, gemini_m: str) -> None:
        """Write model settings cleanly into local .env file."""
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                env_lines = f.readlines()
                
        keys_map = {
            "GROQ_MODEL": groq_m,
            "CEREBRAS_MODEL": cerebras_m,
            "GEMINI_MODEL": gemini_m
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