#!/usr/bin/env python3
"""
Manual demonstration of dynamic RSI period caching with real data
"""

import os
from data_loader import DataLoader
from indicator_engine import IndicatorEngine
from scanner import Scanner
from backtest_engine import BacktestEngine


def demo_dynamic_rsi():
    """Demonstrate the dynamic RSI caching feature with real data."""
    
    print("=" * 70)
    print("Dynamic RSI Period Caching - Live Demo")
    print("=" * 70)
    
    # Load real data
    print("\n1. Loading sample stock data...")
    loader = DataLoader("./data/prices")
    symbols = loader.list_available_symbols()[:5]  # Use first 5 symbols
    
    if not symbols:
        print("❌ No price data found. Please ensure Parquet files exist in ./data/prices/")
        return
    
    print(f"   ✓ Found symbols: {symbols}")
    data_dict = loader.load_multiple_symbols(symbols)
    print(f"   ✓ Loaded {len(data_dict)} symbols")
    
    # Initialize with standard RSI periods
    print("\n2. Computing initial indicators with RSI(14) and RSI(21)...")
    indicator_path = "./data/demo_dynamic_indicators"
    
    # Clean up if exists
    if os.path.exists(indicator_path):
        import shutil
        shutil.rmtree(indicator_path)
    
    engine = IndicatorEngine(indicator_path)
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50],
        rsi_periods=[14, 21],  # Only compute RSI 14 and 21 initially
        show_progress=False
    )
    
    # Check what's available
    test_symbol = symbols[0]
    data = engine.load_indicators(test_symbol)
    print(f"   ✓ Initial RSI columns for {test_symbol}: ", end="")
    rsi_cols = [col for col in data.columns if col.startswith('RSI_')]
    print(rsi_cols)
    
    print(f"\n   Latest values for {test_symbol}:")
    for col in rsi_cols:
        print(f"     {col}: {data[col].iloc[-1]:.2f}")
    
    # Now use scanner with a different RSI period
    print("\n3. Running scan with RSI(30) - not pre-computed...")
    backtest_engine = BacktestEngine("./data/demo_backtests")
    scanner = Scanner(engine, backtest_engine)
    
    print("   Scanning for oversold stocks with RSI(30) < 40...")
    results = scanner.scan_rsi_oversold(
        symbols=symbols,
        rsi_period=30,  # This period was not pre-computed!
        threshold=40
    )
    
    print(f"   ✓ Scan completed! Found {len(results)} results")
    if len(results) > 0:
        print("\n   Results:")
        for _, row in results.iterrows():
            print(f"     {row['symbol']}: RSI(30) = {row['rsi']:.2f}")
    
    # Verify RSI(30) is now cached
    print("\n4. Verifying RSI(30) is now cached...")
    data = engine.load_indicators(test_symbol)
    rsi_cols = [col for col in data.columns if col.startswith('RSI_')]
    print(f"   ✓ RSI columns for {test_symbol}: {rsi_cols}")
    
    if 'RSI_30' in data.columns:
        print(f"   ✓ RSI(30) is now cached: {data['RSI_30'].iloc[-1]:.2f}")
    
    # Show config
    config = engine.get_config()
    print(f"\n   Config for {test_symbol}:")
    print(f"     RSI periods: {config[test_symbol]['rsi_periods']}")
    
    # Test with another custom period
    print("\n5. Testing another custom RSI period (RSI 7)...")
    print("   Scanning for oversold stocks with RSI(7) < 30...")
    results = scanner.scan_rsi_oversold(
        symbols=symbols,
        rsi_period=7,
        threshold=30
    )
    print(f"   ✓ Scan completed! Found {len(results)} results")
    
    # Final verification
    print("\n6. Final cache state...")
    data = engine.load_indicators(test_symbol)
    rsi_cols = sorted([col for col in data.columns if col.startswith('RSI_')])
    print(f"   All cached RSI periods for {test_symbol}:")
    for col in rsi_cols:
        period = col.split('_')[1]
        value = data[col].iloc[-1]
        print(f"     RSI({period}): {value:.2f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Dynamic RSI Caching Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  • Initially computed: RSI(14) and RSI(21)")
    print("  • User requested: RSI(30) and RSI(7)")
    print("  • System automatically computed and cached both on-demand")
    print("  • Next time these periods are requested, they load instantly from cache")
    print("\nBenefit:")
    print("  Users can now enter ANY RSI period in the UI, and the system")
    print("  will compute and cache it automatically!")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        demo_dynamic_rsi()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
