import httpx
import time
from .base import BaseLLMClient

class GeminiClient(BaseLLMClient):
    BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    PROVIDER_NAME = "Gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", *, timeout: int = 20):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def complete(self, system: str, user: str, max_tokens: int = 300) -> dict:
        if not self.is_configured():
            raise ValueError("Gemini API key not configured")

        url = self.BASE.format(model=self._model) + f"?key={self._api_key}"
        # Gemini does not have a system role — prepend system to user message
        combined = f"{system}\n\n{user}"
        body = {
            "contents": [
                {"role": "user", "parts": [{"text": combined}]}
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.monotonic() - t0) * 1000)

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            # Gemini may return empty candidates if content filtered
            finish_reason = ""
            try:
                finish_reason = data["candidates"][0].get("finishReason", "UNKNOWN")
            except (KeyError, IndexError):
                pass
            text = f"[Gemini blocked response: {finish_reason}]"

        try:
            tokens = data["usageMetadata"]["totalTokenCount"]
        except KeyError:
            tokens = 0

        return {
            "text": text,
            "latency_ms": latency_ms,
            "tokens": tokens,
            "provider": self.PROVIDER_NAME,
        }
