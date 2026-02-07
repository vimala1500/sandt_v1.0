"""
Tests for Trade Details Modal Error Handling
============================================
Tests for the trade details modal callback and error handling improvements.
"""

import unittest
import os
import tempfile
import shutil
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backtest_store import BacktestStore
from backtest_engine import BacktestEngine
from indicator_engine import IndicatorEngine
from backtest_manager_ui import BacktestManagerUI


class TestTradeDetailsModalErrorHandling(unittest.TestCase):
    """Test error handling in trade details modal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.indicator_engine = IndicatorEngine(os.path.join(self.test_dir, "indicators"))
        self.backtest_engine = BacktestEngine(os.path.join(self.test_dir, "backtests"))
        self.manager_ui = BacktestManagerUI(self.indicator_engine, self.backtest_engine)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_create_trade_details_view_with_valid_data(self):
        """Test _create_trade_details_view with valid data."""
        detailed_results = {
            'metrics': {
                'win_rate': 0.6,
                'num_trades': 10,
                'total_return': 0.15,
                'cagr': 0.20,
                'sharpe_ratio': 1.5,
                'max_drawdown': -0.10,
                'expectancy': 0.02
            },
            'trades': pd.DataFrame({
                'Trade No.': [1, 2, 3],
                'Entry Date': ['2020-01-01', '2020-02-01', '2020-03-01'],
                'Entry Price': [100, 105, 110],
                'Exit Date': ['2020-01-15', '2020-02-15', '2020-03-15'],
                'Exit Price': [105, 103, 115],
                'Position': ['Long', 'Long', 'Long'],
                'Size': [100, 100, 100],
                'Holding Period': [14, 14, 14],
                'P&L %': [0.05, -0.02, 0.045],
                'P&L $': [500, -200, 450],
                'MAE': [-0.01, -0.03, -0.01],
                'MFE': [0.06, 0.01, 0.05],
                'Exit Reason': ['Target', 'Stop', 'Target'],
                'Comments': ['Good', 'Loss', 'Good']
            }),
            'equity_curve': [10000, 10500, 10300, 10750],
            'dates': ['2020-01-01', '2020-01-15', '2020-02-15', '2020-03-15']
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Verify result is not None and is a Div component
        self.assertIsNotNone(result)
        self.assertEqual(result.__class__.__name__, 'Div')
    
    def test_create_trade_details_view_with_empty_trades(self):
        """Test _create_trade_details_view with empty trades DataFrame."""
        detailed_results = {
            'metrics': {
                'win_rate': 0.0,
                'num_trades': 0,
                'total_return': 0.0,
                'cagr': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'expectancy': 0.0
            },
            'trades': pd.DataFrame(),  # Empty DataFrame
            'equity_curve': [10000],
            'dates': ['2020-01-01']
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Should still return a valid component, not raise an error
        self.assertIsNotNone(result)
        self.assertEqual(result.__class__.__name__, 'Div')
    
    def test_create_trade_details_view_with_none_trades(self):
        """Test _create_trade_details_view with None trades."""
        detailed_results = {
            'metrics': {
                'win_rate': 0.0,
                'num_trades': 0,
                'total_return': 0.0,
                'cagr': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'expectancy': 0.0
            },
            'trades': None,
            'equity_curve': None,
            'dates': []
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Should still return a valid component
        self.assertIsNotNone(result)
        self.assertEqual(result.__class__.__name__, 'Div')
    
    def test_create_trade_details_view_with_missing_columns(self):
        """Test _create_trade_details_view with missing required columns."""
        detailed_results = {
            'metrics': {
                'win_rate': 0.6,
                'num_trades': 2,
                'total_return': 0.10,
                'cagr': 0.15,
                'sharpe_ratio': 1.2,
                'max_drawdown': -0.05,
                'expectancy': 0.01
            },
            'trades': pd.DataFrame({
                'Trade No.': [1, 2],
                'Entry Date': ['2020-01-01', '2020-02-01'],
                'Exit Date': ['2020-01-15', '2020-02-15'],
                # Missing other columns
            })
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Should handle missing columns gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result.__class__.__name__, 'Div')
    
    def test_create_trade_details_view_with_invalid_metrics(self):
        """Test _create_trade_details_view with invalid metrics."""
        detailed_results = {
            'metrics': None,  # Invalid metrics
            'trades': None,
            'equity_curve': None,
            'dates': []
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Should handle invalid metrics gracefully
        self.assertIsNotNone(result)
    
    def test_create_trade_details_view_with_invalid_input(self):
        """Test _create_trade_details_view with completely invalid input."""
        result = self.manager_ui._create_trade_details_view(None)
        
        # Should return error alert, not raise exception
        self.assertIsNotNone(result)
        # Check if it's an Alert component
        self.assertEqual(result.__class__.__name__, 'Alert')
    
    def test_create_trade_details_view_with_corrupt_dataframe(self):
        """Test _create_trade_details_view with corrupt DataFrame data."""
        detailed_results = {
            'metrics': {
                'win_rate': 0.5,
                'num_trades': 2,
                'total_return': 0.10,
                'cagr': 0.15,
                'sharpe_ratio': 1.0,
                'max_drawdown': -0.05,
                'expectancy': 0.01
            },
            'trades': pd.DataFrame({
                'P&L %': [np.nan, np.inf],  # Invalid numeric values
                'Holding Period': [np.nan, -1]
            })
        }
        
        result = self.manager_ui._create_trade_details_view(detailed_results)
        
        # Should handle corrupt data without crashing
        self.assertIsNotNone(result)


class TestBacktestStoreErrorHandling(unittest.TestCase):
    """Test error handling in BacktestStore.get_detailed_results."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.store_path = os.path.join(self.test_dir, "test_store.zarr")
        self.store = BacktestStore(self.store_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_detailed_results_with_invalid_symbol(self):
        """Test get_detailed_results with empty/invalid symbol."""
        result = self.store.get_detailed_results(
            symbol="",  # Empty symbol
            strategy="test_strategy",
            params={"param1": 10},
            exit_rule="default"
        )
        
        self.assertIsNone(result)
    
    def test_get_detailed_results_with_invalid_strategy(self):
        """Test get_detailed_results with empty/invalid strategy."""
        result = self.store.get_detailed_results(
            symbol="AAPL",
            strategy="",  # Empty strategy
            params={"param1": 10},
            exit_rule="default"
        )
        
        self.assertIsNone(result)
    
    def test_get_detailed_results_with_invalid_params(self):
        """Test get_detailed_results with invalid params type."""
        result = self.store.get_detailed_results(
            symbol="AAPL",
            strategy="test_strategy",
            params=None,  # Invalid params
            exit_rule="default"
        )
        
        # Should handle None params gracefully (convert to empty dict)
        self.assertIsNone(result)  # Will be None because no data exists, but shouldn't crash
    
    def test_get_detailed_results_nonexistent_data(self):
        """Test get_detailed_results with nonexistent backtest."""
        result = self.store.get_detailed_results(
            symbol="NONEXISTENT",
            strategy="nonexistent_strategy",
            params={"param1": 999},
            exit_rule="nonexistent"
        )
        
        self.assertIsNone(result)
    
    def test_get_detailed_results_with_valid_data(self):
        """Test get_detailed_results with stored backtest data."""
        # First, store some test data
        from datetime import datetime
        
        self.store.store_backtest(
            symbol='TEST',
            strategy='test_strategy',
            params={'param1': 10},
            exit_rule='default',
            metrics={
                'win_rate': 0.6,
                'num_trades': 10,
                'total_return': 0.15,
                'cagr': 0.20,
                'sharpe_ratio': 1.5,
                'max_drawdown': -0.10,
                'expectancy': 0.02
            },
            equity_curve=np.array([10000, 10500, 11000]),
            dates=np.array(['2020-01-01', '2020-02-01', '2020-03-01']),
            positions=np.array([0, 1, 0])
        )
        
        # Now retrieve it
        result = self.store.get_detailed_results(
            symbol='TEST',
            strategy='test_strategy',
            params={'param1': 10},
            exit_rule='default'
        )
        
        # Should return result with metrics
        self.assertIsNotNone(result)
        self.assertIn('metrics', result)
        self.assertAlmostEqual(result['metrics']['win_rate'], 0.6, places=2)
        self.assertEqual(result['metrics']['num_trades'], 10)


class TestModalCallbackIntegration(unittest.TestCase):
    """Integration tests for the modal callback."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.indicator_engine = IndicatorEngine(os.path.join(self.test_dir, "indicators"))
        self.backtest_engine = BacktestEngine(os.path.join(self.test_dir, "backtests"))
        
        # Store some test data
        self.backtest_engine.store.store_backtest(
            symbol='AAPL',
            strategy='rsi_meanrev',
            params={'rsi_period': 14},
            exit_rule='default',
            metrics={
                'win_rate': 0.6,
                'num_trades': 10,
                'total_return': 0.15,
                'cagr': 0.20,
                'sharpe_ratio': 1.5,
                'max_drawdown': -0.10,
                'expectancy': 0.02
            },
            equity_curve=np.array([10000, 10500, 11000]),
            dates=np.array(['2020-01-01', '2020-02-01', '2020-03-01']),
            positions=np.array([0, 1, 0])
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_modal_opens_with_valid_data(self):
        """Test that modal opens successfully with valid backtest data."""
        manager_ui = BacktestManagerUI(self.indicator_engine, self.backtest_engine)
        
        # Simulate the data structure passed to the callback
        clicked_row_data = {
            'symbol': 'AAPL',
            'strategy': 'rsi_meanrev',
            'params': {'rsi_period': 14},
            'exit_rule': 'default'
        }
        
        # Get detailed results
        detailed_results = self.backtest_engine.store.get_detailed_results(
            symbol=clicked_row_data['symbol'],
            strategy=clicked_row_data['strategy'],
            params=clicked_row_data['params'],
            exit_rule=clicked_row_data['exit_rule']
        )
        
        self.assertIsNotNone(detailed_results)
        
        # Create modal view
        modal_body = manager_ui._create_trade_details_view(detailed_results)
        
        self.assertIsNotNone(modal_body)
        self.assertEqual(modal_body.__class__.__name__, 'Div')


if __name__ == '__main__':
    unittest.main()
