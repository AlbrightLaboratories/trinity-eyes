"""Integration tests for trinity-eyes."""

import asyncio
import pytest
from trinity_eyes import Eyes
from trinity_eyes.models import Index, Forex


@pytest.fixture
def eyes():
    """Create Eyes instance."""
    return Eyes()


class TestEyes:
    """Test Eyes class methods."""
    
    def test_eyes_creation(self, eyes):
        """Eyes should initialize without error."""
        assert eyes is not None
        assert hasattr(eyes, 'get_index')
        assert hasattr(eyes, 'get_forex')
        assert hasattr(eyes, 'get_indices')
    
    @pytest.mark.asyncio
    async def test_get_index_nikkei(self, eyes):
        """Should fetch Nikkei 225."""
        result = await eyes.get_index("^N225")
        assert isinstance(result, Index)
        assert result.symbol == "^N225"
        assert result.close > 0
        assert result.source == "yfinance"
    
    @pytest.mark.asyncio
    async def test_get_index_sp500(self, eyes):
        """Should fetch S&P 500."""
        result = await eyes.get_index("^GSPC")
        assert isinstance(result, Index)
        assert result.symbol == "^GSPC"
        assert result.close > 0
    
    @pytest.mark.asyncio
    async def test_get_forex_eurusd(self, eyes):
        """Should fetch EUR/USD."""
        result = await eyes.get_forex("EURUSD")
        assert isinstance(result, Forex)
        assert result.pair == "EURUSD"
        assert result.rate > 0  # Should be ~1.05-1.15
    
    @pytest.mark.asyncio
    async def test_get_forex_usdjpy(self, eyes):
        """Should fetch USD/JPY."""
        result = await eyes.get_forex("USDJPY")
        assert isinstance(result, Forex)
        assert result.pair == "USDJPY"
        assert result.rate > 100  # Should be ~140-160
    
    @pytest.mark.asyncio
    async def test_get_indices_multiple(self, eyes):
        """Should fetch multiple indices."""
        symbols = ["^N225", "^HSI", "^GSPC"]
        results = await eyes.get_indices(symbols)
        
        # Returns a dict of symbol -> Index
        assert len(results) == 3
        for symbol, idx in results.items():
            assert isinstance(idx, Index)
            assert idx.close > 0


class TestProviderFallback:
    """Test provider fallback behavior."""
    
    @pytest.mark.asyncio
    async def test_invalid_symbol_returns_zero(self, eyes):
        """Invalid symbol should return 0 price (yfinance behavior)."""
        # yfinance doesn't raise on invalid symbols, returns empty/zero
        result = await eyes.get_index("INVALID_SYMBOL_XYZ123")
        # This is yfinance behavior - returns Index with 0 values
        assert isinstance(result, Index)
        assert result.close == 0  # yfinance returns 0 for invalid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
