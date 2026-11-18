"""FRED provider - Federal Reserve Economic Data."""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional

from .base import BaseProvider
from ..models import Yields


class FREDProvider(BaseProvider):
    """
    FRED API - Federal Reserve Economic Data.
    
    Free: Unlimited with API key
    Official source for US Treasury yields, economic data
    """
    
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    
    # FRED series IDs for treasury yields
    SERIES = {
        "us_2y": "DGS2",
        "us_10y": "DGS10",
        "us_30y": "DGS30",
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _fetch_series(self, series_id: str) -> float:
        """Fetch latest value for a FRED series."""
        if not self.api_key:
            raise ValueError("FRED API key not configured")
        
        session = await self._get_session()
        
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "limit": 1,
            "sort_order": "desc"
        }
        
        async with session.get(self.BASE_URL, params=params) as resp:
            data = await resp.json()
        
        obs = data.get("observations", [])
        if not obs:
            return 0.0
        
        value = obs[0].get("value", ".")
        return float(value) if value != "." else 0.0
    
    async def fetch(self, symbol: str) -> Yields:
        """Fetch US Treasury yields."""
        # Fetch all yields in parallel
        tasks = [
            self._fetch_series(self.SERIES["us_2y"]),
            self._fetch_series(self.SERIES["us_10y"]),
            self._fetch_series(self.SERIES["us_30y"]),
        ]
        
        us_2y, us_10y, us_30y = await asyncio.gather(*tasks)
        
        return Yields(
            us_2y=us_2y,
            us_10y=us_10y,
            us_30y=us_30y,
            spread_2_10=round(us_10y - us_2y, 2),
            timestamp=datetime.now(),
            source="fred"
        )
    
    async def close(self):
        if self._session:
            await self._session.close()
