"""Test the signal logic with mock data (exact specification)."""

from typing import List, Dict
import strategy
import filters


def mock_uptrend_pullback() -> List[Dict]:
    """
    Create 200 mock candles:
    - Candles 0-93: ranging/neutral
    - Candles 94-105: uptrend (12 candles with higher highs/lows)
    - Candles 106-194: pullback (last 5 will have >= 2 red candles)
    - Candle 195-199: last 5 with red candles
    """
    candles = []

    # Ranging phase (0-93)
    for i in range(94):
        candles.append({
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.2,
        })

    # Uptrend phase (94-105): 12 candles with higher highs/lows
    base = 100.0
    for i in range(12):
        candles.append({
            "open": base + i * 0.3,
            "high": base + i * 0.3 + 0.5,
            "low": base + i * 0.3 - 0.2,
            "close": base + i * 0.3 + 0.3,
        })

    # Pullback phase (106-194): red candles at the end
    current_price = candles[-1]["close"]
    for i in range(89):
        if i < 84:  # Neutral
            candles.append({
                "open": current_price,
                "high": current_price + 0.1,
                "low": current_price - 0.1,
                "close": current_price,
            })
        else:  # Last 5: red candles
            candles.append({
                "open": current_price - i * 0.05,
                "high": current_price - i * 0.05,
                "low": current_price - i * 0.1,
                "close": current_price - i * 0.1,
            })

    # Last 5 should be red (close < open)
    for i in range(5):
        candles.append({
            "open": current_price - 0.3 - i * 0.1,
            "high": current_price - 0.3 - i * 0.1,
            "low": current_price - 0.4 - i * 0.1,
            "close": current_price - 0.4 - i * 0.1,
        })

    return candles[:200]


def mock_klines_for_api():
    """Mock klines as returned by Binance (list of lists)."""
    # Simulate 200 candles from Binance API
    klines = []
    for i in range(200):
        klines.append([
            1000000 + i * 300,  # open_time
            100.0 + i * 0.01,   # open
            100.5 + i * 0.01,   # high
            99.5 + i * 0.01,    # low
            100.2 + i * 0.01,   # close
            1000.0,             # volume
            2000000 + i * 300,  # close_time
            "100000",           # quote asset volume
            50,                 # number of trades
            "50000",            # taker buy base asset volume
            "50000",            # taker buy quote asset volume
            "0",                # ignore
        ])
    return klines


def test_trend_detection():
    """Test trend detection with exact logic."""
    candles = mock_uptrend_pullback()

    trend_up, trend_down = strategy.detect_trend(candles)

    print("=== TREND DETECTION TEST ===")
    print(f"Trend Up: {trend_up}")
    print(f"Trend Down: {trend_down}")
    print()


def test_pullback_detection():
    """Test pullback detection with exact logic."""
    candles = mock_uptrend_pullback()

    pullback_long, pullback_short = strategy.detect_pullback(candles)

    print("=== PULLBACK DETECTION TEST ===")
    print(f"Pullback Long (bearish >= 2): {pullback_long}")
    print(f"Pullback Short (bullish >= 2): {pullback_short}")
    print()


def test_entries_and_sl():
    """Test entry and SL calculation."""
    candles = mock_uptrend_pullback()

    long_entry, short_entry = strategy.calculate_entries(candles)
    sl_long, sl_short = strategy.calculate_stop_losses(candles)
    tp_long, tp_short = strategy.calculate_take_profits(long_entry, short_entry, sl_long, sl_short)
    risk_pct_long, risk_pct_short = strategy.calculate_risk_percent(long_entry, short_entry, sl_long, sl_short)

    print("=== ENTRY / SL / TP TEST ===")
    print(f"Long Entry: {long_entry:.6f}")
    print(f"Long SL: {sl_long:.6f}")
    print(f"Long TP: {tp_long:.6f}")
    print(f"Long Risk%: {risk_pct_long * 100:.2f}%")
    print()
    print(f"Short Entry: {short_entry:.6f}")
    print(f"Short SL: {sl_short:.6f}")
    print(f"Short TP: {tp_short:.6f}")
    print(f"Short Risk%: {risk_pct_short * 100:.2f}%")
    print()


def test_filters():
    """Test all filters."""
    candles = mock_uptrend_pullback()

    long_entry, short_entry = strategy.calculate_entries(candles)
    sl_long, sl_short = strategy.calculate_stop_losses(candles)
    risk_pct_long, risk_pct_short = strategy.calculate_risk_percent(long_entry, short_entry, sl_long, sl_short)

    print("=== FILTER TESTS ===")

    skip, reason = filters.late_move_filter(candles)
    print(f"Late move: {skip} ({reason})")

    skip, reason = filters.distance_to_entry_filter(candles, long_entry, short_entry, is_long=True)
    print(f"Distance to entry (LONG): {skip} ({reason})")

    skip, reason = filters.volatility_chop_filter(candles)
    print(f"Volatility/chop: {skip} ({reason})")

    skip, reason = filters.risk_sanity_filter(risk_pct_long)
    print(f"Risk sanity (LONG): {skip} ({reason})")

    skip, reason = filters.apply_all_filters(
        candles, long_entry, short_entry, risk_pct_long, risk_pct_short, is_long=True
    )
    print(f"\nAll filters (LONG): skip={skip}, reason='{reason}'")
    print()


def test_closed_candles():
    """Test that closed candles are properly extracted."""
    klines = mock_klines_for_api()
    closed = strategy.get_closed_candles(klines)

    print("=== CLOSED CANDLES TEST ===")
    print(f"Total klines: {len(klines)}")
    print(f"Closed candles: {len(closed)}")
    print(f"Expected: 199 (all but current live candle)")
    print()


if __name__ == "__main__":
    test_closed_candles()
    test_trend_detection()
    test_pullback_detection()
    test_entries_and_sl()
    test_filters()
    print("All tests completed.")
