#!/usr/bin/env python3
"""
Integration tests for trade data pipeline.
Tests the complete flow from backtest execution to trade display.
"""

import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path

from backtest_engine import BacktestEngine
from backtest_store import BacktestStore
from strategy import StrategyConfig


def test_trades_storage_with_trades():
    """Test that trades are stored and retrieved correctly when trades exist."""
    print("\n=== Test: Trades Storage With Trades ===")
    
    # Set random seed for reproducible tests
    np.random.seed(42)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create backtest engine
        engine = BacktestEngine(output_path=tmpdir)
        
        # Create sample data with conditions that will generate trades
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)  # Random walk
        
        # Create oscillating RSI values that will trigger trades
        rsi_values = 50 + 20 * np.sin(np.linspace(0, 4 * np.pi, 100))
        
        data = pd.DataFrame({
            'Close': prices,
            'RSI_14': rsi_values
        }, index=dates)
        
        # Run backtest with RSI mean reversion strategy
        config = StrategyConfig(
            name='rsi_meanrev',
            params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        )
        
        result = engine.run_backtest(
            data, config,
            symbol='TEST',
            exit_rule='default'
        )
        
        # Verify trades were extracted
        trades_df = result.get('trades')
        assert trades_df is not None, "Trades DataFrame should not be None"
        print(f"✓ Extracted {len(trades_df)} trades from backtest")
        
        # Retrieve from store
        detailed_results = engine.store.get_detailed_results(
            'TEST', 'rsi_meanrev', config.params
        )
        
        assert detailed_results is not None, "Detailed results should not be None"
        assert 'trades' in detailed_results, "Trades should be in detailed results"
        
        retrieved_trades = detailed_results['trades']
        assert retrieved_trades is not None, "Retrieved trades should not be None"
        assert isinstance(retrieved_trades, pd.DataFrame), "Retrieved trades should be DataFrame"
        assert len(retrieved_trades) == len(trades_df), f"Should retrieve same number of trades: {len(retrieved_trades)} vs {len(trades_df)}"
        
        print(f"✓ Retrieved {len(retrieved_trades)} trades from store")
        print("✓ test_trades_storage_with_trades PASSED")


def test_trades_storage_empty_trades():
    """Test that empty trades DataFrame is stored and retrieved correctly."""
    print("\n=== Test: Trades Storage Empty Trades ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create backtest engine
        engine = BacktestEngine(output_path=tmpdir)
        
        # Create sample data with conditions that WON'T generate trades
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        prices = np.full(50, 100.0)  # Flat prices
        rsi_values = np.full(50, 50.0)  # Neutral RSI
        
        data = pd.DataFrame({
            'Close': prices,
            'RSI_14': rsi_values
        }, index=dates)
        
        # Run backtest with RSI mean reversion strategy
        config = StrategyConfig(
            name='rsi_meanrev',
            params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        )
        
        result = engine.run_backtest(
            data, config,
            symbol='FLAT',
            exit_rule='default'
        )
        
        # Verify empty trades were extracted
        trades_df = result.get('trades')
        assert trades_df is not None, "Trades DataFrame should not be None"
        assert len(trades_df) == 0, "Trades DataFrame should be empty"
        print(f"✓ Extracted empty trades DataFrame (0 trades)")
        
        # Retrieve from store
        detailed_results = engine.store.get_detailed_results(
            'FLAT', 'rsi_meanrev', config.params
        )
        
        assert detailed_results is not None, "Detailed results should not be None"
        assert 'trades' in detailed_results, "Trades key should exist even for empty trades"
        
        retrieved_trades = detailed_results['trades']
        assert retrieved_trades is not None, "Retrieved trades should not be None (should be empty DataFrame)"
        assert isinstance(retrieved_trades, pd.DataFrame), "Retrieved trades should be DataFrame"
        assert len(retrieved_trades) == 0, "Retrieved trades should be empty"
        
        print(f"✓ Retrieved empty trades DataFrame from store")
        print("✓ test_trades_storage_empty_trades PASSED")


def test_trades_vs_metrics_consistency():
    """Test that trade count in metrics matches actual trades stored."""
    print("\n=== Test: Trades vs Metrics Consistency ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store = BacktestStore(str(Path(tmpdir) / "store.zarr"))
        
        # Store backtest with trades
        symbol = "AAPL"
        strategy = "rsi_meanrev"
        params = {"rsi_period": 14, "oversold": 30, "overbought": 70}
        
        # Create sample trades
        trades_data = []
        for i in range(5):
            trades_data.append({
                'Trade No.': i + 1,
                'Entry Date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=i*10),
                'Entry Price': 100 + i,
                'Exit Date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=i*10 + 5),
                'Exit Price': 101 + i,
                'Position': 'Long',
                'Size': 1000,
                'Holding Period': 5,
                'P&L %': 0.01,
                'P&L $': 1000,
                'MAE': -0.005,
                'MFE': 0.015,
                'Exit Reason': 'Signal Exit',
                'Comments': ''
            })
        
        trades_df = pd.DataFrame(trades_data)
        
        metrics = {
            'win_rate': 0.6,
            'num_trades': len(trades_df),  # Should match trades_df length
            'total_return': 0.3,
            'cagr': 0.1,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.2,
            'expectancy': 0.06
        }
        
        # Store
        backtest_id = store.store_backtest(
            symbol, strategy, params, 'default',
            metrics, trades=trades_df
        )
        
        print(f"✓ Stored backtest with {len(trades_df)} trades and num_trades={metrics['num_trades']}")
        
        # Retrieve and verify consistency
        detailed_results = store.get_detailed_results(symbol, strategy, params)
        
        assert detailed_results is not None
        assert detailed_results['metrics']['num_trades'] == len(trades_df)
        assert len(detailed_results['trades']) == metrics['num_trades']
        
        print(f"✓ Metrics num_trades ({detailed_results['metrics']['num_trades']}) matches stored trades ({len(detailed_results['trades'])})")
        print("✓ test_trades_vs_metrics_consistency PASSED")


def test_trades_serialization_roundtrip():
    """Test that trade data survives serialization/deserialization."""
    print("\n=== Test: Trades Serialization Roundtrip ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store = BacktestStore(str(Path(tmpdir) / "store.zarr"))
        
        # Create trades with various data types
        trades_data = [{
            'Trade No.': 1,
            'Entry Date': pd.Timestamp('2020-01-15'),
            'Entry Price': 123.45,
            'Exit Date': pd.Timestamp('2020-01-20'),
            'Exit Price': 125.67,
            'Position': 'Long',
            'Size': 1000,
            'Holding Period': 5,
            'P&L %': 0.018,
            'P&L $': 2220.0,
            'MAE': -0.005,
            'MFE': 0.025,
            'Exit Reason': 'Signal Exit',
            'Comments': 'Test trade'
        }]
        
        original_trades = pd.DataFrame(trades_data)
        
        metrics = {
            'win_rate': 1.0,
            'num_trades': 1,
            'total_return': 0.018,
            'cagr': 0.1,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.005,
            'expectancy': 0.018
        }
        
        # Store
        store.store_backtest(
            'SER_TEST', 'test_strategy', {'param1': 10}, 'default',
            metrics, trades=original_trades
        )
        
        # Retrieve
        results = store.get_detailed_results('SER_TEST', 'test_strategy', {'param1': 10})
        retrieved_trades = results['trades']
        
        # Verify all columns present
        for col in original_trades.columns:
            assert col in retrieved_trades.columns, f"Column {col} missing after roundtrip"
        
        # Verify data types and values (allowing for datetime conversion to string)
        assert retrieved_trades.iloc[0]['Trade No.'] == 1
        assert abs(retrieved_trades.iloc[0]['Entry Price'] - 123.45) < 0.01
        assert abs(retrieved_trades.iloc[0]['P&L %'] - 0.018) < 0.0001
        assert retrieved_trades.iloc[0]['Position'] == 'Long'
        
        print(f"✓ All columns preserved: {list(retrieved_trades.columns)}")
        print(f"✓ Data values intact after serialization")
        print("✓ test_trades_serialization_roundtrip PASSED")


def test_trades_with_no_initial_symbol():
    """Test backtest without symbol doesn't crash but doesn't store."""
    print("\n=== Test: Trades With No Symbol ===")
    
    # Set random seed for reproducible tests
    np.random.seed(43)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        engine = BacktestEngine(output_path=tmpdir)
        
        # Create sample data
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        data = pd.DataFrame({
            'Close': 100 + np.cumsum(np.random.randn(50) * 0.5),
            'RSI_14': 50 + 10 * np.random.randn(50)
        }, index=dates)
        
        config = StrategyConfig(
            name='rsi_meanrev',
            params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        )
        
        # Run without symbol (should not store)
        result = engine.run_backtest(data, config, symbol=None)
        
        assert 'trades' in result, "Result should contain trades key"
        assert result['trades'] is not None, "Trades should be extracted even without storage"
        
        print(f"✓ Backtest without symbol extracted {len(result['trades'])} trades")
        print("✓ test_trades_with_no_initial_symbol PASSED")


def run_all_tests():
    """Run all trade data pipeline tests."""
    print("=" * 70)
    print("Running Trade Data Pipeline Tests")
    print("=" * 70)
    
    test_trades_storage_with_trades()
    test_trades_storage_empty_trades()
    test_trades_vs_metrics_consistency()
    test_trades_serialization_roundtrip()
    test_trades_with_no_initial_symbol()
    
    print("\n" + "=" * 70)
    print("✓ All Trade Data Pipeline Tests PASSED!")
    print("=" * 70)


if __name__ == '__main__':
    run_all_tests()
