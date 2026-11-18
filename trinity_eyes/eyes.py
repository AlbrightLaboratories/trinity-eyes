"""Trinity Eyes - Main interface for market data."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import Quote, Index, Futures, Forex, Yields, EconomicEvent
from .providers import ProviderChain
from .cache import Cache

logger = logging.getLogger(__name__)


class Eyes:
    """
    Resilient market data interface with automatic fallbacks.
    
    Usage:
        eyes = Eyes()
        nikkei = await eyes.get_index("^N225")
        indices = await eyes.get_indices(["^N225", "^HSI", "^GDAXI"])
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Eyes with optional config.
        
        Args:
            config_path: Path to providers.yaml. If None, uses defaults.
        """
        self.config = self._load_config(config_path)
        self.cache = Cache(self.config.get("cache", {}))
        self.chains = self._init_chains()
        self._health: Dict[str, bool] = {}
    
    def _load_config(self, path: Optional[str]) -> dict:
        """Load config from file or use defaults."""
        if path:
            import yaml
            with open(path) as f:
                return yaml.safe_load(f)
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Default free-tier config."""
        return {
            "providers": {
                "indices": {
                    "chain": [
                        {"name": "yfinance", "type": "free"},
                        {"name": "alpha_vantage", "type": "free"},
                        {"name": "finnhub", "type": "free"},
                    ]
                },
                "futures": {
                    "chain": [
                        {"name": "yfinance", "type": "free"},
                        {"name": "alpha_vantage", "type": "free"},
                    ]
                },
                "forex": {
                    "chain": [
                        {"name": "yfinance", "type": "free"},
                        {"name": "alpha_vantage", "type": "free"},
                        {"name": "ecb", "type": "free"},
                    ]
                },
                "yields": {
                    "chain": [
                        {"name": "fred", "type": "free"},
                        {"name": "yfinance", "type": "free"},
                    ]
                },
                "economic": {
                    "chain": [
                        {"name": "finnhub", "type": "free"},
                        {"name": "fred", "type": "free"},
                    ]
                },
            },
            "cache": {
                "backend": "memory",
                "ttl": {
                    "indices": 300,
                    "futures": 60,
                    "forex": 60,
                    "yields": 3600,
                    "economic": 86400,
                }
            }
        }
    
    def _init_chains(self) -> Dict[str, ProviderChain]:
        """Initialize fallback chains for each data category."""
        chains = {}
        for category, cfg in self.config.get("providers", {}).items():
            chains[category] = ProviderChain(category, cfg.get("chain", []))
        return chains
    
    # === INDEX DATA ===
    
    async def get_index(self, symbol: str) -> Index:
        """
        Get current index value.
        
        Args:
            symbol: Index symbol (e.g., "^N225", "^GDAXI", "^VIX")
        
        Returns:
            Index with current value, change, source
        """
        # Check cache
        cached = await self.cache.get("indices", symbol)
        if cached:
            return cached
        
        # Try fallback chain
        chain = self.chains.get("indices")
        if not chain:
            raise ValueError("No providers configured for indices")
        
        result = await chain.fetch(symbol)
        
        # Cache result
        await self.cache.set("indices", symbol, result)
        
        return result
    
    async def get_indices(self, symbols: List[str]) -> Dict[str, Index]:
        """Get multiple indices at once."""
        tasks = [self.get_index(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            symbols[i]: r for i, r in enumerate(results) 
            if not isinstance(r, Exception)
        }
    
    # === FUTURES DATA ===
    
    async def get_futures(self, symbol: str) -> Futures:
        """Get futures contract price."""
        cached = await self.cache.get("futures", symbol)
        if cached:
            return cached
        
        chain = self.chains.get("futures")
        result = await chain.fetch(symbol)
        await self.cache.set("futures", symbol, result)
        return result
    
    async def get_futures_batch(self, symbols: List[str]) -> Dict[str, Futures]:
        """Get multiple futures at once."""
        tasks = [self.get_futures(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            symbols[i]: r for i, r in enumerate(results)
            if not isinstance(r, Exception)
        }
    
    # === QUOTE DATA ===
    
    async def get_quote(self, symbol: str) -> Quote:
        """Get stock/ETF quote."""
        cached = await self.cache.get("quotes", symbol)
        if cached:
            return cached
        
        chain = self.chains.get("indices")  # Same providers work for quotes
        result = await chain.fetch_quote(symbol)
        await self.cache.set("quotes", symbol, result)
        return result
    
    # === FOREX DATA ===
    
    async def get_forex(self, pair: str) -> Forex:
        """
        Get currency pair rate.
        
        Args:
            pair: Currency pair (e.g., "USDJPY", "EURUSD")
        """
        cached = await self.cache.get("forex", pair)
        if cached:
            return cached
        
        chain = self.chains.get("forex")
        result = await chain.fetch_forex(pair)
        await self.cache.set("forex", pair, result)
        return result
    
    # === YIELDS DATA ===
    
    async def get_yields(self) -> Yields:
        """Get current US Treasury yields."""
        cached = await self.cache.get("yields", "us_treasury")
        if cached:
            return cached
        
        chain = self.chains.get("yields")
        result = await chain.fetch("us_treasury")
        await self.cache.set("yields", "us_treasury", result)
        return result
    
    # === ECONOMIC DATA ===
    
    async def get_economic_calendar(
        self, 
        days_ahead: int = 7,
        impact: Optional[str] = None  # "high", "medium", "low"
    ) -> List[EconomicEvent]:
        """Get upcoming economic events."""
        chain = self.chains.get("economic")
        events = await chain.fetch_calendar(days_ahead)
        
        if impact:
            events = [e for e in events if e.impact == impact]
        
        return events
    
    # === HEALTH & STATUS ===
    
    async def provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all providers."""
        status = {}
        for category, chain in self.chains.items():
            status[category] = await chain.health_check()
        return status
    
    async def close(self):
        """Clean up resources."""
        await self.cache.close()
        for chain in self.chains.values():
            await chain.close()
