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

        # Apply filters (with debug output)
        should_skip, skip_reason = filters.apply_all_filters(
            candles, long_entry, short_entry, risk_pct_long, risk_pct_short, is_long=True, debug=True
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

        # Determine trigger state
        price = candles[-1]["close"]
        trigger_state = strategy.get_trigger_state(price, long_entry, is_long=True)
        signal = "LONG" if trigger_state == "triggered" else "WAIT LONG"

        # Check if WAIT setup is too far from entry
        if signal == "WAIT LONG":
            if strategy.is_wait_gap_too_large(price, long_entry, is_long=True, max_gap=0.003):
                return {
                    "symbol": symbol,
                    "signal": "NO TRADE",
                    "entry": None,
                    "sl": None,
                    "tp": None,
                    "risk_pct": None,
                    "reason": "waiting too far from entry",
                    "score": None,
                    "metrics": None
                }

        return {
            "symbol": symbol,
            "signal": signal,
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

        # Apply filters (with debug output)
        should_skip, skip_reason = filters.apply_all_filters(
            candles, long_entry, short_entry, risk_pct_long, risk_pct_short, is_long=False, debug=True
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

        # Determine trigger state
        price = candles[-1]["close"]
        trigger_state = strategy.get_trigger_state(price, short_entry, is_long=False)
        signal = "SHORT" if trigger_state == "triggered" else "WAIT SHORT"

        # Check if WAIT setup is too far from entry
        if signal == "WAIT SHORT":
            if strategy.is_wait_gap_too_large(price, short_entry, is_long=False, max_gap=0.003):
                return {
                    "symbol": symbol,
                    "signal": "NO TRADE",
                    "entry": None,
                    "sl": None,
                    "tp": None,
                    "risk_pct": None,
                    "reason": "waiting too far from entry",
                    "score": None,
                    "metrics": None
                }

        return {
            "symbol": symbol,
            "signal": signal,
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
    triggered_longs = [r for r in results if r["signal"] == "LONG"]
    triggered_shorts = [r for r in results if r["signal"] == "SHORT"]
    wait_longs = [r for r in results if r["signal"] == "WAIT LONG"]
    wait_shorts = [r for r in results if r["signal"] == "WAIT SHORT"]
    skips = [r for r in results if r["signal"] == "SKIP"]
    no_trades = [r for r in results if r["signal"] == "NO TRADE"]

    # Sort by score (descending) and limit to top 2 for each category
    triggered_longs.sort(key=lambda x: x.get("score", -1), reverse=True)
    triggered_shorts.sort(key=lambda x: x.get("score", -1), reverse=True)
    wait_longs.sort(key=lambda x: x.get("score", -1), reverse=True)
    wait_shorts.sort(key=lambda x: x.get("score", -1), reverse=True)

    top_triggered_longs = triggered_longs[:2]
    top_triggered_shorts = triggered_shorts[:2]
    top_wait_longs = wait_longs[:2]
    top_wait_shorts = wait_shorts[:2]

    # Combine for output: triggered first, then waiting, then skips, then no trades
    output_results = (
        top_triggered_longs + top_triggered_shorts +
        top_wait_longs + top_wait_shorts +
        skips + no_trades
    )

    print("\n" + "=" * 180)
    print(
        f"{'SYMBOL':<10} {'SIGNAL':<12} {'ENTRY':<15} {'SL':<15} {'TP':<15} "
        f"{'RISK%':<8} {'DIST%':<8} {'GAP%':<8} {'PULL':<6} {'RATIO':<7} {'SCORE':<6} {'REASON':<20}"
    )
    print("=" * 180)

    for result in output_results:
        symbol = result["symbol"]
        signal = result["signal"]
        reason = result["reason"]

        if signal in ("LONG", "SHORT", "WAIT LONG", "WAIT SHORT"):
            entry = round_price(result["entry"])
            sl = round_price(result["sl"])
            tp = round_price(result["tp"])
            risk_str = f"{result['risk_pct'] * 100:.2f}%"

            metrics = result["metrics"]
            dist_pct = metrics['distance_to_entry_pct'] * 100
            gap_pct = metrics['gap_to_entry_pct'] * 100

            # For WAIT states: show gap, distance is 0
            # For LONG/SHORT: show distance, gap is 0
            if signal in ("WAIT LONG", "WAIT SHORT"):
                dist_str = "0.00%"
                gap_str = f"{gap_pct:.2f}%"
            else:
                dist_str = f"{dist_pct:.2f}%"
                gap_str = "0.00%"

            pull_str = f"{metrics['pullback_count']}"
            ratio_str = f"{metrics['last_candle_ratio']:.2f}x"
            score_str = f"{result['score']}/5"

            print(
                f"{symbol:<10} {signal:<12} {entry:<15} {sl:<15} {tp:<15} "
                f"{risk_str:<8} {dist_str:<8} {gap_str:<8} {pull_str:<6} {ratio_str:<7} {score_str:<6} {reason:<20}"
            )
        else:
            print(
                f"{symbol:<10} {signal:<12} {'-':<15} {'-':<15} {'-':<15} "
                f"{'-':<8} {'-':<8} {'-':<8} {'-':<6} {'-':<7} {'-':<6} {reason:<20}"
            )

    print("=" * 180 + "\n")


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
