# Binance Futures Signal Engine

A clean, modular price-action signal scanner for Binance USDⓈ-M futures. **Read-only, no auto-trading.**

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## What It Does

Scans the top 10 USDT pairs by volume on the 5-minute timeframe:

- **Detects trends**: Higher highs + higher lows (uptrend) vs. lower highs + lower lows (downtrend)
- **Confirms pullbacks**: 2–4 consecutive red/green candles
- **Generates signals**: LONG, SHORT, SKIP, or NO TRADE
- **Calculates risk**: Entry, stop loss, take profit (fixed 1.5R)
- **Applies filters**: Avoids late moves, missed entries, choppy ranges, unrealistic risk

Output is clean, aligned, and sorted by signal type.

## Structure

```
binance.py        → Fetch klines + top pairs from Binance API
strategy.py       → Trend detection, pullback logic
filters.py        → Skip conditions (late move, distance, chop, risk)
risk.py           → Entry/SL/TP calculation + validation
main.py           → Signal scanning + CLI output
test_logic.py     → Logic verification with mock data
```

## Strategy Logic

### 1. Trend Detection
- **Uptrend**: Recent 6 candles have higher highs AND higher lows than previous 6
- **Downtrend**: Recent 6 candles have lower highs AND lower lows than previous 6

### 2. Pullback Confirmation
- **LONG**: 2–4 consecutive red candles (close < open) after uptrend
- **SHORT**: 2–4 consecutive green candles (close > open) after downtrend

### 3. Entry (Limit Order)
- **LONG**: Previous 2-candle high × (1 + 0.08% buffer)
- **SHORT**: Previous 2-candle low × (1 - 0.08% buffer)

### 4. Stop Loss (Structure-Based)
- **LONG**: Lowest low of last 5 candles
- **SHORT**: Highest high of last 5 candles

### 5. Take Profit (Fixed 1.5R)
- **LONG**: Entry + (Entry - SL) × 1.5
- **SHORT**: Entry - (SL - Entry) × 1.5

## Filters (Non-Optional)

| Filter | Condition | Reason |
|--------|-----------|--------|
| Late Move | Last candle > 1.5× avg of last 10 | Avoid chasing |
| Distance to Entry | Current > entry + 0.2% (LONG) | Avoid missed entries |
| Volatility/Chop | 20-candle range < 0.4% of price | Too choppy, no direction |
| Risk Sanity | Risk < 0.2% or > 1.2% | Noise or oversized |

## Output Example

```
========================================================================================================
SYMBOL     SIGNAL     ENTRY           SL              TP              RISK       REASON
========================================================================================================
BTCUSDT    LONG       68420.00        68100.00        68900.00        0.45%      pullback + breakout
ETHUSDT    SKIP       -               -               -               -          late move
SOLUSDT    NO TRADE   -               -               -               -          no setup
BNBUSDT    SHORT      650.50          651.20          649.10          0.88%      pullback + breakdown
========================================================================================================
```

## Features

- **No indicators**: Pure price-action (highs, lows, closes)
- **Modular**: Easy to tweak individual components
- **Safe**: Strict filters to avoid bad setups
- **Read-only**: No API keys needed, no trading execution
- **Fast**: Scans 10 pairs in seconds

## Testing

```bash
python test_logic.py
```

Verifies trend detection, pullbacks, entry/SL/TP calculation, and filter logic with mock data.

## Future Options (Not Implemented)

- Loop mode (scan every 60s)
- Print only signal changes
- Config file for tuning (buffer, risk limits, etc.)

## Notes

- **Data**: Fetches ~200 5-minute candles per pair from Binance
- **Pair Selection**: Auto-updates based on 24h quote asset volume
- **Rounding**: Prices rounded based on magnitude (BTC ≤ 2 decimals, alts ≤ 6)

---

**This is a scanner, not a prediction system.** It identifies price-action-based continuation patterns with controlled risk. Always backtest and paper-trade first.
