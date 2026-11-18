"""ECB provider - European Central Bank exchange rates."""

import aiohttp
from datetime import datetime
from typing import Optional

from .base import BaseProvider
from ..models import Forex


class ECBProvider(BaseProvider):
    """
    ECB Exchange Rates - Free, official EUR rates.
    
    Updates daily at 16:00 CET
    """
    
    URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._rates_cache: dict = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _load_rates(self):
        """Load ECB rates XML."""
        import xml.etree.ElementTree as ET
        
        session = await self._get_session()
        async with session.get(self.URL) as resp:
            text = await resp.text()
        
        root = ET.fromstring(text)
        ns = {"gesmes": "http://www.gesmes.org/xml/2002-08-01",
              "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
        
        cube = root.find(".//eurofxref:Cube/eurofxref:Cube", ns)
        if cube is None:
            return
        
        self._rates_cache["EUR"] = 1.0
        for rate in cube.findall("eurofxref:Cube", ns):
            currency = rate.get("currency")
            value = float(rate.get("rate"))
            self._rates_cache[currency] = value
    
    async def fetch(self, pair: str) -> Forex:
        """Fetch currency pair rate."""
        if not self._rates_cache:
            await self._load_rates()
        
        # Parse pair like "USDJPY" or "EURUSD"
        base = pair[:3]
        quote = pair[3:]
        
        # ECB provides rates relative to EUR
        base_rate = self._rates_cache.get(base, 1.0)
        quote_rate = self._rates_cache.get(quote, 1.0)
        
        # Calculate cross rate
        rate = quote_rate / base_rate
        
        return Forex(
            pair=pair,
            rate=round(rate, 4),
            bid=None,
            ask=None,
            timestamp=datetime.now(),
            source="ecb"
        )
    
    async def close(self):
        if self._session:
            await self._session.close()
