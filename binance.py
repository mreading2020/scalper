"""Binance API calls for futures data."""

import requests
from typing import List, Dict, Optional


BASE_URL = "https://fapi.binance.com"


def get_top_pairs(limit: int = 10) -> List[str]:
    """Return hardcoded clean watchlist (major liquid contracts)."""
    # Clean watchlist: majors only, no leverage/meme/distorted contracts
    watchlist = [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "LINKUSDT",
        "AVAXUSDT",
        "LTCUSDT",
    ]
    return watchlist[:limit]


def get_klines(symbol: str, interval: str = "5m", limit: int = 200) -> List[Dict]:
    """Fetch klines (candlesticks) from Binance."""
    try:
        resp = requests.get(
            f"{BASE_URL}/fapi/v1/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            },
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        # Convert to dict format
        candles = []
        for kline in data:
            candles.append({
                "open_time": int(kline[0]),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
            })

        return candles
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return []


def get_current_price(symbol: str) -> Optional[float]:
    """Get the current price of a symbol."""
    try:
        resp = requests.get(
            f"{BASE_URL}/fapi/v1/ticker/price",
            params={"symbol": symbol},
            timeout=10
        )
        resp.raise_for_status()
        return float(resp.json()["price"])
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None
