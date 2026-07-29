from __future__ import annotations

from typing import Any

def fetch_stock_price(symbol: str) -> dict[str, Any]:
    sym = symbol.strip().upper()
    
    # Mock stock/crypto database for self-contained robustness
    database = {
        "AAPL": {"price": 180.50, "change": "+1.2%", "company": "Apple Inc."},
        "TSLA": {"price": 220.30, "change": "-0.5%", "company": "Tesla Inc."},
        "MSFT": {"price": 415.80, "change": "+0.8%", "company": "Microsoft Corporation"},
        "GOOG": {"price": 150.20, "change": "+1.5%", "company": "Alphabet Inc."},
        "BTC": {"price": 65000.00, "change": "+3.4%", "company": "Bitcoin"}
    }
    
    if sym in database:
        res = database[sym]
        return {
            "tool": "stock",
            "symbol": sym,
            "company": res["company"],
            "price": res["price"],
            "change": res["change"]
        }
    else:
        return {
            "tool": "stock",
            "symbol": sym,
            "company": f"Ticker ({sym})",
            "price": 100.00,
            "change": "+0.0%"
        }
