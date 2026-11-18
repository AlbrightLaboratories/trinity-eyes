"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
import os


class BaseProvider(ABC):
    """Base class for all data providers."""
    
    def __init__(self, config: dict):
        self.name = config.get("name", self.__class__.__name__)
        self.provider_type = config.get("type", "free")
        self.api_key = config.get("api_key") or os.getenv(
            f"{self.name.upper()}_API_KEY"
        )
        self.rate_limit = config.get("rate_limit")
        self._request_count = 0
    
    @abstractmethod
    async def fetch(self, symbol: str) -> Any:
        """Fetch data for symbol."""
        pass
    
    async def fetch_quote(self, symbol: str) -> Any:
        """Fetch quote data. Override if supported."""
        raise NotImplementedError(f"{self.name} does not support quotes")
    
    async def fetch_calendar(self, days_ahead: int) -> List[Any]:
        """Fetch economic calendar. Override if supported."""
        raise NotImplementedError(f"{self.name} does not support calendar")
    
    async def close(self):
        """Clean up resources."""
        pass
