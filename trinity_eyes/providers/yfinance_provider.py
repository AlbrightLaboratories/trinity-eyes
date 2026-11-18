"""yfinance provider - primary free source."""

import asyncio
from datetime import datetime
from typing import Any

from .base import BaseProvider
from ..models import Index, Quote, Futures, Forex


class YFinanceProvider(BaseProvider):
    """
    Yahoo Finance provider via yfinance library.
    
    Pros: Free, global coverage, good historical data
    Cons: Unofficial API, can break, rate limited
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._yf = None
    
    def _get_yf(self):
        """Lazy load yfinance."""
        if self._yf is None:
            import yfinance as yf
            self._yf = yf
        return self._yf
    
    async def fetch(self, symbol: str) -> Index:
        """Fetch index data."""
        yf = self._get_yf()
        
        # Run in executor to not block
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker(symbol))
        info = await loop.run_in_executor(None, lambda: ticker.info)
        
        # Get current price
        price = info.get("regularMarketPrice") or info.get("previousClose", 0)
        prev_close = info.get("previousClose", price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return Index(
            symbol=symbol,
            name=info.get("shortName", symbol),
            close=price,
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            timestamp=datetime.now(),
            source="yfinance"
        )
    
    async def fetch_quote(self, symbol: str) -> Quote:
        """Fetch stock/ETF quote."""
        yf = self._get_yf()
        
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker(symbol))
        info = await loop.run_in_executor(None, lambda: ticker.info)
        
        price = info.get("regularMarketPrice") or info.get("previousClose", 0)
        prev_close = info.get("previousClose", price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return Quote(
            symbol=symbol,
            price=price,
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            volume=info.get("regularMarketVolume", 0),
            timestamp=datetime.now(),
            source="yfinance"
        )
    
    async def fetch_forex(self, pair: str) -> Forex:
        """Fetch forex pair."""
        # yfinance uses format like "USDJPY=X"
        yf_symbol = f"{pair}=X"
        yf = self._get_yf()
        
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
        info = await loop.run_in_executor(None, lambda: ticker.info)
        
        return Forex(
            pair=pair,
            rate=info.get("regularMarketPrice", 0),
            bid=info.get("bid"),
            ask=info.get("ask"),
            timestamp=datetime.now(),
            source="yfinance"
        )
