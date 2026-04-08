"""Filters to skip invalid setups."""

from typing import List, Dict, Tuple
import strategy


def late_move_filter(candles: List[Dict]) -> Tuple[bool, str]:
    """
    Filter: If last candle size > 1.5x average of last 10 candles → SKIP.
    Returns (is_late_move, reason).
    """
    avg_size = strategy.get_average_candle_size(candles, count=10)
    last_size = strategy.get_last_candle_size(candles)

    if avg_size == 0:
        return False, ""

    if last_size > avg_size * 1.5:
        return True, "late move"

    return False, ""


def distance_to_entry_filter(
    symbol: str,
    candles: List[Dict],
    current_price: float,
    entry: float,
    is_long: bool
) -> Tuple[bool, str]:
    """
    Filter: If current price is too far above entry (LONG) or below (SHORT) → SKIP.
    LONG: if current price > entry * (1 + 0.002) → SKIP ("missed long")
    SHORT: if current price < entry * (1 - 0.002) → SKIP ("missed short")
    Threshold: 0.2% (0.002)
    """
    if current_price is None or entry == 0:
        return False, ""

    if is_long:
        # LONG: current should be below entry (not above)
        if current_price > entry * 1.002:
            return True, "missed long"
    else:
        # SHORT: current should be above entry (not below)
        if current_price < entry * 0.998:
            return True, "missed short"

    return False, ""


def volatility_chop_filter(candles: List[Dict], current_price: float) -> Tuple[bool, str]:
    """
    Filter: If 20-candle range < ~0.4% of price → SKIP (too choppy).
    Returns (is_chop, reason).
    """
    range_20 = strategy.get_20_candle_range(candles)

    if current_price == 0:
        return False, ""

    range_pct = (range_20 / current_price) * 100

    if range_pct < 0.4:
        return True, "chop"

    return False, ""


def risk_sanity_filter(
    risk_pct: float,
    current_price: float
) -> Tuple[bool, str]:
    """
    Filter: Risk validation.
    - If risk < 0.2% of price → SKIP (noise)
    - If risk > 1.2% of price → SKIP (too much)
    Returns (skip, reason).
    """
    if current_price == 0:
        return False, ""

    # Check if risk is too small (noise)
    if risk_pct < 0.2:
        return True, "risk too small"

    # Check if risk is too large
    if risk_pct > 1.2:
        return True, "risk too large"

    return False, ""


def check_all_filters(
    symbol: str,
    candles: List[Dict],
    current_price: float,
    entry: float,
    is_long: bool,
    risk_pct: float
) -> Tuple[bool, str]:
    """
    Run all filters and return first failure (skip, reason).
    Returns (should_skip, reason).
    """
    checks = [
        late_move_filter(candles),
        distance_to_entry_filter(symbol, candles, current_price, entry, is_long),
        volatility_chop_filter(candles, current_price),
        risk_sanity_filter(risk_pct, current_price),
    ]

    for skip, reason in checks:
        if skip:
            return True, reason

    return False, ""
