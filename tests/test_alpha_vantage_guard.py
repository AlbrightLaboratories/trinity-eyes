"""Alpha Vantage fallback guard (Trinity #2205).

Alpha Vantage GLOBAL_QUOTE only serves US-listed tickers. Index (^N225),
futures (ES=F) and non-US (000001.SS) symbols must be refused before any
network call so the free 25/day quota is not spent on them.
"""

import pytest
from trinity_eyes.providers.alpha_vantage import AlphaVantageProvider, UnsupportedSymbolError


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._payload


class _Session:
    def __init__(self, payload=None):
        self.calls = []
        self._payload = payload or {}
        self.closed = False

    def get(self, url, params=None):
        self.calls.append(params)
        return _Resp(self._payload)


def _provider(session):
    p = AlphaVantageProvider({"name": "alpha_vantage", "api_key": "test-key"})

    async def _get_session():
        return session

    p._get_session = _get_session
    return p


@pytest.mark.asyncio
@pytest.mark.parametrize("symbol", ["^N225", "^GDAXI", "ES=F", "000001.SS"])
async def test_non_us_symbol_is_refused_without_network(symbol):
    session = _Session()
    with pytest.raises(UnsupportedSymbolError):
        await _provider(session).fetch(symbol)
    assert session.calls == [], "must not spend an Alpha Vantage request on an unsupported symbol"


@pytest.mark.asyncio
async def test_us_ticker_calls_global_quote():
    session = _Session({"Global Quote": {
        "05. price": "730.2500", "09. change": "1.5000", "10. change percent": "0.2%"}})
    result = await _provider(session).fetch("SPY")
    assert session.calls == [{"function": "GLOBAL_QUOTE", "symbol": "SPY", "apikey": "test-key"}]
    assert result.close == pytest.approx(730.25)
    assert result.source == "alpha_vantage"
