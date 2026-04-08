"""Filters (exact specification)."""

from typing import List, Dict, Tuple


def calculate_distance(price: float, entry: float, side: str) -> float:
    """
    Calculate entry distance as decimal (not percentage).

    Returns distance >= 0.0

    LONG: (price - entry) / entry
    SHORT: (entry - price) / entry
    """
    if entry == 0:
        return 0.0

    if side == "LONG":
        distance = (price - entry) / entry
    elif side == "SHORT":
        distance = (entry - price) / entry
    else:
        return 0.0

    return max(0.0, distance)


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
    is_long: bool,
    debug: bool = False
) -> Tuple[bool, str]:
    """
    Distance to entry filter: avoid missed entries.

    Uses shared calculate_distance function.
    Threshold: 0.0012 (0.12%)

    Returns (should_skip, reason).
    """
    if len(candles) == 0:
        return False, ""

    price = candles[-1]["close"]
    max_distance = 0.0012

    if is_long:
        entry = long_entry
        side = "LONG"
    else:
        entry = short_entry
        side = "SHORT"

    distance = calculate_distance(price, entry, side)

    if debug:
        dist_pct = distance * 100
        print(f"  [DISTANCE FILTER] side={side} price={price:.2f} entry={entry:.2f} "
              f"distance_raw={distance:.6f} dist_pct={dist_pct:.2f}% threshold={max_distance:.4f}")

    if distance > max_distance:
        if debug:
            print(f"    → SKIP: {distance:.6f} > {max_distance:.6f}")
        if is_long:
            return True, "missed long"
        else:
            return True, "missed short"

    if debug:
        print(f"    → PASS")

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


def expanded_move_filter(candles: List[Dict]) -> Tuple[bool, str]:
    """
    Recent expansion filter: if price has already moved >1.5% in last 20 candles → SKIP.

    move_pct = (recent_high - recent_low) / recent_low

    Returns (should_skip, reason).
    """
    if len(candles) < 20:
        return False, ""

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])

    if recent_low == 0:
        return False, ""

    move_pct = (recent_high - recent_low) / recent_low

    if move_pct > 0.015:
        return True, "expanded move"

    return False, ""


def apply_all_filters(
    candles: List[Dict],
    long_entry: float,
    short_entry: float,
    risk_pct_long: float,
    risk_pct_short: float,
    is_long: bool,
    debug: bool = False
) -> Tuple[bool, str]:
    """
    Apply all filters in order. Return first failure.

    Returns (should_skip, reason).
    """
    # Expanded move filter (check before other setup filters)
    skip, reason = expanded_move_filter(candles)
    if skip:
        return True, reason

    # Late move filter (same for both LONG/SHORT)
    skip, reason = late_move_filter(candles)
    if skip:
        return True, reason

    # Distance to entry filter
    skip, reason = distance_to_entry_filter(candles, long_entry, short_entry, is_long, debug=debug)
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
