#!/usr/bin/env python3
"""
Generate sample backtest data for UI testing.
Creates backtests with trades and without trades to demonstrate the fix.
"""

import numpy as np
import pandas as pd
from pathlib import Path

from backtest_engine import BacktestEngine
from strategy import StrategyConfig


def generate_sample_data():
    """Generate sample backtests with various scenarios."""
    print("=" * 70)
    print("Generating Sample Backtest Data for UI Testing")
    print("=" * 70)
    print()
    
    # Initialize engine with default path
    engine = BacktestEngine(output_path="./data/backtests")
    
    # Scenario 1: Generate data with trades
    print("📊 Generating backtest WITH trades...")
    dates = pd.date_range('2020-01-01', periods=252, freq='D')
    
    # Create oscillating price and RSI that will trigger trades
    prices = 100 + np.cumsum(np.random.randn(252) * 0.5)
    rsi_values = 50 + 25 * np.sin(np.linspace(0, 8 * np.pi, 252))
    
    data_with_trades = pd.DataFrame({
        'Close': prices,
        'RSI_14': rsi_values
    }, index=dates)
    
    config1 = StrategyConfig(
        name='rsi_meanrev',
        params={'rsi_period': 14, 'oversold': 30, 'overbought': 70},
        description='RSI Mean Reversion (Aggressive)'
    )
    
    result1 = engine.run_backtest(
        data_with_trades, config1,
        symbol='SAMPLE_WITH_TRADES',
        exit_rule='default'
    )
    
    print(f"  ✓ Generated {len(result1['trades'])} trades")
    print(f"  ✓ Total Return: {result1['metrics']['total_return']*100:.2f}%")
    print(f"  ✓ Win Rate: {result1['metrics']['win_rate']*100:.2f}%")
    print()
    
    # Scenario 2: Generate data with NO trades (conservative parameters)
    print("📊 Generating backtest WITHOUT trades (conservative)...")
    
    data_no_trades = pd.DataFrame({
        'Close': np.full(252, 100.0),  # Flat prices
        'RSI_14': np.full(252, 50.0)    # Neutral RSI
    }, index=dates)
    
    config2 = StrategyConfig(
        name='rsi_meanrev',
        params={'rsi_period': 14, 'oversold': 10, 'overbought': 90},  # Very conservative
        description='RSI Mean Reversion (Conservative)'
    )
    
    result2 = engine.run_backtest(
        data_no_trades, config2,
        symbol='SAMPLE_NO_TRADES',
        exit_rule='default'
    )
    
    print(f"  ✓ Generated {len(result2['trades'])} trades (as expected)")
    print(f"  ✓ Total Return: {result2['metrics']['total_return']*100:.2f}%")
    print()
    
    # Scenario 3: Another backtest with moderate trades
    print("📊 Generating backtest with moderate trades...")
    
    prices2 = 100 + 10 * np.sin(np.linspace(0, 4 * np.pi, 252))
    rsi_values2 = 50 + 30 * np.sin(np.linspace(0, 6 * np.pi, 252))
    
    data_moderate = pd.DataFrame({
        'Close': prices2,
        'RSI_14': rsi_values2
    }, index=dates)
    
    config3 = StrategyConfig(
        name='rsi_meanrev',
        params={'rsi_period': 14, 'oversold': 35, 'overbought': 65},
        description='RSI Mean Reversion (Moderate)'
    )
    
    result3 = engine.run_backtest(
        data_moderate, config3,
        symbol='SAMPLE_MODERATE',
        exit_rule='default'
    )
    
    print(f"  ✓ Generated {len(result3['trades'])} trades")
    print(f"  ✓ Total Return: {result3['metrics']['total_return']*100:.2f}%")
    print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("Sample backtests generated in: ./data/backtests/store.zarr")
    print()
    print("Test scenarios created:")
    print("  1. SAMPLE_WITH_TRADES - Has trades (should show trade table)")
    print("  2. SAMPLE_NO_TRADES - No trades (should show 'No trades generated' message)")
    print("  3. SAMPLE_MODERATE - Moderate trades (should show trade table)")
    print()
    print("To test the UI:")
    print("  1. Run the Backtest Manager")
    print("  2. Look for these sample backtests in the results table")
    print("  3. Click 'View Details' for each")
    print("  4. Verify appropriate messages for each scenario")
    print()
    
    # Show store statistics
    stats = engine.store.get_summary_stats()
    print(f"Store Statistics:")
    print(f"  - Total backtests: {stats['total_backtests']}")
    print(f"  - Unique symbols: {stats['unique_symbols']}")
    print(f"  - Storage size: {stats['storage_size_mb']:.2f} MB")
    print()


if __name__ == '__main__':
    generate_sample_data()
