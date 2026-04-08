"""Main runner: scan pairs and output signals."""

import sys
from typing import List, Dict, Optional
import binance
import strategy
import filters
import risk


def round_price(price: float, symbol: str) -> str:
    """Round price based on symbol (Bitcoin, Altcoin, etc.)."""
    # For most pairs, 2-4 decimals is fine
    if price > 10000:
        return f"{price:.2f}"
    elif price > 100:
        return f"{price:.4f}"
    else:
        return f"{price:.6f}"


def analyze_pair(symbol: str) -> Optional[Dict]:
    """Analyze a single pair and return signal data or None if NO TRADE."""
    candles = binance.get_klines(symbol, interval="5m", limit=200)
    if not candles or len(candles) < 20:
        return None

    current_price = binance.get_current_price(symbol)
    if current_price is None:
        return None

    # Detect trend
    is_up = strategy.is_uptrend(candles)
    is_down = strategy.is_downtrend(candles)

    if not is_up and not is_down:
        return {
            "symbol": symbol,
            "signal": "NO TRADE",
            "entry": None,
            "sl": None,
            "tp": None,
            "risk_pct": None,
            "reason": "no trend"
        }

    # Check pullback
    if is_up and strategy.has_long_pullback(candles):
        # LONG setup
        entry = risk.calculate_long_entry(candles)
        sl = risk.calculate_long_sl(candles)
        tp = risk.calculate_long_tp(entry, sl)
        risk_pct = risk.calculate_risk_percent(entry, sl, current_price)

        # Validate setup
        if not risk.is_valid_long_setup(entry, sl, current_price):
            return {
                "symbol": symbol,
                "signal": "NO TRADE",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": "invalid long setup"
            }

        # Run filters
        should_skip, skip_reason = filters.check_all_filters(
            symbol, candles, current_price, entry, is_long=True, risk_pct=risk_pct
        )

        if should_skip:
            return {
                "symbol": symbol,
                "signal": "SKIP",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": skip_reason
            }

        return {
            "symbol": symbol,
            "signal": "LONG",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "risk_pct": risk_pct,
            "reason": "pullback + breakout"
        }

    elif is_down and strategy.has_short_pullback(candles):
        # SHORT setup
        entry = risk.calculate_short_entry(candles)
        sl = risk.calculate_short_sl(candles)
        tp = risk.calculate_short_tp(entry, sl)
        risk_pct = risk.calculate_risk_percent(entry, sl, current_price)

        # Validate setup
        if not risk.is_valid_short_setup(entry, sl, current_price):
            return {
                "symbol": symbol,
                "signal": "NO TRADE",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": "invalid short setup"
            }

        # Run filters
        should_skip, skip_reason = filters.check_all_filters(
            symbol, candles, current_price, entry, is_long=False, risk_pct=risk_pct
        )

        if should_skip:
            return {
                "symbol": symbol,
                "signal": "SKIP",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": skip_reason
            }

        return {
            "symbol": symbol,
            "signal": "SHORT",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "risk_pct": risk_pct,
            "reason": "pullback + breakdown"
        }

    else:
        # Trend exists but no valid pullback
        return {
            "symbol": symbol,
            "signal": "NO TRADE",
            "entry": None,
            "sl": None,
            "tp": None,
            "risk_pct": None,
            "reason": "no pullback"
        }


def format_output(results: List[Dict]) -> None:
    """Format and print results with clean alignment."""
    # Sort: LONG/SHORT first, then SKIP, then NO TRADE
    priority = {"LONG": 0, "SHORT": 1, "SKIP": 2, "NO TRADE": 3}
    results.sort(key=lambda x: priority.get(x["signal"], 4))

    print("\n" + "=" * 120)
    print(f"{'SYMBOL':<10} {'SIGNAL':<10} {'ENTRY':<15} {'SL':<15} {'TP':<15} {'RISK':<10} REASON")
    print("=" * 120)

    for result in results:
        symbol = result["symbol"]
        signal = result["signal"]
        reason = result["reason"]

        if signal in ("LONG", "SHORT"):
            entry = round_price(result["entry"], symbol)
            sl = round_price(result["sl"], symbol)
            tp = round_price(result["tp"], symbol)
            risk_str = f"{result['risk_pct']:.2f}%"
            print(
                f"{symbol:<10} {signal:<10} {entry:<15} {sl:<15} {tp:<15} {risk_str:<10} {reason}"
            )
        else:
            print(f"{symbol:<10} {signal:<10} {'-':<15} {'-':<15} {'-':<15} {'-':<10} {reason}")

    print("=" * 120 + "\n")


def main():
    """Main scan loop."""
    pairs = binance.get_top_pairs(limit=10)

    if not pairs:
        print("Error: Could not fetch pairs.")
        sys.exit(1)

    print(f"Scanning {len(pairs)} pairs on 5m timeframe...\n")

    results = []
    for symbol in pairs:
        result = analyze_pair(symbol)
        if result:
            results.append(result)

    format_output(results)


if __name__ == "__main__":
    main()
