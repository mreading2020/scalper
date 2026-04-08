"""Risk management: SL, TP, and risk/reward calculations."""

from typing import List, Dict
import strategy


def calculate_long_sl(candles: List[Dict]) -> float:
    """
    LONG SL: lowest low of last 5 candles (excluding current).
    """
    return strategy.get_last_5_low(candles)


def calculate_short_sl(candles: List[Dict]) -> float:
    """
    SHORT SL: highest high of last 5 candles.
    """
    return strategy.get_last_5_high(candles)


def calculate_long_entry(candles: List[Dict], buffer: float = 0.0008) -> float:
    """
    LONG entry: previous 2-candle high * (1 + buffer).
    Buffer default: 0.08% (0.0008).
    """
    prev_2_high = strategy.get_previous_2_high(candles)
    return prev_2_high * (1 + buffer)


def calculate_short_entry(candles: List[Dict], buffer: float = 0.0008) -> float:
    """
    SHORT entry: previous 2-candle low * (1 - buffer).
    Buffer default: 0.08% (0.0008).
    """
    prev_2_low = strategy.get_previous_2_low(candles)
    return prev_2_low * (1 - buffer)


def calculate_long_tp(entry: float, sl: float, ratio: float = 1.5) -> float:
    """
    LONG TP: entry + (entry - SL) * ratio.
    Fixed 1.5R by default.
    """
    risk = entry - sl
    return entry + risk * ratio


def calculate_short_tp(entry: float, sl: float, ratio: float = 1.5) -> float:
    """
    SHORT TP: entry - (SL - entry) * ratio.
    Fixed 1.5R by default.
    """
    risk = sl - entry
    return entry - risk * ratio


def calculate_risk_percent(entry: float, sl: float, current_price: float) -> float:
    """
    Calculate risk as a percentage of current price.
    Risk = abs(entry - SL) / current_price * 100.
    """
    if current_price == 0:
        return 0.0
    risk = abs(entry - sl) / current_price * 100
    return risk


def is_valid_long_setup(entry: float, sl: float, current_price: float) -> bool:
    """
    Validate LONG setup:
    - SL must be below entry
    - Current price must be below entry (not already passed)
    """
    if sl >= entry:
        return False
    if current_price >= entry:
        return False
    return True


def is_valid_short_setup(entry: float, sl: float, current_price: float) -> bool:
    """
    Validate SHORT setup:
    - SL must be above entry
    - Current price must be above entry (not already passed)
    """
    if sl <= entry:
        return False
    if current_price <= entry:
        return False
    return True
