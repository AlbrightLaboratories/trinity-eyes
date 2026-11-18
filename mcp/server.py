"""Trinity Eyes MCP Server.

Exposes Eyes as MCP tools for Claude/Hermes agents.
"""

import asyncio
import json
from typing import Any, Dict, List

# MCP protocol imports (using mcp-server-python or similar)
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

import sys
sys.path.insert(0, '..')
from src import Eyes


class TrinityEyesMCP:
    """MCP Server wrapper for Trinity Eyes."""
    
    def __init__(self):
        self.eyes = Eyes()
        self.server = Server("trinity-eyes") if HAS_MCP else None
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Define MCP tools."""
        return [
            {
                "name": "get_index",
                "description": "Get current index value (e.g., ^N225, ^GDAXI, ^VIX)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Index symbol (e.g., ^N225 for Nikkei)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_indices",
                "description": "Get multiple indices at once",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of index symbols"
                        }
                    },
                    "required": ["symbols"]
                }
            },
            {
                "name": "get_quote",
                "description": "Get stock/ETF quote",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock/ETF symbol (e.g., AAPL, SPY)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_futures",
                "description": "Get futures contract price (e.g., ES=F, NQ=F)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Futures symbol (e.g., ES=F for S&P futures)"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_forex",
                "description": "Get currency pair rate",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pair": {
                            "type": "string",
                            "description": "Currency pair (e.g., USDJPY, EURUSD)"
                        }
                    },
                    "required": ["pair"]
                }
            },
            {
                "name": "get_yields",
                "description": "Get US Treasury yields (2Y, 10Y, 30Y, spread)",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_economic_calendar",
                "description": "Get upcoming economic events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days_ahead": {
                            "type": "integer",
                            "description": "Days to look ahead (default 7)"
                        },
                        "impact": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Filter by impact level"
                        }
                    }
                }
            },
            {
                "name": "provider_status",
                "description": "Check health status of data providers",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_tool(self, name: str, arguments: dict) -> str:
        """Handle tool invocation."""
        from dataclasses import asdict
        
        if name == "get_index":
            result = await self.eyes.get_index(arguments["symbol"])
            return json.dumps(asdict(result), default=str)
        
        elif name == "get_indices":
            results = await self.eyes.get_indices(arguments["symbols"])
            return json.dumps({k: asdict(v) for k, v in results.items()}, default=str)
        
        elif name == "get_quote":
            result = await self.eyes.get_quote(arguments["symbol"])
            return json.dumps(asdict(result), default=str)
        
        elif name == "get_futures":
            result = await self.eyes.get_futures(arguments["symbol"])
            return json.dumps(asdict(result), default=str)
        
        elif name == "get_forex":
            result = await self.eyes.get_forex(arguments["pair"])
            return json.dumps(asdict(result), default=str)
        
        elif name == "get_yields":
            result = await self.eyes.get_yields()
            return json.dumps(asdict(result), default=str)
        
        elif name == "get_economic_calendar":
            days = arguments.get("days_ahead", 7)
            impact = arguments.get("impact")
            results = await self.eyes.get_economic_calendar(days, impact)
            return json.dumps([asdict(e) for e in results], default=str)
        
        elif name == "provider_status":
            status = await self.eyes.provider_status()
            return json.dumps(status, default=str)
        
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
    
    async def run(self, port: int = 3847):
        """Run MCP server."""
        if not HAS_MCP:
            print("MCP server library not installed. Install with: pip install mcp-server-python")
            return
        
        # Register tools
        @self.server.list_tools()
        async def list_tools():
            return self.get_tools()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            result = await self.handle_tool(name, arguments)
            return [TextContent(type="text", text=result)]
        
        # Run server
        print(f"Trinity Eyes MCP server running on port {port}")
        await self.server.run()


async def main():
    server = TrinityEyesMCP()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
