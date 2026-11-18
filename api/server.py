"""Trinity Eyes REST API Server.

FastAPI-based REST interface for Eyes.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from dataclasses import asdict
import uvicorn

import sys
sys.path.insert(0, '..')
from src import Eyes


app = FastAPI(
    title="Trinity Eyes API",
    description="Resilient market data with automatic fallbacks",
    version="0.1.0"
)

# Global Eyes instance
eyes: Optional[Eyes] = None


@app.on_event("startup")
async def startup():
    global eyes
    eyes = Eyes()


@app.on_event("shutdown")
async def shutdown():
    if eyes:
        await eyes.close()


# === INDEX ENDPOINTS ===

@app.get("/api/v1/index/{symbol}")
async def get_index(symbol: str):
    """Get current index value."""
    try:
        result = await eyes.get_index(symbol)
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/indices")
async def get_indices(symbols: str = Query(..., description="Comma-separated symbols")):
    """Get multiple indices."""
    try:
        symbol_list = [s.strip() for s in symbols.split(",")]
        results = await eyes.get_indices(symbol_list)
        return {k: asdict(v) for k, v in results.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === QUOTE ENDPOINTS ===

@app.get("/api/v1/quote/{symbol}")
async def get_quote(symbol: str):
    """Get stock/ETF quote."""
    try:
        result = await eyes.get_quote(symbol)
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === FUTURES ENDPOINTS ===

@app.get("/api/v1/futures/{symbol}")
async def get_futures(symbol: str):
    """Get futures contract price."""
    try:
        result = await eyes.get_futures(symbol)
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === FOREX ENDPOINTS ===

@app.get("/api/v1/forex/{pair}")
async def get_forex(pair: str):
    """Get currency pair rate."""
    try:
        result = await eyes.get_forex(pair)
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === YIELDS ENDPOINTS ===

@app.get("/api/v1/yields")
async def get_yields():
    """Get US Treasury yields."""
    try:
        result = await eyes.get_yields()
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ECONOMIC ENDPOINTS ===

@app.get("/api/v1/economic/calendar")
async def get_economic_calendar(
    days_ahead: int = Query(7, description="Days to look ahead"),
    impact: Optional[str] = Query(None, description="Filter by impact: high, medium, low")
):
    """Get upcoming economic events."""
    try:
        results = await eyes.get_economic_calendar(days_ahead, impact)
        return [asdict(e) for e in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === HEALTH ENDPOINTS ===

@app.get("/api/v1/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "trinity-eyes"}


@app.get("/api/v1/providers")
async def provider_status():
    """Get provider health status."""
    try:
        status = await eyes.provider_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run(host: str = "0.0.0.0", port: int = 8080):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
