"""Trinity Eyes CLI."""

import asyncio
import argparse
import json
from dataclasses import asdict


def main():
    parser = argparse.ArgumentParser(description="Trinity Eyes - Market Data")
    subparsers = parser.add_subparsers(dest="command")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start server")
    serve_parser.add_argument("--mcp", action="store_true", help="Run MCP server")
    serve_parser.add_argument("--api", action="store_true", help="Run REST API")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port (default 8080)")
    
    # Query commands
    index_parser = subparsers.add_parser("index", help="Get index")
    index_parser.add_argument("symbol", help="Index symbol (e.g., ^N225)")
    
    quote_parser = subparsers.add_parser("quote", help="Get quote")
    quote_parser.add_argument("symbol", help="Stock/ETF symbol")
    
    forex_parser = subparsers.add_parser("forex", help="Get forex pair")
    forex_parser.add_argument("pair", help="Currency pair (e.g., USDJPY)")
    
    yields_parser = subparsers.add_parser("yields", help="Get treasury yields")
    
    status_parser = subparsers.add_parser("status", help="Provider status")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        if args.mcp:
            from mcp.server import TrinityEyesMCP
            server = TrinityEyesMCP()
            asyncio.run(server.run(port=args.port))
        elif args.api:
            from api.server import run
            run(port=args.port)
        else:
            print("Specify --mcp or --api")
            
    elif args.command == "index":
        from src import Eyes
        eyes = Eyes()
        result = asyncio.run(eyes.get_index(args.symbol))
        print(json.dumps(asdict(result), indent=2, default=str))
        
    elif args.command == "quote":
        from src import Eyes
        eyes = Eyes()
        result = asyncio.run(eyes.get_quote(args.symbol))
        print(json.dumps(asdict(result), indent=2, default=str))
        
    elif args.command == "forex":
        from src import Eyes
        eyes = Eyes()
        result = asyncio.run(eyes.get_forex(args.pair))
        print(json.dumps(asdict(result), indent=2, default=str))
        
    elif args.command == "yields":
        from src import Eyes
        eyes = Eyes()
        result = asyncio.run(eyes.get_yields())
        print(json.dumps(asdict(result), indent=2, default=str))
        
    elif args.command == "status":
        from src import Eyes
        eyes = Eyes()
        result = asyncio.run(eyes.provider_status())
        print(json.dumps(result, indent=2, default=str))
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
