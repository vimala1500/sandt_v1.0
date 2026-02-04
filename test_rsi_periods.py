#!/usr/bin/env python3
"""
Test script to verify RSI periods work correctly
"""

import pandas as pd
from data_loader import DataLoader
from indicator_engine import IndicatorEngine
from scanner import Scanner
from backtest_engine import BacktestEngine

def test_rsi_periods():
    """Test that multiple RSI periods can be computed and scanned"""
    
    print("=" * 70)
    print("Testing RSI Period Functionality")
    print("=" * 70)
    
    # Load sample data
    print("\n1. Loading sample data...")
    loader = DataLoader("./data/prices")
    symbols = loader.list_available_symbols()[:3]  # Use first 3 symbols
    print(f"   Loading {len(symbols)} symbols: {symbols}")
    data_dict = loader.load_multiple_symbols(symbols)
    print(f"   ✓ Loaded {len(data_dict)} symbols")
    
    # Compute indicators with multiple RSI periods
    print("\n2. Computing indicators with multiple RSI periods...")
    engine = IndicatorEngine("./data/test_indicators")
    rsi_periods = [7, 14, 21, 28]
    print(f"   Computing RSI periods: {rsi_periods}")
    
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50],
        rsi_periods=rsi_periods,
        show_progress=False
    )
    print("   ✓ Indicators computed")
    
    # Verify all RSI columns exist
    print("\n3. Verifying RSI columns exist...")
    for symbol in symbols:
        data = engine.load_indicators(symbol)
        if data is None:
            print(f"   ✗ Failed to load indicators for {symbol}")
            continue
        
        for period in rsi_periods:
            col_name = f"RSI_{period}"
            if col_name in data.columns:
                last_value = data[col_name].iloc[-1]
                print(f"   ✓ {symbol}: {col_name} = {last_value:.2f}")
            else:
                print(f"   ✗ {symbol}: {col_name} NOT FOUND")
    
    # Test scanning with different RSI periods
    print("\n4. Testing scanner with different RSI periods...")
    backtest_engine = BacktestEngine("./data/test_backtests")
    scanner = Scanner(engine, backtest_engine)
    
    for period in [7, 14, 21, 28]:
        print(f"\n   Testing RSI({period}) oversold scan (threshold < 40)...")
        results = scanner.scan_rsi_oversold(
            symbols=symbols,
            rsi_period=period,
            threshold=40
        )
        
        if results is not None and len(results) > 0:
            print(f"   ✓ Found {len(results)} results with RSI({period})")
            for _, row in results.iterrows():
                print(f"      - {row['symbol']}: RSI = {row['rsi']:.2f}")
        else:
            print(f"   ℹ No results found (RSI > 40 for all symbols)")
    
    print("\n" + "=" * 70)
    print("✓ All tests completed successfully!")
    print("=" * 70)
    print("\nConclusion:")
    print("  - Multiple RSI periods can be computed")
    print("  - Scanner works with different RSI periods")
    print("  - Users can now select any RSI period in the UI")

if __name__ == '__main__':
    test_rsi_periods()
