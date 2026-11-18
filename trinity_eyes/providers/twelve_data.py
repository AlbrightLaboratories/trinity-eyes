"""Twelve Data provider - paid slot (disabled by default)."""

from .base import BaseProvider
from ..models import Index


class TwelveDataProvider(BaseProvider):
    """
    Twelve Data API - Premium provider.
    
    Paid: $80-200/mo
    Best for: Real-time global coverage, WebSocket
    
    Enable by setting TWELVE_DATA_API_KEY and enabled: true in config
    """
    
    BASE_URL = "https://api.twelvedata.com"
    
    async def fetch(self, symbol: str) -> Index:
        # Placeholder - implement when paid slot is enabled
        raise NotImplementedError("Twelve Data not configured")
