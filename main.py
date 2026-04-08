"""Main runner: scan pairs and output signals (exact specification)."""

import sys
from typing import List, Dict, Optional
import binance
import strategy
import filters
import scoring


def round_price(price: float) -> str:
    """Round price appropriately."""
    if price > 10000:
        return f"{price:.2f}"
    elif price > 100:
        return f"{price:.4f}"
    else:
        return f"{price:.6f}"


def analyze_pair(symbol: str) -> Optional[Dict]:
    """Analyze a single pair. Returns signal data or None."""
    klines = binance.get_klines(symbol, interval="5m", limit=200)
    if not klines or len(klines) < 20:
        return None

    # Use only closed candles (exclude current live candle)
    candles = strategy.get_closed_candles(klines)
    if len(candles) < 12:
        return None

    # Detect trend
    trend_up, trend_down = strategy.detect_trend(candles)

    if not trend_up and not trend_down:
        return {
            "symbol": symbol,
            "signal": "NO TRADE",
            "entry": None,
            "sl": None,
            "tp": None,
            "risk_pct": None,
            "reason": "no trend",
            "score": None,
            "metrics": None
        }

    # Detect pullback
    pullback_long, pullback_short = strategy.detect_pullback(candles)

    # Check LONG
    if trend_up:
        if not pullback_long:
            return {
                "symbol": symbol,
                "signal": "NO TRADE",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": "no pullback",
                "score": None,
                "metrics": None
            }

        # Calculate setup
        long_entry, short_entry = strategy.calculate_entries(candles)
        sl_long, sl_short = strategy.calculate_stop_losses(candles)
        tp_long, tp_short = strategy.calculate_take_profits(long_entry, short_entry, sl_long, sl_short)
        risk_pct_long, risk_pct_short = strategy.calculate_risk_percent(long_entry, short_entry, sl_long, sl_short)

        # Apply filters
        should_skip, skip_reason = filters.apply_all_filters(
            candles, long_entry, short_entry, risk_pct_long, risk_pct_short, is_long=True
        )

        if should_skip:
            return {
                "symbol": symbol,
                "signal": "SKIP",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": skip_reason,
                "score": None,
                "metrics": None
            }

        # Calculate setup score and metrics
        score, metrics = scoring.calculate_setup_score(candles, long_entry, risk_pct_long, is_long=True)

        return {
            "symbol": symbol,
            "signal": "LONG",
            "entry": long_entry,
            "sl": sl_long,
            "tp": tp_long,
            "risk_pct": risk_pct_long,
            "reason": "pullback + breakout",
            "score": score,
            "metrics": metrics
        }

    # Check SHORT
    if trend_down:
        if not pullback_short:
            return {
                "symbol": symbol,
                "signal": "NO TRADE",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": "no pullback",
                "score": None,
                "metrics": None
            }

        # Calculate setup
        long_entry, short_entry = strategy.calculate_entries(candles)
        sl_long, sl_short = strategy.calculate_stop_losses(candles)
        tp_long, tp_short = strategy.calculate_take_profits(long_entry, short_entry, sl_long, sl_short)
        risk_pct_long, risk_pct_short = strategy.calculate_risk_percent(long_entry, short_entry, sl_long, sl_short)

        # Apply filters
        should_skip, skip_reason = filters.apply_all_filters(
            candles, long_entry, short_entry, risk_pct_long, risk_pct_short, is_long=False
        )

        if should_skip:
            return {
                "symbol": symbol,
                "signal": "SKIP",
                "entry": None,
                "sl": None,
                "tp": None,
                "risk_pct": None,
                "reason": skip_reason,
                "score": None,
                "metrics": None
            }

        # Calculate setup score and metrics
        score, metrics = scoring.calculate_setup_score(candles, short_entry, risk_pct_short, is_long=False)

        return {
            "symbol": symbol,
            "signal": "SHORT",
            "entry": short_entry,
            "sl": sl_short,
            "tp": tp_short,
            "risk_pct": risk_pct_short,
            "reason": "pullback + breakdown",
            "score": score,
            "metrics": metrics
        }

    return None


def format_output(results: List[Dict]) -> None:
    """Format and print results with quality scoring."""
    # Separate by signal type
    longs = [r for r in results if r["signal"] == "LONG"]
    shorts = [r for r in results if r["signal"] == "SHORT"]
    skips = [r for r in results if r["signal"] == "SKIP"]
    no_trades = [r for r in results if r["signal"] == "NO TRADE"]

    # Sort by score (descending) and limit to top 2
    longs.sort(key=lambda x: x.get("score", -1), reverse=True)
    shorts.sort(key=lambda x: x.get("score", -1), reverse=True)

    top_longs = longs[:2]
    top_shorts = shorts[:2]

    # Combine for output
    output_results = top_longs + top_shorts + skips + no_trades

    print("\n" + "=" * 160)
    print(
        f"{'SYMBOL':<10} {'SIGNAL':<10} {'ENTRY':<15} {'SL':<15} {'TP':<15} "
        f"{'RISK%':<8} {'DIST%':<8} {'PULL':<6} {'RATIO':<7} {'SCORE':<6} {'REASON':<20}"
    )
    print("=" * 160)

    for result in output_results:
        symbol = result["symbol"]
        signal = result["signal"]
        reason = result["reason"]

        if signal in ("LONG", "SHORT"):
            entry = round_price(result["entry"])
            sl = round_price(result["sl"])
            tp = round_price(result["tp"])
            risk_str = f"{result['risk_pct'] * 100:.2f}%"

            metrics = result["metrics"]
            dist_str = f"{metrics['distance_to_entry_pct']:.2f}%"
            pull_str = f"{metrics['pullback_count']}"
            ratio_str = f"{metrics['last_candle_ratio']:.2f}x"
            score_str = f"{result['score']}/5"

            print(
                f"{symbol:<10} {signal:<10} {entry:<15} {sl:<15} {tp:<15} "
                f"{risk_str:<8} {dist_str:<8} {pull_str:<6} {ratio_str:<7} {score_str:<6} {reason:<20}"
            )
        else:
            print(
                f"{symbol:<10} {signal:<10} {'-':<15} {'-':<15} {'-':<15} "
                f"{'-':<8} {'-':<8} {'-':<6} {'-':<7} {'-':<6} {reason:<20}"
            )

    print("=" * 160 + "\n")


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
