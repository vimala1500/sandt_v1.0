#!/usr/bin/env python3
"""
Tests for BacktestStore module.
Tests storage, retrieval, and querying of backtest results.
"""

import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path

from backtest_store import BacktestStore


def test_basic_storage_and_retrieval():
    """Test basic storage and retrieval of backtest results."""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_store.zarr"
        store = BacktestStore(str(store_path))
        
        # Test data
        symbol = "AAPL"
        strategy = "rsi_meanrev"
        params = {"rsi_period": 14, "oversold": 30, "overbought": 70}
        exit_rule = "default"
        
        metrics = {
            'win_rate': 0.65,
            'num_trades': 25,
            'total_return': 0.35,
            'cagr': 0.12,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.15,
            'expectancy': 0.014
        }
        
        equity_curve = np.linspace(100000, 135000, 100)
        positions = np.random.choice([0, 1, -1], size=100)
        dates = pd.date_range('2020-01-01', periods=100)
        
        # Store backtest
        backtest_id = store.store_backtest(
            symbol, strategy, params, exit_rule,
            metrics, equity_curve, positions, dates.values
        )
        
        print(f"✓ Stored backtest with ID: {backtest_id}")
        
        # Retrieve stats
        stats_df = store.get_stats(symbol, strategy, params, exit_rule)
        assert len(stats_df) == 1, "Should retrieve exactly one backtest"
        
        row = stats_df.iloc[0]
        assert row['symbol'] == symbol
        assert row['strategy'] == strategy
        assert abs(row['win_rate'] - 0.65) < 0.01
        assert row['num_trades'] == 25
        
        print(f"✓ Retrieved stats correctly")
        
        # Retrieve detailed results
        details = store.get_detailed_results(symbol, strategy, params, exit_rule)
        assert details is not None
        assert 'equity_curve' in details
        assert len(details['equity_curve']) == 100
        
        print(f"✓ Retrieved detailed results correctly")
        
        print("✓ test_basic_storage_and_retrieval PASSED")


def test_multiple_strategies_and_params():
    """Test storing and querying multiple strategies and parameter sets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_store.zarr"
        store = BacktestStore(str(store_path))
        
        symbols = ["AAPL", "GOOGL", "MSFT"]
        strategies = ["rsi_meanrev", "ma_crossover"]
        
        # Store multiple backtests
        count = 0
        for symbol in symbols:
            for strategy in strategies:
                if strategy == "rsi_meanrev":
                    params_list = [
                        {"rsi_period": 14, "oversold": 30, "overbought": 70},
                        {"rsi_period": 14, "oversold": 20, "overbought": 80}
                    ]
                else:
                    params_list = [
                        {"fast_period": 20, "slow_period": 50},
                        {"fast_period": 50, "slow_period": 200}
                    ]
                
                for params in params_list:
                    metrics = {
                        'win_rate': np.random.uniform(0.4, 0.7),
                        'num_trades': np.random.randint(10, 50),
                        'total_return': np.random.uniform(0.1, 0.5),
                        'cagr': np.random.uniform(0.05, 0.15),
                        'sharpe_ratio': np.random.uniform(0.5, 2.0),
                        'max_drawdown': np.random.uniform(-0.3, -0.1),
                        'expectancy': np.random.uniform(0.005, 0.02)
                    }
                    
                    store.store_backtest(
                        symbol, strategy, params, 'default',
                        metrics
                    )
                    count += 1
        
        print(f"✓ Stored {count} backtests")
        
        # Test filtering by symbol
        aapl_stats = store.get_stats(symbol="AAPL")
        assert len(aapl_stats) == 4  # 2 strategies x 2 param sets
        assert all(aapl_stats['symbol'] == "AAPL")
        print(f"✓ Filtered by symbol correctly: {len(aapl_stats)} results for AAPL")
        
        # Test filtering by strategy
        rsi_stats = store.get_stats(strategy="rsi_meanrev")
        assert len(rsi_stats) == 6  # 3 symbols x 2 param sets
        assert all(rsi_stats['strategy'] == "rsi_meanrev")
        print(f"✓ Filtered by strategy correctly: {len(rsi_stats)} results for rsi_meanrev")
        
        # Test getting all stats
        all_stats = store.get_all_stats()
        assert len(all_stats) == count
        print(f"✓ Retrieved all {len(all_stats)} stats")
        
        # Test summary stats
        summary = store.get_summary_stats()
        assert summary['total_backtests'] == count
        assert summary['unique_symbols'] == 3
        assert summary['unique_strategies'] == 2
        print(f"✓ Summary stats: {summary}")
        
        print("✓ test_multiple_strategies_and_params PASSED")


def test_bulk_retrieval():
    """Test bulk retrieval of backtest stats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_store.zarr"
        store = BacktestStore(str(store_path))
        
        # Store some backtests
        test_cases = [
            ("AAPL", "rsi_meanrev", {"rsi_period": 14, "oversold": 30, "overbought": 70}),
            ("GOOGL", "rsi_meanrev", {"rsi_period": 14, "oversold": 30, "overbought": 70}),
            ("MSFT", "ma_crossover", {"fast_period": 20, "slow_period": 50})
        ]
        
        for symbol, strategy, params in test_cases:
            metrics = {
                'win_rate': 0.6,
                'num_trades': 20,
                'total_return': 0.3,
                'cagr': 0.1,
                'sharpe_ratio': 1.2,
                'max_drawdown': -0.2,
                'expectancy': 0.015
            }
            store.store_backtest(symbol, strategy, params, 'default', metrics)
        
        # Bulk retrieve
        lookups = [
            (symbol, strategy, params, 'default')
            for symbol, strategy, params in test_cases
        ]
        
        bulk_stats = store.bulk_get_stats(lookups)
        assert len(bulk_stats) == 3
        print(f"✓ Bulk retrieval of {len(bulk_stats)} backtests")
        
        print("✓ test_bulk_retrieval PASSED")


def test_delete_backtest():
    """Test deleting a backtest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_store.zarr"
        store = BacktestStore(str(store_path))
        
        # Store a backtest
        symbol = "AAPL"
        strategy = "rsi_meanrev"
        params = {"rsi_period": 14, "oversold": 30, "overbought": 70}
        
        metrics = {
            'win_rate': 0.6,
            'num_trades': 20,
            'total_return': 0.3,
            'cagr': 0.1,
            'sharpe_ratio': 1.2,
            'max_drawdown': -0.2,
            'expectancy': 0.015
        }
        
        store.store_backtest(symbol, strategy, params, 'default', metrics)
        
        # Verify it exists
        stats = store.get_stats(symbol, strategy, params)
        assert len(stats) == 1
        
        # Delete it
        deleted = store.delete_backtest(symbol, strategy, params)
        assert deleted
        
        # Verify it's gone
        stats = store.get_stats(symbol, strategy, params)
        assert len(stats) == 0
        
        # Try deleting again - should return False
        deleted = store.delete_backtest(symbol, strategy, params)
        assert not deleted
        
        print("✓ test_delete_backtest PASSED")


def test_params_hashing():
    """Test that parameter hashing is stable and different params get different hashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_store.zarr"
        store = BacktestStore(str(store_path))
        
        # Same params in different order should hash to same value
        params1 = {"rsi_period": 14, "oversold": 30, "overbought": 70}
        params2 = {"oversold": 30, "rsi_period": 14, "overbought": 70}
        
        hash1 = store._hash_params(params1)
        hash2 = store._hash_params(params2)
        
        assert hash1 == hash2, "Same params in different order should hash identically"
        print(f"✓ Param hashing is stable: {hash1} == {hash2}")
        
        # Different params should hash differently
        params3 = {"rsi_period": 14, "oversold": 20, "overbought": 80}
        hash3 = store._hash_params(params3)
        
        assert hash1 != hash3, "Different params should hash differently"
        print(f"✓ Different params hash differently: {hash1} != {hash3}")
        
        print("✓ test_params_hashing PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("Running BacktestStore Tests")
    print("=" * 70)
    
    test_basic_storage_and_retrieval()
    print()
    
    test_multiple_strategies_and_params()
    print()
    
    test_bulk_retrieval()
    print()
    
    test_delete_backtest()
    print()
    
    test_params_hashing()
    print()
    
    print("=" * 70)
    print("✓ All tests PASSED!")
    print("=" * 70)


if __name__ == '__main__':
    run_all_tests()
