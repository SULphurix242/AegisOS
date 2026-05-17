from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 300) -> dict:
        """
        Returns dict with keys:
          text: str           — model response
          latency_ms: int     — wall-clock time
          tokens: int         — total tokens used
          provider: str       — provider name string
        Raises httpx.HTTPError or Exception on failure.
        Never returns None.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if API key is non-empty."""
        ...
