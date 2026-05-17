import httpx
import time
from .base import BaseLLMClient

class GroqClient(BaseLLMClient):
    BASE = "https://api.groq.com/openai/v1/chat/completions"
    PROVIDER_NAME = "Groq"

    def __init__(self, api_key: str, model: str = "llama3-70b-8192", *, timeout: int = 15):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def complete(self, system: str, user: str, max_tokens: int = 300) -> dict:
        if not self.is_configured():
            raise ValueError("Groq API key not configured")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False,
        }

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(self.BASE, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.monotonic() - t0) * 1000)

        # Defensive parsing — Groq response structure may vary
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            text = ""

        try:
            tokens = data["usage"]["total_tokens"]
        except KeyError:
            tokens = 0

        return {
            "text": text,
            "latency_ms": latency_ms,
            "tokens": tokens,
            "provider": self.PROVIDER_NAME,
        }
