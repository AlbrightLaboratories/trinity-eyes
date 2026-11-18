"""Alpha Vantage provider - free tier with API key."""

import asyncio
import re
import aiohttp
from datetime import datetime
from typing import Optional

from .base import BaseProvider
from ..models import Index, Quote, Forex


# Plain US-listed ticker (SPY, AAPL, BRK.B). Anything else (^N225, ES=F,
# 000001.SS) is not served by GLOBAL_QUOTE and must not spend a request.
_US_TICKER = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


class UnsupportedSymbolError(ValueError):
    """Symbol is outside what Alpha Vantage GLOBAL_QUOTE serves."""


class AlphaVantageProvider(BaseProvider):
    """
    Alpha Vantage API.
    
    Free tier: 25 requests/day
    Paid: Higher limits
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def fetch(self, symbol: str) -> Index:
        """Fetch index/stock data."""
        if not _US_TICKER.match(symbol):
            raise UnsupportedSymbolError(f"Alpha Vantage does not serve {symbol!r}")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not configured")
        
        session = await self._get_session()
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with session.get(self.BASE_URL, params=params) as resp:
            data = await resp.json()
        
        if "Global Quote" not in data:
            raise ValueError(f"Invalid response: {data}")
        
        quote = data["Global Quote"]
        price = float(quote.get("05. price", 0))
        change = float(quote.get("09. change", 0))
        change_pct = float(quote.get("10. change percent", "0%").rstrip("%"))
        
        return Index(
            symbol=symbol,
            name=symbol,
            close=price,
            change=change,
            change_pct=change_pct,
            timestamp=datetime.now(),
            source="alpha_vantage"
        )
    
    async def fetch_quote(self, symbol: str) -> Quote:
        """Fetch quote."""
        index = await self.fetch(symbol)
        return Quote(
            symbol=index.symbol,
            price=index.close,
            change=index.change,
            change_pct=index.change_pct,
            volume=0,  # Would need separate API call
            timestamp=index.timestamp,
            source="alpha_vantage"
        )
    
    async def close(self):
        if self._session:
            await self._session.close()
