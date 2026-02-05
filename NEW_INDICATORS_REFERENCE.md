# New Indicator Features - Quick Reference

This document provides a quick reference for the newly added indicator features.

## Overview

The indicator storage pipeline has been enhanced with 231 new technical indicators:

- **215 EMA indicators** (periods 2-200, then 250-1000 by 50s)
- **12 candlestick patterns** (pure Python, no TA-Lib required)
- **4 streak/tracking indicators** (consecutive highs/lows, days since prev high/low)

## Quick Start

### Using CLI

```bash
# Compute indicators with all new features (default)
python compute_indicators.py

# Disable specific features
python compute_indicators.py --no-candlestick-patterns
python compute_indicators.py --no-streak-indicators
python compute_indicators.py --no-high-low-days

# Custom EMA periods only
python compute_indicators.py --ema-periods 10 20 50 100 200

# Process specific symbols
python compute_indicators.py --symbols AAPL GOOGL MSFT
```

### Using Python API

```python
from indicator_engine import IndicatorEngine

# Initialize engine
engine = IndicatorEngine("./data/indicators")

# Compute all indicators (default behavior)
result = engine.compute_indicators(
    data,
    sma_periods=[20, 50, 200],
    rsi_periods=[14],
    ema_periods=None,  # Uses default: 2-200, 250-1000
    include_candlestick_patterns=True,
    include_streak_indicators=True,
    include_high_low_days=True
)

# Access specific indicators
ema_50 = result['EMA_50']
hammer_pattern = result['hammer']
consecutive_highs = result['consec_higher_high']
days_since_high = result['days_since_prev_high']
```

## Available Indicators

### 1. Exponential Moving Averages (EMAs)

**Column naming:** `EMA_{period}`

**Available periods:**
- 2 through 200 (every period): `EMA_2`, `EMA_3`, ..., `EMA_200`
- 250 through 1000 (every 50): `EMA_250`, `EMA_300`, ..., `EMA_1000`

**Total:** 215 EMA indicators

**Example:**
```python
# Access EMA indicators
ema_20 = result['EMA_20']
ema_50 = result['EMA_50']
ema_200 = result['EMA_200']
ema_500 = result['EMA_500']
```

### 2. Candlestick Patterns

All patterns return **1** if detected, **0** otherwise.

#### Reversal Patterns

| Column Name | Pattern | Signal |
|------------|---------|--------|
| `engulfing_bull` | Bullish Engulfing | Bullish reversal |
| `engulfing_bear` | Bearish Engulfing | Bearish reversal |
| `hammer` | Hammer | Potential bullish reversal |
| `hanging_man` | Hanging Man | Potential bearish reversal |
| `shooting_star` | Shooting Star | Bearish reversal |
| `harami_bull` | Bullish Harami | Potential bullish reversal |
| `harami_bear` | Bearish Harami | Potential bearish reversal |

#### Special Patterns

| Column Name | Pattern | Signal |
|------------|---------|--------|
| `doji` | Doji | Indecision/potential reversal |
| `dark_cloud` | Dark Cloud Cover | Bearish reversal |
| `piercing` | Piercing Pattern | Bullish reversal |
| `three_white_soldiers` | Three White Soldiers | Strong bullish continuation |
| `three_black_crows` | Three Black Crows | Strong bearish continuation |

**Example:**
```python
# Find days with bullish engulfing pattern
bullish_engulfing_days = result[result['engulfing_bull'] == 1]

# Find days with any reversal pattern
reversals = result[
    (result['engulfing_bull'] == 1) | 
    (result['hammer'] == 1) | 
    (result['shooting_star'] == 1)
]

# Count pattern occurrences
doji_count = result['doji'].sum()
```

### 3. Streak Indicators

Track momentum through consecutive price movements.

| Column Name | Description | Value |
|------------|-------------|-------|
| `consec_higher_high` | Consecutive days with High > previous High | Count of days in streak |
| `consec_lower_low` | Consecutive days with Low < previous Low | Count of days in streak |

**Values:** Integer count of consecutive days (0 when streak breaks)

**Example:**
```python
# Find strong upward momentum (5+ consecutive higher highs)
strong_momentum = result[result['consec_higher_high'] >= 5]

# Find strong downward momentum
strong_decline = result[result['consec_lower_low'] >= 5]

# Check current streak
current_up_streak = result['consec_higher_high'].iloc[-1]
current_down_streak = result['consec_lower_low'].iloc[-1]
```

### 4. High/Low Tracking

Track when stocks reach new highs or lows.

| Column Name | Description | Value |
|------------|-------------|-------|
| `days_since_prev_high` | Days since previous all-time high | Trading days (0 if not a new high) |
| `days_since_prev_low` | Days since previous all-time low | Trading days (0 if not a new low) |

**Lookback window:** 5 years (approximately 1260 trading days)

**Values:**
- **>0**: Number of trading days since the previous record high/low (only on days that set a new record)
- **0**: Not a new high/low

**Example:**
```python
# Find days that set new highs
new_highs = result[result['days_since_prev_high'] > 0]

# Find days that set new lows
new_lows = result[result['days_since_prev_low'] > 0]

# Check if recent high/low
recent_high = result['days_since_prev_high'].iloc[-1] > 0
days_gap = result['days_since_prev_high'].iloc[-1]

# Find breakouts after long consolidation
long_consolidation_breakout = result[result['days_since_prev_high'] > 100]
```

## Integration Examples

### Finding Trading Signals

```python
from indicator_engine import IndicatorEngine

engine = IndicatorEngine("./data/indicators")
data = engine.load_indicators("AAPL")

# Example 1: EMA crossover with pattern confirmation
bullish_signal = (
    (data['EMA_20'] > data['EMA_50']) &  # Short EMA above long EMA
    (data['engulfing_bull'] == 1)         # Bullish engulfing pattern
)

# Example 2: Momentum breakout
momentum_breakout = (
    (data['consec_higher_high'] >= 3) &   # 3+ consecutive higher highs
    (data['days_since_prev_high'] > 0)    # New all-time high
)

# Example 3: Reversal after downtrend
reversal_signal = (
    (data['consec_lower_low'] >= 5) &     # Strong downtrend
    (data['hammer'] == 1)                  # Hammer reversal pattern
)
```

### Screening Multiple Symbols

```python
from indicator_engine import IndicatorEngine

engine = IndicatorEngine("./data/indicators")
symbols = engine.list_available_symbols()

# Find symbols with strong momentum
strong_momentum_symbols = []

for symbol in symbols:
    data = engine.load_indicators(symbol)
    if data is not None:
        latest = data.iloc[-1]
        
        # Check criteria
        if (latest['consec_higher_high'] >= 5 and
            latest['EMA_20'] > latest['EMA_50'] and
            latest['days_since_prev_high'] > 0):
            strong_momentum_symbols.append(symbol)

print(f"Found {len(strong_momentum_symbols)} symbols with strong momentum")
```

### Pattern Analysis

```python
# Analyze pattern frequency over time
patterns = [
    'engulfing_bull', 'engulfing_bear', 'hammer', 
    'doji', 'shooting_star', 'three_white_soldiers'
]

pattern_counts = {}
for pattern in patterns:
    count = data[pattern].sum()
    pattern_counts[pattern] = count

# Find most common patterns
import pandas as pd
pattern_df = pd.DataFrame.from_dict(
    pattern_counts, 
    orient='index', 
    columns=['Count']
).sort_values('Count', ascending=False)

print(pattern_df)
```

## Performance Characteristics

- **EMA computation**: O(n) per period, vectorized using pandas `ewm()`
- **Streak indicators**: O(n) with single pass through data
- **High/Low tracking**: O(n×window) with optimized lookback
- **Candlestick patterns**: O(n) per pattern, fully vectorized

**Storage overhead:**
- Typical: ~50-100KB per symbol for all new indicators
- Format: HDF5 with zlib compression (level 9)

## Configuration

The `config.json` tracks which indicators are computed:

```json
{
  "SYMBOL": {
    "sma_periods": [20, 50, 200],
    "rsi_periods": [14],
    "ema_periods": [2, 3, ..., 200, 250, ..., 1000],
    "candlestick_patterns": true,
    "streak_indicators": true,
    "high_low_days": true
  }
}
```

## Testing

Run the comprehensive test suite:

```bash
python test_new_indicators.py
```

This tests:
- EMA computation for various periods
- Consecutive streak indicators
- Days since high/low tracking
- All 12 candlestick patterns
- Full integration with HDF5 storage
- Config persistence

## Backward Compatibility

All changes are backward compatible:
- Existing code continues to work without modifications
- New features are opt-in via parameters (enabled by default in CLI)
- Existing HDF5 files can be extended with new indicators
- Old indicator data remains accessible

## Notes

- **No TA-Lib required**: All patterns use pure Python implementations
- **Vectorized**: Efficient computation on long price histories
- **Extensible**: Easy to add more patterns or indicators
- **Tested**: Comprehensive test suite with 100% pass rate
- **Secure**: Zero security vulnerabilities (CodeQL verified)

## Support

For issues or questions:
1. Check `IMPLEMENTATION_SUMMARY.md` for detailed implementation notes
2. Review test examples in `test_new_indicators.py`
3. See existing tests in `test_local.py` for integration examples
