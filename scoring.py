"""Setup quality scoring (V4 enhancement)."""

from typing import List, Dict, Tuple
import filters


def count_bearish_candles(candles: List[Dict]) -> int:
    """Count bearish (red) candles in last 5."""
    if len(candles) < 5:
        return 0
    recent = candles[-5:]
    return sum(1 for c in recent if c["close"] < c["open"])


def count_bullish_candles(candles: List[Dict]) -> int:
    """Count bullish (green) candles in last 5."""
    if len(candles) < 5:
        return 0
    recent = candles[-5:]
    return sum(1 for c in recent if c["close"] > c["open"])


def get_distance_to_entry(candles: List[Dict], entry: float, is_long: bool) -> float:
    """
    Calculate distance from current price to entry as decimal (not percentage).

    Uses shared calculate_distance function for consistency.

    Returns decimal value (e.g., 0.0029 for 0.29%).
    """
    if len(candles) == 0 or entry == 0:
        return 0.0

    price = candles[-1]["close"]
    side = "LONG" if is_long else "SHORT"

    return filters.calculate_distance(price, entry, side)


def get_last_candle_size_ratio(candles: List[Dict]) -> float:
    """
    Calculate last candle size as ratio of average size.

    ratio = last_size / avg_size
    """
    if len(candles) < 10:
        return 1.0

    sizes = [c["high"] - c["low"] for c in candles]
    last_size = sizes[-1]
    avg_size = sum(sizes[-10:]) / 10

    if avg_size == 0:
        return 1.0

    return last_size / avg_size


def get_20_candle_range_pct(candles: List[Dict]) -> float:
    """
    Calculate 20-candle range as percentage of current price.

    range_pct = (range_high - range_low) / price * 100
    """
    if len(candles) < 20:
        return 0.0

    price = candles[-1]["close"]
    if price == 0:
        return 0.0

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    range_high = max(highs[-20:])
    range_low = min(lows[-20:])

    range_pct = (range_high - range_low) / price * 100

    return range_pct


def calculate_setup_score(
    candles: List[Dict],
    entry: float,
    risk_pct: float,
    is_long: bool
) -> Tuple[int, Dict]:
    """
    Calculate setup quality score (0-5).

    Scoring rules:
    - +1 if risk % is between 0.3% and 0.7%
    - +1 if distance from entry is under 0.1%
    - +1 if pullback count is 3 or more
    - +1 if last candle size is below 1.2x average
    - +1 if 20-candle range is above 0.6%

    Returns (score, metrics_dict).
    """
    score = 0
    metrics = {}

    # Score 1: Risk % between 0.3% and 0.7%
    risk_pct_val = risk_pct * 100
    metrics["risk_pct"] = risk_pct_val
    if 0.3 <= risk_pct_val <= 0.7:
        score += 1

    # Score 2: Distance from entry under 0.1%
    distance = get_distance_to_entry(candles, entry, is_long)
    metrics["distance_to_entry_pct"] = distance
    if distance < 0.1:
        score += 1

    # Score 3: Pullback count >= 3
    if is_long:
        pullback_count = count_bearish_candles(candles)
    else:
        pullback_count = count_bullish_candles(candles)
    metrics["pullback_count"] = pullback_count
    if pullback_count >= 3:
        score += 1

    # Score 4: Last candle size < 1.2x average
    last_candle_ratio = get_last_candle_size_ratio(candles)
    metrics["last_candle_ratio"] = last_candle_ratio
    if last_candle_ratio < 1.2:
        score += 1

    # Score 5: 20-candle range > 0.6%
    range_20_pct = get_20_candle_range_pct(candles)
    metrics["range_20_pct"] = range_20_pct
    if range_20_pct > 0.6:
        score += 1

    return score, metrics
