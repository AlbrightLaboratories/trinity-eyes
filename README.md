# Trinity Eyes 👁

**Resilient market data module with automatic fallbacks.**

Any agent can use Trinity Eyes to get global market data. She handles rate limits, outages, and provider failures automatically — you just ask for data.

## Features

- **Multi-provider fallback chains** — if one source fails, she tries the next
- **Unified interface** — same API regardless of underlying provider
- **Dual exposure** — use as MCP server OR REST API
- **Caching** — reduce API calls, respect rate limits
- **Free-first** — starts with free tiers, paid slots available

## Quick Start

### As Python Module
```python
from trinity_eyes import Eyes

eyes = Eyes()

# Get index price (she picks the best available source)
nikkei = await eyes.get_index("^N225")
print(f"Nikkei: {nikkei.close} ({nikkei.change_pct}%)")

# Get multiple at once
indices = await eyes.get_indices(["^N225", "^HSI", "^GDAXI", "^FTSE"])
```

### As MCP Server
```bash
# Start MCP server
trinity-eyes serve --mcp

# In Claude/Hermes, connect to:
# mcp://localhost:3847/trinity-eyes
```

### As REST API
```bash
# Start API server
trinity-eyes serve --api --port 8080

# GET /api/v1/index/^N225
# GET /api/v1/indices?symbols=^N225,^HSI,^GDAXI
# GET /api/v1/futures/ES=F
# GET /api/v1/forex/USDJPY
```

## Data Categories

| Category | Free Sources | Paid Slots |
|----------|--------------|------------|
| **Indices** | yfinance, Alpha Vantage, Finnhub | Twelve Data, Polygon |
| **Futures** | yfinance, Alpha Vantage | Twelve Data, Polygon |
| **Forex** | yfinance, Alpha Vantage, ECB | Twelve Data, OANDA |
| **Yields** | FRED, yfinance | — |
| **Economic** | Finnhub, FRED | — |
| **Sentiment** | Finnhub (free tier) | Finnhub Pro |

## Fallback Chain Example

When you request `^N225` (Nikkei 225):

```
1. Check cache (5 min TTL for indices)
   ↓ miss
2. Try yfinance
   ↓ rate limited
3. Try Alpha Vantage
   ↓ success → cache → return
```

If all free sources fail, she checks paid slots (if configured).

## Configuration

```yaml
# config/providers.yaml
providers:
  indices:
    chain:
      - name: yfinance
        type: free
        rate_limit: 2000/hour
      - name: alpha_vantage
        type: free
        rate_limit: 25/day  # free tier
        api_key: ${ALPHA_VANTAGE_API_KEY}
      - name: finnhub
        type: free
        rate_limit: 60/minute
        api_key: ${FINNHUB_API_KEY}
      - name: twelve_data
        type: paid
        enabled: false  # slot available
        api_key: ${TWELVE_DATA_API_KEY}

cache:
  backend: redis  # or "memory" for single-process
  ttl:
    indices: 300      # 5 min
    futures: 60       # 1 min
    forex: 60         # 1 min
    yields: 3600      # 1 hour
    economic: 86400   # 1 day
```

## For Trinity

Trinity Eyes is Trinity's data layer. She calls it to watch her 4 waves:

```python
# In Trinity's wave scheduler
from trinity_eyes import Eyes

eyes = Eyes()

# Wave 1: Oceania
oceania = await eyes.get_indices(["^NZ50", "^AXJO"])

# Wave 2: East Asia  
asia = await eyes.get_indices(["^N225", "^HSI", "000001.SS", "^KS11", "^STI"])

# Wave 3: Europe
europe = await eyes.get_indices(["^GDAXI", "^FTSE", "^STOXX50E"])

# Wave 4: US Pre-market
us_pre = await eyes.get_futures(["ES=F", "NQ=F", "YM=F"])
vix = await eyes.get_index("^VIX")
```

## For Other Agents

Any agent can use Trinity Eyes:

```python
# BrightEyes convergence checker
from trinity_eyes import Eyes

eyes = Eyes()
spy = await eyes.get_quote("SPY")
vix = await eyes.get_index("^VIX")

# Boardroom agent checking sector ETFs
xlk = await eyes.get_quote("XLK")  # Tech
xlu = await eyes.get_quote("XLU")  # Utilities
```

## MCP Tools

When running as MCP server, these tools are available:

| Tool | Description |
|------|-------------|
| `get_index` | Get current index value |
| `get_indices` | Get multiple indices |
| `get_quote` | Get stock/ETF quote |
| `get_futures` | Get futures prices |
| `get_forex` | Get currency pair |
| `get_yields` | Get treasury yields |
| `get_economic_calendar` | Get upcoming events |
| `provider_status` | Check which providers are healthy |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/index/{symbol}` | GET | Single index |
| `/api/v1/indices` | GET | Multiple indices |
| `/api/v1/quote/{symbol}` | GET | Stock/ETF quote |
| `/api/v1/futures/{symbol}` | GET | Futures price |
| `/api/v1/forex/{pair}` | GET | Currency pair |
| `/api/v1/yields` | GET | Treasury yields |
| `/api/v1/economic/calendar` | GET | Economic events |
| `/api/v1/health` | GET | Provider health |
| `/api/v1/providers` | GET | Provider status |

## Installation

```bash
pip install trinity-eyes

# Or from source
git clone git@github.com:AlbrightLaboratories/trinity-eyes.git
cd trinity-eyes
pip install -e .
```

## Environment Variables

```bash
# Optional - only needed if using these providers
ALPHA_VANTAGE_API_KEY=your_key    # Free: alphavantage.co
FINNHUB_API_KEY=your_key          # Free: finnhub.io
FRED_API_KEY=your_key             # Free: fred.stlouisfed.org

# Paid slots (disabled by default)
TWELVE_DATA_API_KEY=your_key      # twelvedata.com
POLYGON_API_KEY=your_key          # polygon.io
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      TRINITY EYES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │   MCP   │  │   API   │  │ Python  │   ← Interfaces      │
│  │ Server  │  │ Server  │  │ Module  │                     │
│  └────┬────┘  └────┬────┘  └────┬────┘                     │
│       │            │            │                           │
│       └────────────┴────────────┘                           │
│                    │                                        │
│            ┌───────▼───────┐                               │
│            │   Data Layer  │                               │
│            │  (unified)    │                               │
│            └───────┬───────┘                               │
│                    │                                        │
│            ┌───────▼───────┐                               │
│            │  Cache Layer  │   ← Redis or Memory           │
│            └───────┬───────┘                               │
│                    │                                        │
│            ┌───────▼───────┐                               │
│            │ Fallback Chain│   ← Automatic failover        │
│            └───────┬───────┘                               │
│                    │                                        │
│  ┌─────────────────┼─────────────────────────────────────┐ │
│  │                 │          PROVIDERS                   │ │
│  │  ┌──────┐  ┌────┴───┐  ┌────────┐  ┌────────┐        │ │
│  │  │yfin  │  │Alpha V │  │Finnhub │  │  FRED  │  FREE  │ │
│  │  └──────┘  └────────┘  └────────┘  └────────┘        │ │
│  │  ┌──────┐  ┌────────┐  ┌────────┐                    │ │
│  │  │12Data│  │Polygon │  │ OANDA  │  PAID (slots)      │ │
│  │  └──────┘  └────────┘  └────────┘                    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT — Use freely, contribute back.
