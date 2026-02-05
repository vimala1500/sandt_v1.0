"""
Candlestick Pattern Detection Module
====================================
Pure Python implementation of common candlestick patterns.
Vectorized for efficient computation on long price histories.

Patterns Implemented:
- Bullish Engulfing
- Bearish Engulfing
- Hammer
- Hanging Man
- Doji
- Shooting Star
- Bullish Harami
- Bearish Harami
- Dark Cloud Cover
- Piercing Pattern
- Three White Soldiers
- Three Black Crows
"""

import pandas as pd
import numpy as np
from typing import Dict


def compute_body_size(df: pd.DataFrame) -> pd.Series:
    """Compute the size of the candle body."""
    return abs(df['Close'] - df['Open'])


def compute_upper_shadow(df: pd.DataFrame) -> pd.Series:
    """Compute the upper shadow (wick) length."""
    return df['High'] - df[['Open', 'Close']].max(axis=1)


def compute_lower_shadow(df: pd.DataFrame) -> pd.Series:
    """Compute the lower shadow (tail) length."""
    return df[['Open', 'Close']].min(axis=1) - df['Low']


def compute_candle_range(df: pd.DataFrame) -> pd.Series:
    """Compute the total candle range (High - Low)."""
    return df['High'] - df['Low']


def is_bullish(df: pd.DataFrame) -> pd.Series:
    """Return True where Close > Open (bullish candle)."""
    return df['Close'] > df['Open']


def is_bearish(df: pd.DataFrame) -> pd.Series:
    """Return True where Close < Open (bearish candle)."""
    return df['Close'] < df['Open']


def detect_engulfing_bullish(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bullish Engulfing pattern.
    
    Criteria:
    - Previous candle is bearish (red)
    - Current candle is bullish (green)
    - Current candle body completely engulfs previous candle body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bearish = is_bearish(df).shift(1)
    curr_bullish = is_bullish(df)
    
    # Current open < previous close AND current close > previous open
    engulfs = (df['Open'] < df['Close'].shift(1)) & (df['Close'] > df['Open'].shift(1))
    
    pattern = prev_bearish & curr_bullish & engulfs
    return pattern.astype(int).fillna(0)


def detect_engulfing_bearish(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bearish Engulfing pattern.
    
    Criteria:
    - Previous candle is bullish (green)
    - Current candle is bearish (red)
    - Current candle body completely engulfs previous candle body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bullish = is_bullish(df).shift(1)
    curr_bearish = is_bearish(df)
    
    # Current open > previous close AND current close < previous open
    engulfs = (df['Open'] > df['Close'].shift(1)) & (df['Close'] < df['Open'].shift(1))
    
    pattern = prev_bullish & curr_bearish & engulfs
    return pattern.astype(int).fillna(0)


def detect_hammer(df: pd.DataFrame) -> pd.Series:
    """
    Detect Hammer pattern.
    
    Criteria:
    - Small body at upper end of range
    - Lower shadow at least 2x body size
    - Upper shadow very small or absent
    - Appears after downtrend (bullish reversal)
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    body = compute_body_size(df)
    lower_shadow = compute_lower_shadow(df)
    upper_shadow = compute_upper_shadow(df)
    candle_range = compute_candle_range(df)
    
    # Small body (less than 30% of range)
    small_body = body < (0.3 * candle_range)
    
    # Long lower shadow (at least 2x body)
    long_lower = lower_shadow >= (2 * body)
    
    # Small upper shadow (less than 10% of range)
    small_upper = upper_shadow < (0.1 * candle_range)
    
    # Body at upper part of range
    body_at_top = (df[['Open', 'Close']].min(axis=1) - df['Low']) >= (0.6 * candle_range)
    
    pattern = small_body & long_lower & small_upper & body_at_top
    return pattern.astype(int).fillna(0)


def detect_hanging_man(df: pd.DataFrame) -> pd.Series:
    """
    Detect Hanging Man pattern.
    
    Criteria:
    - Small body at upper end of range
    - Lower shadow at least 2x body size
    - Upper shadow very small or absent
    - Appears after uptrend (bearish reversal)
    
    Note: Technically same shape as hammer, but context differs
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    # Same shape as hammer
    body = compute_body_size(df)
    lower_shadow = compute_lower_shadow(df)
    upper_shadow = compute_upper_shadow(df)
    candle_range = compute_candle_range(df)
    
    small_body = body < (0.3 * candle_range)
    long_lower = lower_shadow >= (2 * body)
    small_upper = upper_shadow < (0.1 * candle_range)
    body_at_top = (df[['Open', 'Close']].min(axis=1) - df['Low']) >= (0.6 * candle_range)
    
    pattern = small_body & long_lower & small_upper & body_at_top
    return pattern.astype(int).fillna(0)


def detect_doji(df: pd.DataFrame) -> pd.Series:
    """
    Detect Doji pattern.
    
    Criteria:
    - Very small body (Open ≈ Close)
    - Body is less than 5% of the candle range
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    body = compute_body_size(df)
    candle_range = compute_candle_range(df)
    
    # Very small body relative to range
    very_small_body = body < (0.05 * candle_range)
    
    # Ensure there's some range (not a flat line)
    has_range = candle_range > 0
    
    pattern = very_small_body & has_range
    return pattern.astype(int).fillna(0)


def detect_shooting_star(df: pd.DataFrame) -> pd.Series:
    """
    Detect Shooting Star pattern.
    
    Criteria:
    - Small body at lower end of range
    - Upper shadow at least 2x body size
    - Lower shadow very small or absent
    - Bearish reversal signal
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    body = compute_body_size(df)
    lower_shadow = compute_lower_shadow(df)
    upper_shadow = compute_upper_shadow(df)
    candle_range = compute_candle_range(df)
    
    # Small body (less than 30% of range)
    small_body = body < (0.3 * candle_range)
    
    # Long upper shadow (at least 2x body)
    long_upper = upper_shadow >= (2 * body)
    
    # Small lower shadow (less than 10% of range)
    small_lower = lower_shadow < (0.1 * candle_range)
    
    # Body at bottom part of range
    body_at_bottom = (df['High'] - df[['Open', 'Close']].max(axis=1)) >= (0.6 * candle_range)
    
    pattern = small_body & long_upper & small_lower & body_at_bottom
    return pattern.astype(int).fillna(0)


def detect_harami_bullish(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bullish Harami pattern.
    
    Criteria:
    - Previous candle is large bearish
    - Current candle is small bullish
    - Current candle body is within previous candle body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bearish = is_bearish(df).shift(1)
    curr_bullish = is_bullish(df)
    
    prev_body = compute_body_size(df).shift(1)
    curr_body = compute_body_size(df)
    
    # Previous candle is large
    prev_large = prev_body > (0.3 * compute_candle_range(df).shift(1))
    
    # Current body is smaller
    curr_smaller = curr_body < prev_body
    
    # Current is inside previous body
    inside = (df['Open'] > df['Close'].shift(1)) & (df['Close'] < df['Open'].shift(1))
    
    pattern = prev_bearish & curr_bullish & prev_large & curr_smaller & inside
    return pattern.astype(int).fillna(0)


def detect_harami_bearish(df: pd.DataFrame) -> pd.Series:
    """
    Detect Bearish Harami pattern.
    
    Criteria:
    - Previous candle is large bullish
    - Current candle is small bearish
    - Current candle body is within previous candle body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bullish = is_bullish(df).shift(1)
    curr_bearish = is_bearish(df)
    
    prev_body = compute_body_size(df).shift(1)
    curr_body = compute_body_size(df)
    
    # Previous candle is large
    prev_large = prev_body > (0.3 * compute_candle_range(df).shift(1))
    
    # Current body is smaller
    curr_smaller = curr_body < prev_body
    
    # Current is inside previous body
    inside = (df['Open'] < df['Close'].shift(1)) & (df['Close'] > df['Open'].shift(1))
    
    pattern = prev_bullish & curr_bearish & prev_large & curr_smaller & inside
    return pattern.astype(int).fillna(0)


def detect_dark_cloud_cover(df: pd.DataFrame) -> pd.Series:
    """
    Detect Dark Cloud Cover pattern.
    
    Criteria:
    - Previous candle is bullish
    - Current candle is bearish
    - Current opens above previous high
    - Current closes below midpoint of previous body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bullish = is_bullish(df).shift(1)
    curr_bearish = is_bearish(df)
    
    # Current opens above previous high
    opens_above = df['Open'] > df['High'].shift(1)
    
    # Current closes below midpoint of previous body
    prev_midpoint = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    closes_below_mid = df['Close'] < prev_midpoint
    
    pattern = prev_bullish & curr_bearish & opens_above & closes_below_mid
    return pattern.astype(int).fillna(0)


def detect_piercing_pattern(df: pd.DataFrame) -> pd.Series:
    """
    Detect Piercing Pattern.
    
    Criteria:
    - Previous candle is bearish
    - Current candle is bullish
    - Current opens below previous low
    - Current closes above midpoint of previous body
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    prev_bearish = is_bearish(df).shift(1)
    curr_bullish = is_bullish(df)
    
    # Current opens below previous low
    opens_below = df['Open'] < df['Low'].shift(1)
    
    # Current closes above midpoint of previous body
    prev_midpoint = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    closes_above_mid = df['Close'] > prev_midpoint
    
    pattern = prev_bearish & curr_bullish & opens_below & closes_above_mid
    return pattern.astype(int).fillna(0)


def detect_three_white_soldiers(df: pd.DataFrame) -> pd.Series:
    """
    Detect Three White Soldiers pattern.
    
    Criteria:
    - Three consecutive bullish candles
    - Each opens within previous body
    - Each closes higher than previous
    - Each has relatively small shadows
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    bullish = is_bullish(df)
    body = compute_body_size(df)
    candle_range = compute_candle_range(df)
    
    # Three consecutive bullish candles
    three_bullish = bullish & bullish.shift(1) & bullish.shift(2)
    
    # Each opens within previous body
    opens_in_body_1 = (df['Open'] > df['Open'].shift(1)) & (df['Open'] < df['Close'].shift(1))
    opens_in_body_2 = (df['Open'].shift(1) > df['Open'].shift(2)) & (df['Open'].shift(1) < df['Close'].shift(2))
    
    # Each closes higher
    closes_higher = (df['Close'] > df['Close'].shift(1)) & (df['Close'].shift(1) > df['Close'].shift(2))
    
    # Bodies are reasonably large (> 50% of range)
    large_bodies = (body > 0.5 * candle_range) & \
                   (body.shift(1) > 0.5 * candle_range.shift(1)) & \
                   (body.shift(2) > 0.5 * candle_range.shift(2))
    
    pattern = three_bullish & opens_in_body_1 & opens_in_body_2 & closes_higher & large_bodies
    return pattern.astype(int).fillna(0)


def detect_three_black_crows(df: pd.DataFrame) -> pd.Series:
    """
    Detect Three Black Crows pattern.
    
    Criteria:
    - Three consecutive bearish candles
    - Each opens within previous body
    - Each closes lower than previous
    - Each has relatively small shadows
    
    Returns:
        Series with 1 where pattern detected, 0 otherwise
    """
    bearish = is_bearish(df)
    body = compute_body_size(df)
    candle_range = compute_candle_range(df)
    
    # Three consecutive bearish candles
    three_bearish = bearish & bearish.shift(1) & bearish.shift(2)
    
    # Each opens within previous body
    opens_in_body_1 = (df['Open'] < df['Open'].shift(1)) & (df['Open'] > df['Close'].shift(1))
    opens_in_body_2 = (df['Open'].shift(1) < df['Open'].shift(2)) & (df['Open'].shift(1) > df['Close'].shift(2))
    
    # Each closes lower
    closes_lower = (df['Close'] < df['Close'].shift(1)) & (df['Close'].shift(1) < df['Close'].shift(2))
    
    # Bodies are reasonably large (> 50% of range)
    large_bodies = (body > 0.5 * candle_range) & \
                   (body.shift(1) > 0.5 * candle_range.shift(1)) & \
                   (body.shift(2) > 0.5 * candle_range.shift(2))
    
    pattern = three_bearish & opens_in_body_1 & opens_in_body_2 & closes_lower & large_bodies
    return pattern.astype(int).fillna(0)


def compute_all_patterns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Compute all candlestick patterns.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Dictionary mapping pattern name to detection series
    """
    patterns = {
        'engulfing_bull': detect_engulfing_bullish(df),
        'engulfing_bear': detect_engulfing_bearish(df),
        'hammer': detect_hammer(df),
        'hanging_man': detect_hanging_man(df),
        'doji': detect_doji(df),
        'shooting_star': detect_shooting_star(df),
        'harami_bull': detect_harami_bullish(df),
        'harami_bear': detect_harami_bearish(df),
        'dark_cloud': detect_dark_cloud_cover(df),
        'piercing': detect_piercing_pattern(df),
        'three_white_soldiers': detect_three_white_soldiers(df),
        'three_black_crows': detect_three_black_crows(df),
    }
    
    return patterns
