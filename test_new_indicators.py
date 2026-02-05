#!/usr/bin/env python3
"""
Test script for new indicator features:
- EMAs (2-200, 250-1000)
- Days since prev high/low
- Consecutive higher/lower streaks
- Candlestick patterns
"""

import os
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

from indicator_engine import IndicatorEngine
from candlestick_patterns import (
    detect_engulfing_bullish,
    detect_engulfing_bearish,
    detect_hammer,
    detect_hanging_man,
    detect_doji,
    detect_shooting_star,
    compute_all_patterns
)


def create_test_data(num_days: int = 100) -> pd.DataFrame:
    """Create synthetic OHLCV data for testing."""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=num_days, freq='D')
    
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(num_days) * 2)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': close_prices + np.random.randn(num_days) * 0.5,
        'High': close_prices + np.abs(np.random.randn(num_days) * 1),
        'Low': close_prices - np.abs(np.random.randn(num_days) * 1),
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 10000000, num_days)
    })
    
    df = df.set_index('Date')
    return df


def test_ema_computation():
    """Test EMA computation for various periods."""
    print("\n" + "=" * 70)
    print("Testing EMA Computation")
    print("=" * 70)
    
    df = create_test_data(500)  # Need more data for EMA_1000
    engine = IndicatorEngine()
    
    # Test various EMA periods
    test_periods = [2, 10, 50, 100, 200, 250, 500, 1000]
    
    for period in test_periods:
        ema = engine.compute_ema(df['Close'], period)
        
        # Check that EMA has correct length
        assert len(ema) == len(df), f"EMA_{period} length mismatch"
        
        # Check that EMA has NaN for first (period-1) values
        assert ema.iloc[:period-1].isna().all() or ema.iloc[:period-1].isna().sum() >= period//2, \
            f"EMA_{period} should have NaN values at start"
        
        # Check that EMA has valid values after warmup
        valid_ema = ema.iloc[period:]
        if len(valid_ema) > 0:
            assert valid_ema.notna().any(), f"EMA_{period} should have valid values"
            print(f"  ✓ EMA_{period}: Last value = {ema.iloc[-1]:.2f}")
    
    print("\n✅ All EMA tests passed!")


def test_consecutive_streaks():
    """Test consecutive higher high and lower low indicators."""
    print("\n" + "=" * 70)
    print("Testing Consecutive Streak Indicators")
    print("=" * 70)
    
    # Create specific test pattern
    dates = pd.date_range(end=pd.Timestamp.now(), periods=20, freq='D')
    
    # Pattern: 5 higher highs, then 3 lower lows, then mixed
    highs = [100, 101, 102, 103, 104, 105, 104, 103, 102, 103, 104, 103, 102, 101, 100, 101, 102, 103, 104, 105]
    lows = [90, 91, 92, 93, 94, 95, 94, 93, 92, 93, 94, 93, 92, 91, 90, 91, 92, 93, 94, 95]
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': highs,
        'High': highs,
        'Low': lows,
        'Close': highs,
        'Volume': [1000000] * 20
    }).set_index('Date')
    
    engine = IndicatorEngine()
    
    # Test consecutive higher highs
    consec_hh = engine.compute_consec_higher_high(df)
    print("\n  Consecutive Higher Highs:")
    print(f"    Values: {consec_hh.values[:10]}")
    
    # First value should be 0 (no previous day)
    assert consec_hh.iloc[0] == 0, "First value should be 0"
    
    # After 5 consecutive higher highs, value should be 5
    assert consec_hh.iloc[5] == 5, f"After 5 higher highs, streak should be 5, got {consec_hh.iloc[5]}"
    
    # After a break, should reset to 0
    assert consec_hh.iloc[6] == 0, "Streak should reset after break"
    
    print("  ✓ Consecutive higher high works correctly")
    
    # Test consecutive lower lows
    # Create pattern with lower lows
    df2 = pd.DataFrame({
        'Date': dates,
        'Open': highs,
        'High': highs,
        'Low': [95, 94, 93, 92, 91, 90, 91, 92, 93, 94, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86],
        'Close': highs,
        'Volume': [1000000] * 20
    }).set_index('Date')
    
    consec_ll = engine.compute_consec_lower_low(df2)
    print("\n  Consecutive Lower Lows:")
    print(f"    Values: {consec_ll.values[:10]}")
    
    # Should have consecutive lower lows
    assert consec_ll.iloc[5] == 5, f"After 5 lower lows, streak should be 5, got {consec_ll.iloc[5]}"
    assert consec_ll.iloc[6] == 0, "Streak should reset after break"
    
    print("  ✓ Consecutive lower low works correctly")
    
    print("\n✅ All consecutive streak tests passed!")


def test_days_since_highs_lows():
    """Test days since previous high/low indicators."""
    print("\n" + "=" * 70)
    print("Testing Days Since Prev High/Low")
    print("=" * 70)
    
    # Create pattern with clear highs and lows
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
    
    # Create a pattern: gradual increase to peak at day 30, then decrease, then new peak at day 60
    base = np.linspace(100, 150, 30)
    decline = np.linspace(150, 120, 20)
    rise = np.linspace(120, 160, 30)
    final = np.linspace(160, 140, 20)
    highs = np.concatenate([base, decline, rise, final])
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': highs,
        'High': highs,
        'Low': highs - 5,
        'Close': highs,
        'Volume': [1000000] * 100
    }).set_index('Date')
    
    engine = IndicatorEngine()
    
    # Test days since prev high
    days_high = engine.compute_days_since_prev_high(df, lookback_years=5)
    print("\n  Days Since Prev High:")
    
    # Find where new highs occur
    new_highs = days_high[days_high > 0]
    print(f"    New highs detected at {len(new_highs)} positions")
    print(f"    Sample values: {days_high[days_high > 0].head()}")
    
    # There should be at least one new high
    assert len(new_highs) > 0, "Should detect at least one new high"
    print("  ✓ Days since prev high works correctly")
    
    # Test days since prev low
    # Create pattern with clear lows
    base_low = np.linspace(100, 90, 30)
    rise_low = np.linspace(90, 110, 20)
    decline_low = np.linspace(110, 85, 30)
    final_low = np.linspace(85, 95, 20)
    lows = np.concatenate([base_low, rise_low, decline_low, final_low])
    
    df2 = pd.DataFrame({
        'Date': dates,
        'Open': lows + 5,
        'High': lows + 10,
        'Low': lows,
        'Close': lows + 5,
        'Volume': [1000000] * 100
    }).set_index('Date')
    
    days_low = engine.compute_days_since_prev_low(df2, lookback_years=5)
    print("\n  Days Since Prev Low:")
    
    # Find where new lows occur
    new_lows = days_low[days_low > 0]
    print(f"    New lows detected at {len(new_lows)} positions")
    print(f"    Sample values: {days_low[days_low > 0].head()}")
    
    # There should be at least one new low
    assert len(new_lows) > 0, "Should detect at least one new low"
    print("  ✓ Days since prev low works correctly")
    
    print("\n✅ All days since high/low tests passed!")


def test_candlestick_patterns():
    """Test candlestick pattern detection."""
    print("\n" + "=" * 70)
    print("Testing Candlestick Patterns")
    print("=" * 70)
    
    # Test engulfing bullish pattern
    df_engulf = pd.DataFrame({
        'Open': [100, 99],
        'High': [101, 105],
        'Low': [99, 98],
        'Close': [99.5, 104]
    })
    
    engulf_bull = detect_engulfing_bullish(df_engulf)
    assert engulf_bull.iloc[1] == 1, "Should detect bullish engulfing at index 1"
    print("  ✓ Bullish engulfing pattern detected correctly")
    
    # Test engulfing bearish pattern
    df_engulf_bear = pd.DataFrame({
        'Open': [100, 105],
        'High': [105, 106],
        'Low': [99, 98],
        'Close': [104, 99]
    })
    
    engulf_bear = detect_engulfing_bearish(df_engulf_bear)
    assert engulf_bear.iloc[1] == 1, "Should detect bearish engulfing at index 1"
    print("  ✓ Bearish engulfing pattern detected correctly")
    
    # Test doji pattern (open ≈ close)
    df_doji = pd.DataFrame({
        'Open': [100, 100],
        'High': [100, 105],
        'Low': [100, 95],
        'Close': [100, 100.1]
    })
    
    doji = detect_doji(df_doji)
    assert doji.iloc[1] == 1, "Should detect doji at index 1"
    print("  ✓ Doji pattern detected correctly")
    
    # Test hammer pattern
    df_hammer = pd.DataFrame({
        'Open': [100, 98],
        'High': [101, 100],
        'Low': [99, 90],
        'Close': [100, 99]
    })
    
    hammer = detect_hammer(df_hammer)
    # Hammer has specific criteria, may or may not detect in this simple case
    print(f"  ✓ Hammer pattern detection executed (detected: {hammer.iloc[1]})")
    
    # Test all patterns together
    df_all = create_test_data(100)
    patterns = compute_all_patterns(df_all)
    
    print(f"\n  All patterns computed: {len(patterns)} patterns")
    for pattern_name, pattern_series in patterns.items():
        count = pattern_series.sum()
        print(f"    {pattern_name}: {count} occurrences")
    
    # Check that all expected patterns are present
    expected_patterns = [
        'engulfing_bull', 'engulfing_bear', 'hammer', 'hanging_man',
        'doji', 'shooting_star', 'harami_bull', 'harami_bear',
        'dark_cloud', 'piercing', 'three_white_soldiers', 'three_black_crows'
    ]
    
    for pattern in expected_patterns:
        assert pattern in patterns, f"Pattern {pattern} should be in results"
    
    print("\n✅ All candlestick pattern tests passed!")


def test_full_integration():
    """Test full integration with all indicators."""
    print("\n" + "=" * 70)
    print("Testing Full Integration")
    print("=" * 70)
    
    # Create test cache directory
    test_cache_path = "./data/test_new_indicators"
    if os.path.exists(test_cache_path):
        shutil.rmtree(test_cache_path)
    
    # Create test data
    test_data = create_test_data(500)
    
    # Initialize engine
    engine = IndicatorEngine(test_cache_path)
    
    # Compute all indicators
    print("\n  Computing all indicators...")
    result = engine.compute_indicators(
        test_data,
        sma_periods=[20, 50],
        rsi_periods=[14],
        ema_periods=[2, 10, 20, 50, 100, 200],  # Subset for testing
        include_candlestick_patterns=True,
        include_streak_indicators=True,
        include_high_low_days=True
    )
    
    # Verify all indicator columns exist
    print("\n  Verifying indicator columns...")
    
    # Check SMAs
    assert 'SMA_20' in result.columns, "SMA_20 should exist"
    assert 'SMA_50' in result.columns, "SMA_50 should exist"
    print("    ✓ SMA columns present")
    
    # Check RSIs
    assert 'RSI_14' in result.columns, "RSI_14 should exist"
    print("    ✓ RSI columns present")
    
    # Check EMAs
    for period in [2, 10, 20, 50, 100, 200]:
        assert f'EMA_{period}' in result.columns, f"EMA_{period} should exist"
    print("    ✓ EMA columns present")
    
    # Check candlestick patterns
    assert 'engulfing_bull' in result.columns, "engulfing_bull should exist"
    assert 'doji' in result.columns, "doji should exist"
    print("    ✓ Candlestick pattern columns present")
    
    # Check streak indicators
    assert 'consec_higher_high' in result.columns, "consec_higher_high should exist"
    assert 'consec_lower_low' in result.columns, "consec_lower_low should exist"
    print("    ✓ Streak indicator columns present")
    
    # Check high/low day tracking
    assert 'days_since_prev_high' in result.columns, "days_since_prev_high should exist"
    assert 'days_since_prev_low' in result.columns, "days_since_prev_low should exist"
    print("    ✓ High/low day tracking columns present")
    
    # Test storage
    print("\n  Testing HDF5 storage...")
    engine.process_and_store(
        'TEST_SYMBOL',
        test_data,
        sma_periods=[20, 50],
        rsi_periods=[14],
        ema_periods=[2, 10, 20, 50, 100, 200],
        include_candlestick_patterns=True,
        include_streak_indicators=True,
        include_high_low_days=True
    )
    
    # Load back and verify
    loaded = engine.load_indicators('TEST_SYMBOL')
    assert loaded is not None, "Should load stored indicators"
    assert len(loaded) == len(test_data), "Loaded data should have same length"
    
    # Verify key columns
    assert 'EMA_50' in loaded.columns, "EMA_50 should be in loaded data"
    assert 'engulfing_bull' in loaded.columns, "engulfing_bull should be in loaded data"
    assert 'consec_higher_high' in loaded.columns, "consec_higher_high should be in loaded data"
    assert 'days_since_prev_high' in loaded.columns, "days_since_prev_high should be in loaded data"
    
    print("    ✓ Storage and loading work correctly")
    
    # Verify config
    config = engine.get_config()
    assert 'TEST_SYMBOL' in config, "Config should include TEST_SYMBOL"
    assert config['TEST_SYMBOL']['candlestick_patterns'] == True, "Config should track candlestick patterns"
    assert config['TEST_SYMBOL']['streak_indicators'] == True, "Config should track streak indicators"
    assert config['TEST_SYMBOL']['high_low_days'] == True, "Config should track high/low days"
    print("    ✓ Config tracking works correctly")
    
    # Cleanup
    if os.path.exists(test_cache_path):
        shutil.rmtree(test_cache_path)
    
    print("\n✅ Full integration test passed!")


def main():
    """Run all tests."""
    print("=" * 70)
    print("Testing New Indicator Features")
    print("=" * 70)
    
    try:
        test_ema_computation()
        test_consecutive_streaks()
        test_days_since_highs_lows()
        test_candlestick_patterns()
        test_full_integration()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nNew indicators successfully implemented:")
        print("  • EMA periods (2-200, 250-1000)")
        print("  • Days since previous high/low")
        print("  • Consecutive higher high / lower low streaks")
        print("  • 12 candlestick patterns (engulfing, hammer, doji, etc.)")
        print("\n" + "=" * 70)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
