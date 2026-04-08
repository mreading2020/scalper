"""Price-action strategy logic: trend and pullback detection."""

from typing import List, Dict


def is_uptrend(candles: List[Dict], lookback: int = 6) -> bool:
    """
    Detect uptrend: higher highs AND higher lows.
    Compare last ~6 candles vs previous group.
    """
    if len(candles) < lookback * 2:
        return False

    recent = candles[-lookback:]
    previous = candles[-(lookback * 2):-lookback]

    recent_high = max(c["high"] for c in recent)
    recent_low = min(c["low"] for c in recent)
    prev_high = max(c["high"] for c in previous)
    prev_low = min(c["low"] for c in previous)

    return recent_high > prev_high and recent_low > prev_low


def is_downtrend(candles: List[Dict], lookback: int = 6) -> bool:
    """
    Detect downtrend: lower highs AND lower lows.
    Compare last ~6 candles vs previous group.
    """
    if len(candles) < lookback * 2:
        return False

    recent = candles[-lookback:]
    previous = candles[-(lookback * 2):-lookback]

    recent_high = max(c["high"] for c in recent)
    recent_low = min(c["low"] for c in recent)
    prev_high = max(c["high"] for c in previous)
    prev_low = min(c["low"] for c in previous)

    return recent_high < prev_high and recent_low < prev_low


def count_red_candles(candles: List[Dict], count: int = 5) -> int:
    """Count consecutive red candles from the end (close < open)."""
    reds = 0
    for i in range(1, count + 1):
        if len(candles) < i:
            break
        if candles[-i]["close"] < candles[-i]["open"]:
            reds += 1
        else:
            break
    return reds


def count_green_candles(candles: List[Dict], count: int = 5) -> int:
    """Count consecutive green candles from the end (close > open)."""
    greens = 0
    for i in range(1, count + 1):
        if len(candles) < i:
            break
        if candles[-i]["close"] > candles[-i]["open"]:
            greens += 1
        else:
            break
    return greens


def has_long_pullback(candles: List[Dict]) -> bool:
    """
    LONG pullback: 2–4 consecutive red candles after uptrend.
    """
    reds = count_red_candles(candles, count=4)
    return 2 <= reds <= 4


def has_short_pullback(candles: List[Dict]) -> bool:
    """
    SHORT pullback: 2–4 consecutive green candles after downtrend.
    """
    greens = count_green_candles(candles, count=4)
    return 2 <= greens <= 4


def get_previous_2_high(candles: List[Dict]) -> float:
    """Get the high of the previous 2 candles (index -2 and -1)."""
    if len(candles) < 2:
        return 0.0
    return max(candles[-2]["high"], candles[-1]["high"])


def get_previous_2_low(candles: List[Dict]) -> float:
    """Get the low of the previous 2 candles (index -2 and -1)."""
    if len(candles) < 2:
        return 0.0
    return min(candles[-2]["low"], candles[-1]["low"])


def get_last_5_low(candles: List[Dict]) -> float:
    """Get the lowest low of the last 5 candles (excluding current)."""
    if len(candles) < 5:
        return min(c["low"] for c in candles)
    return min(c["low"] for c in candles[-5:])


def get_last_5_high(candles: List[Dict]) -> float:
    """Get the highest high of the last 5 candles (excluding current)."""
    if len(candles) < 5:
        return max(c["high"] for c in candles)
    return max(c["high"] for c in candles[-5:])


def get_average_candle_size(candles: List[Dict], count: int = 10) -> float:
    """Get average candle size (high - low) for the last N candles."""
    if len(candles) < count:
        count = len(candles)
    sizes = [c["high"] - c["low"] for c in candles[-count:]]
    return sum(sizes) / len(sizes) if sizes else 0.0


def get_last_candle_size(candles: List[Dict]) -> float:
    """Get the last candle's size (high - low)."""
    if not candles:
        return 0.0
    last = candles[-1]
    return last["high"] - last["low"]


def get_20_candle_range(candles: List[Dict]) -> float:
    """Get the range (high - low) of the last 20 candles."""
    if len(candles) < 20:
        return 0.0
    recent = candles[-20:]
    high = max(c["high"] for c in recent)
    low = min(c["low"] for c in recent)
    return high - low
