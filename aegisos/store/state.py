from collections import deque
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class AppState:
    # Threat events — capped at 200
    events: deque = field(default_factory=lambda: deque(maxlen=200))

    # Metrics history — capped at 60 samples (2 min at 2s interval)
    metrics_history: deque = field(default_factory=lambda: deque(maxlen=60))

    # Latest metrics snapshot
    latest_metrics: dict = field(default_factory=lambda: {
        "cpu": 0, "gpu": 0, "ram": 0, "vram": 0, "tokens_sec": 0
    })

    # Active agents list
    agents_list: list = field(default_factory=list)

    # Routing history — capped at 100
    routing_history: deque = field(default_factory=lambda: deque(maxlen=100))

    # Provider status cache: {provider_name: {"online": bool, "latency_ms": int, "last_check": float}}
    provider_status: dict = field(default_factory=dict)

    # Current routing mode
    route_mode: str = "balanced"

    # Total threat count
    total_threats: int = 0

    # Lockdown state
    in_lockdown: bool = False

    def add_event(self, event: dict):
        # Replace existing event with same id (for update after LLM analysis)
        for i, e in enumerate(self.events):
            if e["id"] == event["id"]:
                self.events[i] = event
                return
        self.events.appendleft(event)
        self.total_threats += 1

    def get_recent_events(self, n: int = 10) -> list:
        return list(self.events)[:n]

    def add_routing_event(self, event: dict):
        self.routing_history.appendleft(event)
        # Update provider status cache
        provider = event.get("provider", "")
        if provider and provider != "NONE":
            self.provider_status[provider] = {
                "online": event.get("success", False),
                "latency_ms": event.get("latency_ms", 0),
                "last_check": __import__("time").monotonic(),
            }
