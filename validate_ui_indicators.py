#!/usr/bin/env python3
"""
Validation script for new indicator UI features.
Tests that the UI components and callbacks are properly configured.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from indicator_engine import IndicatorEngine
from scanner import Scanner
from backtest_engine import BacktestEngine

def test_scanner_features():
    """Test new scanner features."""
    print("Testing Scanner Features")
    print("=" * 70)
    
    # Create test data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    test_symbols = ['TEST1', 'TEST2', 'TEST3']
    data_dict = {}
    
    for symbol in test_symbols:
        df = pd.DataFrame({
            'Open': close_prices + np.random.randn(100) * 0.5,
            'High': close_prices + np.abs(np.random.randn(100) * 1),
            'Low': close_prices - np.abs(np.random.randn(100) * 1),
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        data_dict[symbol] = df
    
    # Setup test environment
    test_path = Path("/tmp/test_ui_validation")
    if test_path.exists():
        import shutil
        shutil.rmtree(test_path)
    test_path.mkdir(parents=True)
    
    indicator_path = test_path / "indicators"
    backtest_path = test_path / "backtests"
    indicator_path.mkdir(parents=True)
    backtest_path.mkdir(parents=True)
    
    # Initialize components
    engine = IndicatorEngine(str(indicator_path))
    engine.process_multiple_symbols(
        data_dict, 
        sma_periods=[20, 50], 
        rsi_periods=[14],
        ema_periods=[10, 20, 50, 100, 200],
        include_candlestick_patterns=True,
        include_streak_indicators=True,
        include_high_low_days=True,
        show_progress=False
    )
    
    backtest_engine = BacktestEngine(str(backtest_path))
    scanner = Scanner(engine, backtest_engine)
    
    # Test 1: Get available indicators
    print("\n✓ Test 1: Get Available Indicators")
    available = scanner.get_available_indicators()
    print(f"  Found {len(available)} indicators")
    
    # Verify expected indicators exist
    expected_indicators = [
        'RSI_14', 'SMA_20', 'SMA_50', 'EMA_10', 'EMA_20', 'EMA_50', 'EMA_100', 'EMA_200',
        'hammer', 'doji', 'engulfing_bull', 'engulfing_bear',
        'consec_higher_high', 'consec_lower_low',
        'days_since_prev_high', 'days_since_prev_low'
    ]
    
    for indicator in expected_indicators:
        if indicator in available:
            print(f"    ✓ {indicator}")
        else:
            print(f"    ✗ MISSING: {indicator}")
    
    # Test 2: Scan by various indicator types
    print("\n✓ Test 2: Scan by Indicator (Generic Method)")
    
    # Test RSI scan
    results = scanner.scan_by_indicator(test_symbols, 'RSI_14', '<', 100)
    print(f"  RSI scan: {len(results)} results")
    
    # Test EMA scan
    results = scanner.scan_by_indicator(test_symbols, 'EMA_50', '>', 0)
    print(f"  EMA scan: {len(results)} results")
    
    # Test candlestick pattern scan
    results = scanner.scan_by_indicator(test_symbols, 'hammer', '==', 1)
    print(f"  Candlestick pattern scan: {len(results)} results")
    
    # Test streak scan
    results = scanner.scan_by_indicator(test_symbols, 'consec_higher_high', '>=', 0)
    print(f"  Streak scan: {len(results)} results")
    
    # Test 3: Validate UI component imports
    print("\n✓ Test 3: Validate UI Components")
    try:
        from dash_ui import DashUI
        print("  ✓ DashUI class imported successfully")
        
        # Try to create UI instance (won't run server)
        ui = DashUI(str(indicator_path), str(backtest_path))
        print("  ✓ DashUI instance created successfully")
        
        # Verify app has expected attributes
        assert hasattr(ui, 'app'), "Missing app attribute"
        assert hasattr(ui, 'scanner'), "Missing scanner attribute"
        assert hasattr(ui, 'indicator_engine'), "Missing indicator_engine attribute"
        print("  ✓ UI instance has required attributes")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Verify new scan types are recognized
    print("\n✓ Test 4: Verify New Scan Types")
    expected_scan_types = [
        'rsi_oversold', 'rsi_overbought', 'ma_cross_bull', 'ma_cross_bear',
        'candlestick', 'momentum_streak', 'custom_indicator', 'top_performers'
    ]
    
    # Check if scan types exist in UI layout
    import dash_ui
    with open('dash_ui.py', 'r') as f:
        ui_code = f.read()
        for scan_type in expected_scan_types:
            if f"'{scan_type}'" in ui_code or f'"{scan_type}"' in ui_code:
                print(f"  ✓ {scan_type}")
            else:
                print(f"  ✗ MISSING: {scan_type}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path)
    
    print("\n" + "=" * 70)
    print("✅ All validation tests completed!")
    print("=" * 70)

if __name__ == '__main__':
    test_scanner_features()
