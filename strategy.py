"""Price-action strategy logic (exact specification)."""

from typing import List, Dict, Tuple


def get_closed_candles(klines: List[Dict]) -> List[Dict]:
    """Exclude current live candle. Return only closed candles."""
    return klines[:-1]


def detect_trend(candles: List[Dict]) -> Tuple[bool, bool]:
    """
    Detect trend using last 12 closed candles.

    Returns (trend_up, trend_down).
    """
    if len(candles) < 12:
        return False, False

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    recent_highs = highs[-6:]
    previous_highs = highs[-12:-6]

    recent_lows = lows[-6:]
    previous_lows = lows[-12:-6]

    higher_highs_count = sum(1 for i in range(6) if recent_highs[i] > previous_highs[i])
    higher_lows_count = sum(1 for i in range(6) if recent_lows[i] > previous_lows[i])

    lower_highs_count = sum(1 for i in range(6) if recent_highs[i] < previous_highs[i])
    lower_lows_count = sum(1 for i in range(6) if recent_lows[i] < previous_lows[i])

    trend_up = (higher_highs_count >= 4) and (higher_lows_count >= 4)
    trend_down = (lower_highs_count >= 4) and (lower_lows_count >= 4)

    return trend_up, trend_down


def detect_pullback(candles: List[Dict]) -> Tuple[bool, bool]:
    """
    Detect pullback using last 5 closed candles.

    Returns (pullback_long, pullback_short).
    """
    if len(candles) < 5:
        return False, False

    recent = candles[-5:]

    bearish = sum(1 for c in recent if c["close"] < c["open"])
    bullish = sum(1 for c in recent if c["close"] > c["open"])

    pullback_long = bearish >= 2
    pullback_short = bullish >= 2

    return pullback_long, pullback_short


def calculate_entries(candles: List[Dict]) -> Tuple[float, float]:
    """
    Calculate entry prices using last 3 closed candles.

    Returns (long_entry, short_entry).
    """
    if len(candles) < 3:
        return 0.0, 0.0

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    last_highs = highs[-3:]
    last_lows = lows[-3:]

    prev_high = max(last_highs[:-1])
    prev_low = min(last_lows[:-1])

    buffer = 0.0008

    long_entry = prev_high * (1 + buffer)
    short_entry = prev_low * (1 - buffer)

    return long_entry, short_entry


def calculate_stop_losses(candles: List[Dict]) -> Tuple[float, float]:
    """
    Calculate stop losses using last 5 closed candles (excluding breakout).

    Returns (sl_long, sl_short).
    """
    if len(candles) < 6:
        return 0.0, 0.0

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    sl_long = min(lows[-6:-1])
    sl_short = max(highs[-6:-1])

    return sl_long, sl_short


def calculate_take_profits(
    long_entry: float,
    short_entry: float,
    sl_long: float,
    sl_short: float
) -> Tuple[float, float]:
    """
    Calculate take profits with fixed 1.5R.

    Returns (tp_long, tp_short).
    """
    RR = 1.5

    risk_long = long_entry - sl_long
    risk_short = sl_short - short_entry

    tp_long = long_entry + (risk_long * RR)
    tp_short = short_entry - (risk_short * RR)

    return tp_long, tp_short


def calculate_risk_percent(
    long_entry: float,
    short_entry: float,
    sl_long: float,
    sl_short: float
) -> Tuple[float, float]:
    """
    Calculate risk as percentage of entry.

    Returns (risk_pct_long, risk_pct_short).
    """
    if long_entry == 0 or short_entry == 0:
        return 0.0, 0.0

    risk_long = long_entry - sl_long
    risk_short = sl_short - short_entry

    risk_pct_long = risk_long / long_entry
    risk_pct_short = risk_short / short_entry

    return risk_pct_long, risk_pct_short


def get_trigger_state(price: float, entry: float, is_long: bool) -> str:
    """
    Determine if breakout entry has been triggered.

    LONG: triggered when price >= entry
    SHORT: triggered when price <= entry

    Returns "triggered" or "waiting".
    """
    if is_long:
        return "triggered" if price >= entry else "waiting"
    else:
        return "triggered" if price <= entry else "waiting"


def is_wait_gap_too_large(price: float, entry: float, is_long: bool, max_gap: float = 0.003) -> bool:
    """
    Check if WAIT setup is too far from entry to be useful.

    max_gap default: 0.003 (0.30%)

    Returns True if setup should be skipped (gap too large).
    """
    if entry == 0:
        return False

    if is_long:
        gap = (entry - price) / entry
    else:
        gap = (price - entry) / entry

    gap = max(0.0, gap)

    return gap > max_gap
