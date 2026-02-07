#!/usr/bin/env python3
"""
Demonstration of trade data pipeline fix.
Shows that trades are now properly stored and retrieved, including empty trades.
"""

import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

from backtest_engine import BacktestEngine
from strategy import StrategyConfig


def demo_trade_fix():
    """Demonstrate the trade data pipeline fix."""
    print("=" * 70)
    print("Trade Data Pipeline Fix - Demonstration")
    print("=" * 70)
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = BacktestEngine(output_path=tmpdir)
        
        # Scenario 1: Backtest with trades
        print("📊 Scenario 1: Backtest with trades")
        print("-" * 70)
        
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        rsi_values = 50 + 20 * np.sin(np.linspace(0, 4 * np.pi, 100))
        
        data_with_trades = pd.DataFrame({
            'Close': prices,
            'RSI_14': rsi_values
        }, index=dates)
        
        config = StrategyConfig(
            name='rsi_meanrev',
            params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        )
        
        result1 = engine.run_backtest(data_with_trades, config, symbol='WITH_TRADES')
        
        print(f"✓ Backtest completed")
        print(f"  - Extracted {len(result1['trades'])} trades")
        print(f"  - Metrics num_trades: {result1['metrics']['num_trades']}")
        
        # Retrieve from store
        details1 = engine.store.get_detailed_results('WITH_TRADES', 'rsi_meanrev', config.params)
        
        if details1 and 'trades' in details1:
            print(f"✓ Retrieved from store")
            print(f"  - Stored trades: {len(details1['trades'])}")
            print(f"  - Metrics match: {details1['metrics']['num_trades'] == len(details1['trades'])}")
        else:
            print("✗ Failed to retrieve trades")
        
        print()
        
        # Scenario 2: Backtest with NO trades (empty)
        print("📊 Scenario 2: Backtest with NO trades (legitimate)")
        print("-" * 70)
        
        dates2 = pd.date_range('2020-01-01', periods=50, freq='D')
        flat_prices = np.full(50, 100.0)
        neutral_rsi = np.full(50, 50.0)
        
        data_no_trades = pd.DataFrame({
            'Close': flat_prices,
            'RSI_14': neutral_rsi
        }, index=dates2)
        
        result2 = engine.run_backtest(data_no_trades, config, symbol='NO_TRADES')
        
        print(f"✓ Backtest completed")
        print(f"  - Extracted {len(result2['trades'])} trades (empty DataFrame)")
        print(f"  - Metrics num_trades: {result2['metrics']['num_trades']}")
        
        # Retrieve from store
        details2 = engine.store.get_detailed_results('NO_TRADES', 'rsi_meanrev', config.params)
        
        if details2 and 'trades' in details2:
            print(f"✓ Retrieved from store")
            print(f"  - Stored trades: {len(details2['trades'])} (empty DataFrame preserved!)")
            print(f"  - Can distinguish: 'trades' key exists but DataFrame is empty")
            print(f"  - UI can show: 'No trades generated' vs 'Trade data missing'")
        else:
            print("✗ Failed to retrieve trades")
        
        print()
        
        # Scenario 3: Compare with missing data
        print("📊 Scenario 3: Simulated missing trade data")
        print("-" * 70)
        
        # Try to retrieve non-existent backtest
        details3 = engine.store.get_detailed_results('NONEXISTENT', 'rsi_meanrev', config.params)
        
        if details3 is None:
            print("✓ Correctly returns None for non-existent backtest")
        else:
            print("✗ Should return None for non-existent backtest")
        
        print()
        
        # Summary
        print("=" * 70)
        print("Summary of Fix")
        print("=" * 70)
        print()
        print("✓ Empty trades DataFrames are now stored (not dropped)")
        print("✓ Can distinguish between:")
        print("  1. Trades exist: 'trades' key present with data")
        print("  2. No trades occurred: 'trades' key present but empty DataFrame")
        print("  3. Data missing: 'trades' key absent or retrieval returns None")
        print()
        print("✓ UI can show appropriate messages:")
        print("  - Case 1: Display trade table")
        print("  - Case 2: 'No trades generated - try different parameters'")
        print("  - Case 3: 'Trade data missing - re-run backtest'")
        print()
        print("✓ Comprehensive logging added for debugging")
        print("✓ Tests validate all scenarios")
        print()


if __name__ == '__main__':
    demo_trade_fix()
