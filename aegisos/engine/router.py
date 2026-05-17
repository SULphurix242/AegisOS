import asyncio
import time
from ..llm.groq import GroqClient
from ..llm.cerebras import CerebrasClient
from ..llm.gemini import GeminiClient
from typing import Callable, Awaitable

class LLMRouter:
    def __init__(self, config, on_routing_event: Callable | None = None):
        self.groq     = GroqClient(config.groq_key, config.groq_model, timeout=config.llm_timeout)
        self.cerebras = CerebrasClient(config.cerebras_key, config.cerebras_model, timeout=config.llm_timeout)
        self.gemini   = GeminiClient(config.gemini_key, config.gemini_model, timeout=config.gemini_timeout)
        self.on_routing_event = on_routing_event
        self.history = []   # list of routing event dicts, newest first

    # ── Public task methods ────────────────────────────────────────────

    async def classify(self, payload: str) -> dict:
        system = (
            "You are AegisOS threat classifier. Given a suspicious AI agent input, "
            "respond ONLY with valid JSON — no markdown fences, no preamble, no explanation. "
            "JSON schema: "
            "{\"is_threat\": boolean, "
            "\"confidence\": float between 0 and 1, "
            "\"category\": string, "
            "\"severity\": one of CRITICAL HIGH MEDIUM LOW, "
            "\"reason\": string max 20 words}"
        )
        return await self._route("classify", [self.groq, self.cerebras, self.gemini], system, payload, max_tokens=150)

    async def summarize(self, event: dict) -> dict:
        system = (
            "You are AegisOS threat analyst. Provide a brief, concise one-sentence explanation of: "
            "(1) what this AI attack was attempting to do, and "
            "(2) the potential damage if successful. "
            "Be extremely direct, brief, and technical. Under 25 words total. No preamble."
        )
        user = (
            f"Threat type: {event.get('type', 'Unknown')}\n"
            f"Agent role: {event.get('agent_role', 'Unknown')}\n"
            f"Payload: {event.get('payload', '')}\n"
            f"Agent: {event.get('agent', 'Unknown')}"
        )
        return await self._route("summarize", [self.cerebras, self.groq, self.gemini], system, user, max_tokens=120)

    async def advise(self, recent_events: list) -> dict:
        system = (
            "You are AegisOS security advisor. Analyze the threat pattern and provide "
            "exactly 3 numbered security recommendations. Each recommendation must be "
            "under 30 words and immediately actionable. Format:\n"
            "1. [Action]: [specific recommendation]\n"
            "2. [Action]: [specific recommendation]\n"
            "3. [Action]: [specific recommendation]"
        )
        threat_summary = "Recent threats detected:\n"
        for e in recent_events[:6]:
            threat_summary += f"- {e.get('type','?')} ({e.get('severity','?')}) on {e.get('agent','?')} at {e.get('timestamp','?')}\n"
        return await self._route("advise", [self.gemini, self.groq, self.cerebras], system, threat_summary, max_tokens=220)

    async def test_provider(self, provider_name: str) -> dict:
        """
        Test a specific provider with a simple ping prompt.
        Returns result dict with success, latency_ms, text.
        """
        client_map = {"Groq": self.groq, "Cerebras": self.cerebras, "Gemini": self.gemini}
        client = client_map.get(provider_name)
        if not client:
            return {"success": False, "error": f"Unknown provider: {provider_name}", "latency_ms": 0}
        if not client.is_configured():
            return {"success": False, "error": "API key not configured", "latency_ms": 0}
        try:
            result = await client.complete("You are a test.", "Reply with exactly: OK", max_tokens=5)
            result["success"] = True
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": 0, "provider": provider_name}

    # ── Internal routing ───────────────────────────────────────────────

    async def _route(self, task: str, priority_chain: list, system: str, user: str, max_tokens: int) -> dict:
        """
        Try each client in priority_chain in order.
        Skip unconfigured clients.
        Skip already-attempted clients (by class name).
        Return first success or error dict if all fail.
        """
        attempted = set()

        for client in priority_chain:
            class_name = client.__class__.__name__
            if class_name in attempted:
                continue
            if not client.is_configured():
                await self._emit({
                    "task": task,
                    "provider": client.PROVIDER_NAME,
                    "success": False,
                    "error": "Not configured",
                    "latency_ms": 0,
                    "tokens": 0,
                })
                attempted.add(class_name)
                continue

            attempted.add(class_name)
            try:
                result = await client.complete(system, user, max_tokens)
                result["task"] = task
                result["success"] = True
                await self._emit(result)
                return result
            except Exception as exc:
                await self._emit({
                    "task": task,
                    "provider": client.PROVIDER_NAME,
                    "success": False,
                    "error": str(exc)[:80],   # truncate long error messages
                    "latency_ms": 0,
                    "tokens": 0,
                })
                # Continue to next in chain

        # All providers failed
        error_result = {
            "task": task,
            "provider": "NONE",
            "success": False,
            "text": "All LLM providers failed or unconfigured.",
            "latency_ms": 0,
            "tokens": 0,
            "error": "All providers failed",
        }
        await self._emit(error_result)
        return error_result

    async def _emit(self, event: dict):
        """Append to history and notify callback."""
        self.history.insert(0, event)
        if len(self.history) > 100:
            self.history = self.history[:100]
        if self.on_routing_event:
            try:
                await self.on_routing_event(event)
            except Exception:
                pass
