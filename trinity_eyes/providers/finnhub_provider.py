"""Finnhub provider - free tier with economic calendar."""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional

from .base import BaseProvider
from ..models import Index, EconomicEvent


class FinnhubProvider(BaseProvider):
    """
    Finnhub API.
    
    Free tier: 60 requests/minute
    Good for: Economic calendar, news sentiment
    """
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def fetch(self, symbol: str) -> Index:
        """Fetch quote data."""
        if not self.api_key:
            raise ValueError("Finnhub API key not configured")
        
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/quote"
        params = {"symbol": symbol, "token": self.api_key}
        
        async with session.get(url, params=params) as resp:
            data = await resp.json()
        
        if "c" not in data:
            raise ValueError(f"Invalid response: {data}")
        
        price = data["c"]  # current
        prev = data["pc"]  # previous close
        change = price - prev
        change_pct = (change / prev * 100) if prev else 0
        
        return Index(
            symbol=symbol,
            name=symbol,
            close=price,
            change=round(change, 2),
            change_pct=round(change_pct, 2),
            timestamp=datetime.now(),
            source="finnhub"
        )
    
    async def fetch_calendar(self, days_ahead: int = 7) -> List[EconomicEvent]:
        """Fetch economic calendar."""
        if not self.api_key:
            raise ValueError("Finnhub API key not configured")
        
        session = await self._get_session()
        
        from_date = datetime.now().strftime("%Y-%m-%d")
        to_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/calendar/economic"
        params = {
            "from": from_date,
            "to": to_date,
            "token": self.api_key
        }
        
        async with session.get(url, params=params) as resp:
            data = await resp.json()
        
        events = []
        for item in data.get("economicCalendar", []):
            events.append(EconomicEvent(
                date=datetime.fromisoformat(item["time"].replace("Z", "+00:00")),
                event=item.get("event", ""),
                country=item.get("country", ""),
                impact=item.get("impact", "low"),
                actual=item.get("actual"),
                forecast=item.get("estimate"),
                previous=item.get("prev"),
            ))
        
        return events
    
    async def close(self):
        if self._session:
            await self._session.close()
