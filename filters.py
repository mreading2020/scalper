"""Filters (exact specification)."""

from typing import List, Dict, Tuple


def late_move_filter(candles: List[Dict]) -> Tuple[bool, str]:
    """
    Late move filter: if last_size > avg_size * 1.5 → SKIP.

    Returns (should_skip, reason).
    """
    if len(candles) < 10:
        return False, ""

    sizes = [c["high"] - c["low"] for c in candles]
    last_size = sizes[-1]
    avg_size = sum(sizes[-10:]) / 10

    if last_size > avg_size * 1.5:
        return True, "late move"

    return False, ""


def distance_to_entry_filter(
    candles: List[Dict],
    long_entry: float,
    short_entry: float,
    is_long: bool
) -> Tuple[bool, str]:
    """
    Distance to entry filter: avoid missed entries.

    LONG: if (price - long_entry) / long_entry > 0.0015 → SKIP
    SHORT: if (short_entry - price) / short_entry > 0.0015 → SKIP

    Returns (should_skip, reason).
    """
    if len(candles) == 0:
        return False, ""

    price = candles[-1]["close"]

    if is_long:
        if long_entry == 0:
            return False, ""
        distance = (price - long_entry) / long_entry
        if distance > 0.0015:
            return True, "missed long"
    else:
        if short_entry == 0:
            return False, ""
        distance = (short_entry - price) / short_entry
        if distance > 0.0015:
            return True, "missed short"

    return False, ""


def volatility_chop_filter(candles: List[Dict]) -> Tuple[bool, str]:
    """
    Volatility / chop filter: if range_pct < 0.004 → SKIP.

    range_pct = (range_high - range_low) / price

    Returns (should_skip, reason).
    """
    if len(candles) < 20:
        return False, ""

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    price = candles[-1]["close"]

    if price == 0:
        return False, ""

    range_high = max(highs[-20:])
    range_low = min(lows[-20:])

    range_pct = (range_high - range_low) / price

    if range_pct < 0.004:
        return True, "chop"

    return False, ""


def risk_sanity_filter(risk_pct: float) -> Tuple[bool, str]:
    """
    Risk sanity filter: if risk_pct < 0.002 or > 0.012 → SKIP.

    Returns (should_skip, reason).
    """
    if risk_pct < 0.002:
        return True, "risk too small"

    if risk_pct > 0.012:
        return True, "risk too large"

    return False, ""


def apply_all_filters(
    candles: List[Dict],
    long_entry: float,
    short_entry: float,
    risk_pct_long: float,
    risk_pct_short: float,
    is_long: bool
) -> Tuple[bool, str]:
    """
    Apply all filters in order. Return first failure.

    Returns (should_skip, reason).
    """
    # Late move filter (same for both LONG/SHORT)
    skip, reason = late_move_filter(candles)
    if skip:
        return True, reason

    # Distance to entry filter
    skip, reason = distance_to_entry_filter(candles, long_entry, short_entry, is_long)
    if skip:
        return True, reason

    # Volatility filter (same for both LONG/SHORT)
    skip, reason = volatility_chop_filter(candles)
    if skip:
        return True, reason

    # Risk sanity filter
    risk_pct = risk_pct_long if is_long else risk_pct_short
    skip, reason = risk_sanity_filter(risk_pct)
    if skip:
        return True, reason

    return False, ""
