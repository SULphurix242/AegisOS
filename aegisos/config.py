import os
import sys
from dotenv import load_dotenv
from dataclasses import dataclass, field

@dataclass
class AegisConfig:
    groq_key: str
    cerebras_key: str
    gemini_key: str
    groq_model: str
    cerebras_model: str
    gemini_model: str
    route_mode: str
    event_interval: float
    min_cols: int
    min_rows: int
    llm_timeout: int
    gemini_timeout: int

    def has_any_key(self) -> bool:
        return bool(self.groq_key or self.cerebras_key or self.gemini_key)

    def available_providers(self) -> list[str]:
        """Return list of provider names that have keys configured."""
        providers = []
        if self.groq_key:
            providers.append("Groq")
        if self.cerebras_key:
            providers.append("Cerebras")
        if self.gemini_key:
            providers.append("Gemini")
        return providers

    def validate_route_mode(self) -> str:
        valid = {"balanced", "cheapest", "fastest", "smartest"}
        if self.route_mode not in valid:
            return "balanced"
        return self.route_mode


def load_config() -> AegisConfig:
    load_dotenv(override=True)

    def _float_env(key: str, default: float) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _int_env(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    cfg = AegisConfig(
        groq_key=os.getenv("GROQ_API_KEY", "").strip(),
        cerebras_key=os.getenv("CEREBRAS_API_KEY", "").strip(),
        gemini_key=os.getenv("GEMINI_API_KEY", "").strip(),
        groq_model=os.getenv("GROQ_MODEL", "llama3-70b-8192").strip(),
        cerebras_model=os.getenv("CEREBRAS_MODEL", "llama3.1-70b").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip(),
        route_mode=os.getenv("AEGIS_ROUTE_MODE", "balanced").strip(),
        event_interval=max(1.0, _float_env("AEGIS_EVENT_INTERVAL", 4.0)),
        min_cols=_int_env("AEGIS_MIN_COLS", 120),
        min_rows=_int_env("AEGIS_MIN_ROWS", 30),
        llm_timeout=_int_env("AEGIS_LLM_TIMEOUT", 15),
        gemini_timeout=_int_env("AEGIS_GEMINI_TIMEOUT", 20),
    )
    cfg.route_mode = cfg.validate_route_mode()
    return cfg
