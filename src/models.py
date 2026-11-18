"""Data models for market data."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Quote:
    """Stock/ETF quote."""
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: int
    timestamp: datetime
    source: str  # which provider returned this

@dataclass(frozen=True)
class Index:
    """Index value."""
    symbol: str
    name: str
    close: float
    change: float
    change_pct: float
    timestamp: datetime
    source: str

@dataclass(frozen=True)
class Futures:
    """Futures contract."""
    symbol: str
    price: float
    change: float
    change_pct: float
    expiry: Optional[str]
    timestamp: datetime
    source: str

@dataclass(frozen=True)
class Forex:
    """Currency pair."""
    pair: str
    rate: float
    bid: Optional[float]
    ask: Optional[float]
    timestamp: datetime
    source: str

@dataclass(frozen=True)
class Yields:
    """Treasury yields."""
    us_2y: float
    us_10y: float
    us_30y: Optional[float]
    spread_2_10: float  # 10y - 2y
    timestamp: datetime
    source: str

@dataclass(frozen=True)
class EconomicEvent:
    """Economic calendar event."""
    date: datetime
    event: str
    country: str
    impact: str  # low, medium, high
    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
