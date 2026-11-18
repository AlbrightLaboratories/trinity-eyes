"""Trinity Eyes - Resilient market data with automatic fallbacks."""

from .eyes import Eyes
from .models import Quote, Index, Futures, Forex, Yields

__version__ = "0.1.0"
__all__ = ["Eyes", "Quote", "Index", "Futures", "Forex", "Yields"]
