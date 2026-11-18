"""Provider chain with automatic fallbacks."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProviderChain:
    """
    Fallback chain of data providers.
    
    Tries each provider in order until one succeeds.
    Tracks health and rate limits per provider.
    """
    
    def __init__(self, category: str, chain_config: List[dict]):
        self.category = category
        self.providers = self._init_providers(chain_config)
        self._failures: Dict[str, int] = {}  # provider -> consecutive failures
        self._last_success: Dict[str, datetime] = {}
    
    def _init_providers(self, config: List[dict]) -> List['BaseProvider']:
        """Initialize provider instances from config."""
        from .yfinance_provider import YFinanceProvider
        from .alpha_vantage import AlphaVantageProvider
        from .finnhub_provider import FinnhubProvider
        from .fred_provider import FREDProvider
        from .twelve_data import TwelveDataProvider
        from .ecb_provider import ECBProvider
        
        provider_map = {
            "yfinance": YFinanceProvider,
            "alpha_vantage": AlphaVantageProvider,
            "finnhub": FinnhubProvider,
            "fred": FREDProvider,
            "twelve_data": TwelveDataProvider,
            "ecb": ECBProvider,
        }
        
        providers = []
        for cfg in config:
            name = cfg.get("name")
            if name not in provider_map:
                logger.warning(f"Unknown provider: {name}")
                continue
            
            # Skip disabled providers (paid slots not configured)
            if not cfg.get("enabled", True):
                logger.info(f"Provider {name} disabled (paid slot available)")
                continue
            
            try:
                provider = provider_map[name](cfg)
                providers.append(provider)
                logger.info(f"Initialized provider: {name} ({cfg.get('type', 'free')})")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
        
        return providers
    
    async def fetch(self, symbol: str) -> Any:
        """
        Fetch data with automatic fallback.
        
        Tries each provider in order until one succeeds.
        """
        errors = []
        
        for provider in self.providers:
            try:
                # Check if provider is healthy
                if self._failures.get(provider.name, 0) > 5:
                    # Skip providers with too many consecutive failures
                    # But reset after 5 minutes
                    last = self._last_success.get(provider.name)
                    if last and (datetime.now() - last).seconds < 300:
                        logger.debug(f"Skipping {provider.name} (too many failures)")
                        continue
                    else:
                        # Reset and try again
                        self._failures[provider.name] = 0
                
                result = await provider.fetch(symbol)
                
                # Success - reset failure counter
                self._failures[provider.name] = 0
                self._last_success[provider.name] = datetime.now()
                
                logger.debug(f"Got {symbol} from {provider.name}")
                return result
                
            except Exception as e:
                # Track failure
                self._failures[provider.name] = self._failures.get(provider.name, 0) + 1
                errors.append(f"{provider.name}: {e}")
                logger.warning(f"Provider {provider.name} failed for {symbol}: {e}")
                continue
        
        # All providers failed
        raise RuntimeError(
            f"All providers failed for {symbol}. Errors: {'; '.join(errors)}"
        )
    
    async def fetch_quote(self, symbol: str) -> Any:
        """Fetch quote data with fallback."""
        errors = []
        
        for provider in self.providers:
            if not hasattr(provider, 'fetch_quote'):
                continue
            try:
                result = await provider.fetch_quote(symbol)
                self._failures[provider.name] = 0
                return result
            except Exception as e:
                self._failures[provider.name] = self._failures.get(provider.name, 0) + 1
                errors.append(f"{provider.name}: {e}")
                continue
        
        raise RuntimeError(f"All providers failed for quote {symbol}")
    
    async def fetch_forex(self, pair: str) -> Any:
        """Fetch forex data with fallback."""
        errors = []
        
        for provider in self.providers:
            if not hasattr(provider, 'fetch_forex'):
                continue
            try:
                result = await provider.fetch_forex(pair)
                self._failures[provider.name] = 0
                return result
            except Exception as e:
                self._failures[provider.name] = self._failures.get(provider.name, 0) + 1
                errors.append(f"{provider.name}: {e}")
                continue
        
        raise RuntimeError(f"All providers failed for forex {pair}")
    
    async def fetch_calendar(self, days_ahead: int) -> List[Any]:
        """Fetch economic calendar with fallback."""
        for provider in self.providers:
            if not hasattr(provider, 'fetch_calendar'):
                continue
            try:
                return await provider.fetch_calendar(days_ahead)
            except Exception as e:
                logger.warning(f"Calendar fetch failed from {provider.name}: {e}")
                continue
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers in chain."""
        status = {}
        for provider in self.providers:
            status[provider.name] = {
                "healthy": self._failures.get(provider.name, 0) < 3,
                "consecutive_failures": self._failures.get(provider.name, 0),
                "last_success": self._last_success.get(provider.name),
                "type": provider.provider_type,
            }
        return status
    
    async def close(self):
        """Clean up provider resources."""
        for provider in self.providers:
            if hasattr(provider, 'close'):
                await provider.close()
