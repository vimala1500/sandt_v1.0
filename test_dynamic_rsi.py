#!/usr/bin/env python3
"""
Test script for dynamic RSI period caching feature
"""

import os
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

from data_loader import DataLoader
from indicator_engine import IndicatorEngine
from scanner import Scanner
from backtest_engine import BacktestEngine


def create_test_price_data(symbol: str, num_days: int = 100) -> pd.DataFrame:
    """Create synthetic price data for testing."""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=num_days, freq='D')
    
    # Generate synthetic OHLCV data
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


def test_dynamic_rsi_caching():
    """Test that RSI periods are dynamically computed and cached."""
    
    print("=" * 70)
    print("Testing Dynamic RSI Period Caching")
    print("=" * 70)
    
    # Setup test directories
    test_cache_path = "./data/test_dynamic_rsi"
    if os.path.exists(test_cache_path):
        shutil.rmtree(test_cache_path)
    
    print("\n1. Creating test data...")
    test_symbols = ['TEST_A', 'TEST_B', 'TEST_C']
    data_dict = {symbol: create_test_price_data(symbol) for symbol in test_symbols}
    print(f"   ✓ Created {len(test_symbols)} test symbols")
    
    # Step 2: Initialize with only RSI(14)
    print("\n2. Computing initial indicators with only RSI(14)...")
    engine = IndicatorEngine(test_cache_path)
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50],
        rsi_periods=[14],  # Only RSI 14 initially
        show_progress=False
    )
    
    # Verify RSI(14) exists
    test_symbol = test_symbols[0]
    data = engine.load_indicators(test_symbol)
    assert 'RSI_14' in data.columns, "RSI_14 should exist"
    print(f"   ✓ RSI_14 computed: {data['RSI_14'].iloc[-1]:.2f}")
    
    # Verify RSI(21) does NOT exist yet
    assert 'RSI_21' not in data.columns, "RSI_21 should not exist yet"
    print("   ✓ RSI_21 not yet computed (as expected)")
    
    # Step 3: Test has_rsi_period method
    print("\n3. Testing has_rsi_period method...")
    assert engine.has_rsi_period(test_symbol, 14), "Should find RSI_14"
    assert not engine.has_rsi_period(test_symbol, 21), "Should not find RSI_21"
    print("   ✓ has_rsi_period works correctly")
    
    # Step 4: Test compute_and_cache_rsi_period
    print("\n4. Testing dynamic RSI period computation...")
    success = engine.compute_and_cache_rsi_period(test_symbol, 21)
    assert success, "Should successfully compute RSI_21"
    print("   ✓ RSI_21 computed on-demand")
    
    # Verify RSI(21) now exists
    data = engine.load_indicators(test_symbol)
    assert 'RSI_21' in data.columns, "RSI_21 should now exist"
    print(f"   ✓ RSI_21 value: {data['RSI_21'].iloc[-1]:.2f}")
    
    # Verify config was updated
    config = engine.get_config()
    assert 21 in config[test_symbol]['rsi_periods'], "Config should include RSI_21"
    print(f"   ✓ Config updated: {config[test_symbol]['rsi_periods']}")
    
    # Step 5: Test ensure_rsi_period (should not recompute)
    print("\n5. Testing ensure_rsi_period (already exists)...")
    success = engine.ensure_rsi_period(test_symbol, 21)
    assert success, "Should return True for existing period"
    print("   ✓ ensure_rsi_period returns True for existing period")
    
    # Step 6: Test ensure_rsi_period (needs computation)
    print("\n6. Testing ensure_rsi_period (needs computation)...")
    success = engine.ensure_rsi_period(test_symbol, 30)
    assert success, "Should successfully compute RSI_30"
    
    data = engine.load_indicators(test_symbol)
    assert 'RSI_30' in data.columns, "RSI_30 should now exist"
    print(f"   ✓ RSI_30 computed on-demand: {data['RSI_30'].iloc[-1]:.2f}")
    
    # Step 7: Test with Scanner
    print("\n7. Testing Scanner with dynamic RSI periods...")
    backtest_engine = BacktestEngine("./data/test_backtests")
    scanner = Scanner(engine, backtest_engine)
    
    # Scan with RSI(7) which doesn't exist yet
    print("   Testing scan with RSI(7) (not pre-computed)...")
    results = scanner.scan_rsi_oversold(
        symbols=test_symbols,
        rsi_period=7,
        threshold=50  # High threshold to catch results
    )
    
    # Verify RSI(7) was computed
    data = engine.load_indicators(test_symbol)
    assert 'RSI_7' in data.columns, "RSI_7 should be computed by scanner"
    print(f"   ✓ Scanner auto-computed RSI_7: {data['RSI_7'].iloc[-1]:.2f}")
    print(f"   ✓ Scan found {len(results)} results")
    
    # Step 8: Test persistence
    print("\n8. Testing cache persistence...")
    engine2 = IndicatorEngine(test_cache_path)
    data2 = engine2.load_indicators(test_symbol)
    
    # Verify all computed RSI periods are still there
    expected_periods = [7, 14, 21, 30]
    for period in expected_periods:
        col_name = f"RSI_{period}"
        assert col_name in data2.columns, f"{col_name} should persist"
        print(f"   ✓ {col_name} persisted: {data2[col_name].iloc[-1]:.2f}")
    
    # Step 9: Test with multiple symbols
    print("\n9. Testing with multiple symbols...")
    for symbol in test_symbols:
        success = engine.ensure_rsi_period(symbol, 50)
        assert success, f"Should compute RSI_50 for {symbol}"
        
        data = engine.load_indicators(symbol)
        assert 'RSI_50' in data.columns, f"RSI_50 should exist for {symbol}"
    print("   ✓ RSI_50 computed for all test symbols")
    
    # Step 10: Summary
    print("\n" + "=" * 70)
    print("✅ All Dynamic RSI Caching Tests Passed!")
    print("=" * 70)
    
    final_config = engine.get_config()
    print(f"\nFinal cached RSI periods for {test_symbol}:")
    print(f"  {final_config[test_symbol]['rsi_periods']}")
    
    print("\nKey Features Verified:")
    print("  ✓ RSI periods are computed on-demand when requested")
    print("  ✓ Newly computed periods are cached in HDF5")
    print("  ✓ Config file is updated with new periods")
    print("  ✓ Scanner automatically computes missing RSI periods")
    print("  ✓ Cached periods persist across engine instances")
    print("  ✓ Works for multiple symbols")
    
    # Cleanup
    print("\n10. Cleanup...")
    if os.path.exists(test_cache_path):
        shutil.rmtree(test_cache_path)
    print("   ✓ Test cache directory removed")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        test_dynamic_rsi_caching()
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
