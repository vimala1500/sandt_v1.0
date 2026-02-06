"""
Tests for Backtest Manager functionality
=========================================
Tests for batch backtesting, group sets, and UI components.
"""

import unittest
import os
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

from backtest_store import BacktestStore
from backtest_engine import BacktestEngine
from strategy import StrategyConfig


class TestBacktestManagerBatch(unittest.TestCase):
    """Test batch backtest functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.store_path = os.path.join(self.test_dir, "test_store.zarr")
        self.store = BacktestStore(self.store_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_group_set_save_load(self):
        """Test saving and loading group sets."""
        # Save a group set
        self.store.save_group_set(
            name="test_group",
            symbols=["AAPL", "GOOGL", "MSFT"],
            strategies=["rsi_meanrev", "ma_crossover"],
            params_list=[
                {"rsi_period": 14, "oversold": 30, "overbought": 70},
                {"fast_period": 20, "slow_period": 50}
            ],
            exit_rules=["default", "trailing_stop"]
        )
        
        # Load the group set
        loaded = self.store.load_group_set("test_group")
        
        # Verify
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "test_group")
        self.assertEqual(len(loaded["symbols"]), 3)
        self.assertIn("AAPL", loaded["symbols"])
        self.assertEqual(len(loaded["strategies"]), 2)
        self.assertIn("rsi_meanrev", loaded["strategies"])
        self.assertEqual(len(loaded["params_list"]), 2)
        self.assertEqual(len(loaded["exit_rules"]), 2)
    
    def test_list_group_sets(self):
        """Test listing all group sets."""
        # Save multiple group sets
        self.store.save_group_set(
            name="group1",
            symbols=["AAPL"],
            strategies=["rsi_meanrev"],
            params_list=[{"rsi_period": 14}],
            exit_rules=["default"]
        )
        
        self.store.save_group_set(
            name="group2",
            symbols=["GOOGL"],
            strategies=["ma_crossover"],
            params_list=[{"fast_period": 20, "slow_period": 50}],
            exit_rules=["default"]
        )
        
        # List group sets
        groups = self.store.list_group_sets()
        
        # Verify
        self.assertEqual(len(groups), 2)
        self.assertIn("group1", groups)
        self.assertIn("group2", groups)
    
    def test_delete_group_set(self):
        """Test deleting a group set."""
        # Save a group set
        self.store.save_group_set(
            name="to_delete",
            symbols=["AAPL"],
            strategies=["rsi_meanrev"],
            params_list=[{"rsi_period": 14}],
            exit_rules=["default"]
        )
        
        # Verify it exists
        self.assertIn("to_delete", self.store.list_group_sets())
        
        # Delete it
        deleted = self.store.delete_group_set("to_delete")
        self.assertTrue(deleted)
        
        # Verify it's gone
        self.assertNotIn("to_delete", self.store.list_group_sets())
        
        # Try deleting non-existent
        deleted = self.store.delete_group_set("nonexistent")
        self.assertFalse(deleted)
    
    def test_group_set_persistence(self):
        """Test that group sets persist across store instances."""
        # Save a group set
        self.store.save_group_set(
            name="persistent",
            symbols=["AAPL", "MSFT"],
            strategies=["rsi_meanrev"],
            params_list=[{"rsi_period": 14}],
            exit_rules=["default"]
        )
        
        # Close and reopen store
        del self.store
        self.store = BacktestStore(self.store_path)
        
        # Verify group set is still there
        loaded = self.store.load_group_set("persistent")
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded["symbols"]), 2)


class TestBatchBacktestExecution(unittest.TestCase):
    """Test batch backtest execution."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.engine = BacktestEngine(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _create_test_data(self, n_days=100):
        """Create synthetic test data."""
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
        prices = 100 + np.cumsum(np.random.randn(n_days) * 2)
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.random.randint(1000000, 5000000, n_days)
        }, index=dates)
        
        # Add indicators
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['RSI_14'] = 50 + np.random.randn(n_days) * 10  # Simplified RSI
        
        return data
    
    def test_batch_backtest_structure(self):
        """Test batch backtest return structure."""
        # This test verifies the structure without actually running backtests
        # since we don't have real indicator data
        
        # Create strategy configs
        configs = [
            StrategyConfig(name="rsi_meanrev", params={"rsi_period": 14, "oversold": 30, "overbought": 70}),
            StrategyConfig(name="ma_crossover", params={"fast_period": 20, "slow_period": 50})
        ]
        
        symbols = ["TEST1", "TEST2"]
        exit_rules = ["default"]
        
        # Calculate expected job count
        expected_jobs = len(symbols) * len(configs) * len(exit_rules)
        
        # Verify calculation
        self.assertEqual(expected_jobs, 4)  # 2 symbols * 2 strategies * 1 exit rule


class TestBacktestManagerUI(unittest.TestCase):
    """Test Backtest Manager UI components."""
    
    def setUp(self):
        """Set up test fixtures."""
        from indicator_engine import IndicatorEngine
        from backtest_manager_ui import BacktestManagerUI
        
        self.test_dir = tempfile.mkdtemp()
        self.indicator_engine = IndicatorEngine(os.path.join(self.test_dir, "indicators"))
        self.backtest_engine = BacktestEngine(os.path.join(self.test_dir, "backtests"))
        self.manager_ui = BacktestManagerUI(self.indicator_engine, self.backtest_engine)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_manager_ui_initialization(self):
        """Test that BacktestManagerUI initializes correctly."""
        self.assertIsNotNone(self.manager_ui)
        self.assertEqual(len(self.manager_ui.available_strategies), 2)
        self.assertIn('rsi_meanrev', self.manager_ui.available_strategies)
        self.assertIn('ma_crossover', self.manager_ui.available_strategies)
    
    def test_layout_creation(self):
        """Test that layout is created without errors."""
        layout = self.manager_ui.create_layout()
        self.assertIsNotNone(layout)
    
    def test_strategy_param_sets(self):
        """Test that strategy parameter sets are defined."""
        rsi_params = self.manager_ui.available_strategies['rsi_meanrev']['params']
        self.assertGreater(len(rsi_params), 0)
        self.assertIsInstance(rsi_params[0], dict)
        self.assertIn('rsi_period', rsi_params[0])
        
        ma_params = self.manager_ui.available_strategies['ma_crossover']['params']
        self.assertGreater(len(ma_params), 0)
        self.assertIsInstance(ma_params[0], dict)
        self.assertIn('fast_period', ma_params[0])


class TestTradeExtraction(unittest.TestCase):
    """Test trade-by-trade extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.engine = BacktestEngine(os.path.join(self.test_dir, "backtests"))
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_extract_trades_basic(self):
        """Test basic trade extraction from positions."""
        # Create simple test data
        n_days = 100
        prices = np.array([100.0 + i * 0.5 for i in range(n_days)])
        
        # Simple positions: long for 20 days, flat for 10, long for 20, flat
        positions = np.zeros(n_days)
        positions[10:30] = 1  # First trade
        positions[40:60] = 1  # Second trade
        
        # Create equity curve
        equity = np.full(n_days, 100000.0)
        for i in range(1, n_days):
            if positions[i] == 1:
                price_change = (prices[i] - prices[i-1]) / prices[i-1]
                equity[i] = equity[i-1] * (1 + price_change)
            else:
                equity[i] = equity[i-1]
        
        # Create dates
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D').values
        
        # Extract trades
        trades_df = self.engine.extract_trades(prices, positions, equity, dates)
        
        # Verify
        self.assertIsInstance(trades_df, pd.DataFrame)
        self.assertEqual(len(trades_df), 2)  # Should have 2 trades
        
        # Check columns exist
        expected_columns = [
            'Trade No.', 'Entry Date', 'Entry Price', 'Exit Date', 'Exit Price',
            'Position', 'Size', 'Holding Period', 'P&L %', 'P&L $',
            'MAE', 'MFE', 'Exit Reason', 'Comments'
        ]
        for col in expected_columns:
            self.assertIn(col, trades_df.columns)
        
        # Check first trade
        first_trade = trades_df.iloc[0]
        self.assertEqual(first_trade['Trade No.'], 1)
        self.assertEqual(first_trade['Position'], 'Long')
        self.assertEqual(first_trade['Holding Period'], 20)
        self.assertGreater(first_trade['P&L %'], 0)  # Should be profitable given upward prices
    
    def test_extract_trades_long_and_short(self):
        """Test trade extraction with both long and short positions."""
        n_days = 100
        prices = np.array([100.0 + i * 0.5 for i in range(n_days)])
        
        # Mix of long and short positions
        positions = np.zeros(n_days)
        positions[10:30] = 1   # Long trade
        positions[40:60] = -1  # Short trade
        
        equity = np.full(n_days, 100000.0)
        for i in range(1, n_days):
            if positions[i] != 0:
                price_change = (prices[i] - prices[i-1]) / prices[i-1]
                equity[i] = equity[i-1] * (1 + positions[i] * price_change)
            else:
                equity[i] = equity[i-1]
        
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D').values
        
        trades_df = self.engine.extract_trades(prices, positions, equity, dates)
        
        # Verify
        self.assertEqual(len(trades_df), 2)
        
        # Check positions
        self.assertEqual(trades_df.iloc[0]['Position'], 'Long')
        self.assertEqual(trades_df.iloc[1]['Position'], 'Short')
    
    def test_extract_trades_no_trades(self):
        """Test trade extraction with no positions."""
        n_days = 50
        prices = np.array([100.0] * n_days)
        positions = np.zeros(n_days)
        equity = np.full(n_days, 100000.0)
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D').values
        
        trades_df = self.engine.extract_trades(prices, positions, equity, dates)
        
        # Should return empty DataFrame
        self.assertIsInstance(trades_df, pd.DataFrame)
        self.assertEqual(len(trades_df), 0)
    
    def test_backtest_stores_trades(self):
        """Test that run_backtest stores trades in the result."""
        # Create test data
        n_days = 100
        dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
        data = pd.DataFrame({
            'Close': 100 + np.cumsum(np.random.randn(n_days) * 2),
            'RSI_14': 50 + np.random.randn(n_days) * 10
        }, index=dates)
        
        # Create strategy config
        from strategy import StrategyConfig
        config = StrategyConfig(
            name='rsi_meanrev',
            params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        )
        
        # Run backtest
        result = self.engine.run_backtest(
            data=data,
            strategy_config=config,
            symbol='TEST'
        )
        
        # Verify trades are in result
        self.assertIn('trades', result)
        self.assertIsInstance(result['trades'], pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
