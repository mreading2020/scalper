"""Test the signal logic with mock data."""

from typing import List, Dict
import strategy
import filters
import risk


def mock_candles_uptrend_pullback() -> List[Dict]:
    """
    Create mock candles: uptrend for 12 candles, then 3 red candles (pullback).
    """
    candles = []

    # Uptrend phase (12 candles with higher highs and lows)
    for i in range(12):
        candles.append({
            "open": 100 + i * 0.5,
            "high": 101 + i * 0.5,
            "low": 99 + i * 0.5,
            "close": 100.5 + i * 0.5,
            "volume": 1000,
            "open_time": i,
        })

    # Pullback phase (3 red candles)
    base = candles[-1]["close"]
    for i in range(3):
        candles.append({
            "open": base - i * 0.2,
            "high": base - i * 0.2,
            "low": base - i * 0.3,
            "close": base - i * 0.3,
            "volume": 1000,
            "open_time": 12 + i,
        })

    return candles


def mock_candles_downtrend_pullback() -> List[Dict]:
    """
    Create mock candles: downtrend for 12 candles, then 3 green candles (pullback).
    """
    candles = []

    # Downtrend phase (12 candles with lower highs and lows)
    for i in range(12):
        candles.append({
            "open": 100 - i * 0.5,
            "high": 101 - i * 0.5,
            "low": 99 - i * 0.5,
            "close": 99.5 - i * 0.5,
            "volume": 1000,
            "open_time": i,
        })

    # Pullback phase (3 green candles)
    base = candles[-1]["close"]
    for i in range(3):
        candles.append({
            "open": base + i * 0.2,
            "high": base + i * 0.3,
            "low": base + i * 0.2,
            "close": base + i * 0.3,
            "volume": 1000,
            "open_time": 12 + i,
        })

    return candles


def test_uptrend_long_signal():
    """Test LONG signal detection."""
    candles = mock_candles_uptrend_pullback()
    current_price = 95.0  # Below entry

    is_up = strategy.is_uptrend(candles)
    has_pullback = strategy.has_long_pullback(candles)

    print("=== TEST: UPTREND + LONG PULLBACK ===")
    print(f"Uptrend detected: {is_up}")
    print(f"Long pullback detected: {has_pullback}")

    if is_up and has_pullback:
        entry = risk.calculate_long_entry(candles)
        sl = risk.calculate_long_sl(candles)
        tp = risk.calculate_long_tp(entry, sl)
        risk_pct = risk.calculate_risk_percent(entry, sl, current_price)

        print(f"Entry: {entry:.2f}")
        print(f"SL: {sl:.2f}")
        print(f"TP: {tp:.2f}")
        print(f"Risk: {risk_pct:.2f}%")
        print(f"Valid LONG setup: {risk.is_valid_long_setup(entry, sl, current_price)}")
    print()


def test_downtrend_short_signal():
    """Test SHORT signal detection."""
    candles = mock_candles_downtrend_pullback()
    current_price = 90.0  # Above entry

    is_down = strategy.is_downtrend(candles)
    has_pullback = strategy.has_short_pullback(candles)

    print("=== TEST: DOWNTREND + SHORT PULLBACK ===")
    print(f"Downtrend detected: {is_down}")
    print(f"Short pullback detected: {has_pullback}")

    if is_down and has_pullback:
        entry = risk.calculate_short_entry(candles)
        sl = risk.calculate_short_sl(candles)
        tp = risk.calculate_short_tp(entry, sl)
        risk_pct = risk.calculate_risk_percent(entry, sl, current_price)

        print(f"Entry: {entry:.2f}")
        print(f"SL: {sl:.2f}")
        print(f"TP: {tp:.2f}")
        print(f"Risk: {risk_pct:.2f}%")
        print(f"Valid SHORT setup: {risk.is_valid_short_setup(entry, sl, current_price)}")
    print()


def test_filters():
    """Test filter logic."""
    candles = mock_candles_uptrend_pullback()
    current_price = 95.0
    entry = risk.calculate_long_entry(candles)
    sl = risk.calculate_long_sl(candles)
    risk_pct = risk.calculate_risk_percent(entry, sl, current_price)

    print("=== TEST: FILTERS ===")

    # Test late move filter
    late_move, reason = filters.late_move_filter(candles)
    print(f"Late move filter: {late_move} ({reason})")

    # Test distance to entry
    dist_skip, dist_reason = filters.distance_to_entry_filter(
        "TEST", candles, current_price, entry, is_long=True
    )
    print(f"Distance to entry filter: {dist_skip} ({dist_reason})")

    # Test volatility
    chop, chop_reason = filters.volatility_chop_filter(candles, current_price)
    print(f"Volatility/chop filter: {chop} ({chop_reason})")

    # Test risk sanity
    risk_skip, risk_reason = filters.risk_sanity_filter(risk_pct, current_price)
    print(f"Risk sanity filter: {risk_skip} ({risk_reason})")

    # All filters
    should_skip, skip_reason = filters.check_all_filters(
        "TEST", candles, current_price, entry, is_long=True, risk_pct=risk_pct
    )
    print(f"All filters: skip={should_skip} reason='{skip_reason}'")
    print()


if __name__ == "__main__":
    test_uptrend_long_signal()
    test_downtrend_short_signal()
    test_filters()
