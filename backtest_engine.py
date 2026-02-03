"""
Backtest Engine Module
======================
Numba-accelerated vectorized backtesting engine.
Outputs metrics and results to Zarr for efficient storage.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import zarr
from numba import jit
from tqdm import tqdm

from strategy import StrategyRegistry, StrategyConfig


@jit(nopython=True)
def _vectorized_backtest(
    prices: np.ndarray,
    signals: np.ndarray,
    initial_capital: float = 100000.0
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Numba-accelerated backtest calculation.
    
    Args:
        prices: Array of close prices
        signals: Array of trading signals (1=long, -1=short, 0=neutral)
        initial_capital: Starting capital
        
    Returns:
        Tuple of (equity_curve, positions, num_trades)
    """
    n = len(prices)
    equity = np.zeros(n)
    positions = np.zeros(n)
    
    equity[0] = initial_capital
    current_position = 0
    num_trades = 0
    
    for i in range(1, n):
        # Check for signal change
        if signals[i] != current_position:
            if current_position != 0:
                num_trades += 1
            current_position = signals[i]
        
        positions[i] = current_position
        
        # Calculate returns
        if current_position != 0:
            price_change = (prices[i] - prices[i-1]) / prices[i-1]
            equity[i] = equity[i-1] * (1 + current_position * price_change)
        else:
            equity[i] = equity[i-1]
    
    return equity, positions, num_trades


class BacktestEngine:
    """
    Vectorized backtesting engine with Numba acceleration.
    
    Design:
    - Fast vectorized backtests using Numba
    - Computes standard metrics: win rate, CAGR, Sharpe, max drawdown, expectancy
    - Stores results to Zarr chunked arrays for efficiency
    - Stores metadata to JSON and Parquet
    """
    
    def __init__(self, output_path: str = "/content/drive/MyDrive/backtests"):
        """
        Initialize BacktestEngine.
        
        Args:
            output_path: Directory to store backtest results
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.zarr_path = self.output_path / "results.zarr"
        self.metadata_path = self.output_path / "metadata.json"
        self.strategy_registry = StrategyRegistry()
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_config: StrategyConfig,
        initial_capital: float = 100000.0
    ) -> Dict:
        """
        Run a single backtest.
        
        Args:
            data: DataFrame with price data and indicators
            strategy_config: Strategy configuration
            initial_capital: Starting capital
            
        Returns:
            Dictionary with backtest results and metrics
        """
        # Get strategy function
        strategy_func = self.strategy_registry.get_strategy(strategy_config.name)
        
        # Generate signals
        signals = strategy_func(data, **strategy_config.params)
        
        # Convert to numpy arrays for Numba
        prices = data['Close'].values
        signals_array = signals.values
        
        # Run backtest
        equity, positions, num_trades = _vectorized_backtest(
            prices, signals_array, initial_capital
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(equity, prices, positions, num_trades)
        
        return {
            'equity': equity,
            'positions': positions,
            'signals': signals_array,
            'metrics': metrics,
            'dates': data.index.values
        }
    
    def _calculate_metrics(
        self,
        equity: np.ndarray,
        prices: np.ndarray,
        positions: np.ndarray,
        num_trades: int
    ) -> Dict:
        """
        Calculate backtest performance metrics.
        
        Args:
            equity: Equity curve
            prices: Price array
            positions: Position array
            num_trades: Number of trades
            
        Returns:
            Dictionary of metrics
        """
        # Returns
        returns = np.diff(equity) / equity[:-1]
        returns = returns[~np.isnan(returns)]
        
        # Total return
        total_return = (equity[-1] - equity[0]) / equity[0]
        
        # CAGR (assuming daily data)
        n_years = len(equity) / 252
        if n_years > 0:
            cagr = (1 + total_return) ** (1 / n_years) - 1
        else:
            cagr = 0.0
        
        # Sharpe ratio (annualized, assuming 252 trading days)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe = 0.0
        
        # Max drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = np.min(drawdown)
        
        # Win rate (approximate based on positive return days)
        if len(returns) > 0:
            win_rate = np.sum(returns > 0) / len(returns)
        else:
            win_rate = 0.0
        
        # Expectancy (average return per trade)
        if num_trades > 0:
            expectancy = total_return / num_trades
        else:
            expectancy = 0.0
        
        return {
            'total_return': float(total_return),
            'cagr': float(cagr),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'num_trades': int(num_trades),
            'expectancy': float(expectancy)
        }
    
    def run_multiple_backtests(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy_configs: List[StrategyConfig],
        initial_capital: float = 100000.0,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Run backtests for multiple symbols and strategies.
        
        Args:
            data_dict: Dictionary mapping symbol to DataFrame
            strategy_configs: List of strategy configurations
            initial_capital: Starting capital
            show_progress: Whether to show progress bar
            
        Returns:
            DataFrame with results for all [strategy, symbol] pairs
        """
        results = []
        
        symbols = list(data_dict.keys())
        total_runs = len(symbols) * len(strategy_configs)
        
        if show_progress:
            from tqdm import tqdm
            pbar = tqdm(total=total_runs, desc="Running backtests")
        
        for symbol in symbols:
            data = data_dict[symbol]
            
            for config in strategy_configs:
                try:
                    result = self.run_backtest(data, config, initial_capital)
                    
                    # Store summary metrics
                    results.append({
                        'symbol': symbol,
                        'strategy': config.name,
                        'params': str(config.params),
                        **result['metrics']
                    })
                    
                    # Store detailed results to Zarr
                    self._store_to_zarr(symbol, config, result)
                    
                except Exception as e:
                    print(f"Error backtesting {symbol} with {config.name}: {e}")
                
                if show_progress:
                    pbar.update(1)
        
        if show_progress:
            pbar.close()
        
        # Create DataFrame
        results_df = pd.DataFrame(results)
        
        # Save to Parquet
        if len(results_df) > 0:
            parquet_path = self.output_path / "summary.parquet"
            results_df.to_parquet(parquet_path, index=False)
        
        # Update metadata
        self._update_metadata(strategy_configs, symbols)
        
        return results_df
    
    def _store_to_zarr(self, symbol: str, config: StrategyConfig, result: Dict):
        """
        Store detailed backtest results to Zarr.
        
        Args:
            symbol: Stock symbol
            config: Strategy configuration
            result: Backtest result dictionary
        """
        # Create Zarr store
        store = zarr.open(str(self.zarr_path), mode='a')
        
        # Create group for this backtest
        group_name = f"{symbol}/{config.name}_{hash(str(config.params)) % 1000000}"
        group = store.require_group(group_name)
        
        # Store arrays with compression
        group.array('equity', result['equity'], chunks=(1000,), compressor=zarr.Blosc())
        group.array('positions', result['positions'], chunks=(1000,), compressor=zarr.Blosc())
        group.array('signals', result['signals'], chunks=(1000,), compressor=zarr.Blosc())
        
        # Store dates as string array
        dates_str = [str(d) for d in result['dates']]
        group.array('dates', dates_str, chunks=(1000,))
        
        # Store metrics as attributes
        group.attrs['metrics'] = result['metrics']
        group.attrs['params'] = config.params
    
    def _update_metadata(self, strategy_configs: List[StrategyConfig], symbols: List[str]):
        """
        Update metadata JSON with backtest information.
        
        Args:
            strategy_configs: List of strategy configurations
            symbols: List of symbols backtested
        """
        metadata = {
            'strategies': [
                {
                    'name': config.name,
                    'params': config.params,
                    'description': config.description
                }
                for config in strategy_configs
            ],
            'symbols': symbols,
            'num_backtests': len(symbols) * len(strategy_configs)
        }
        
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_summary(self) -> Optional[pd.DataFrame]:
        """
        Load summary results from Parquet.
        
        Returns:
            DataFrame with summary results or None if not found
        """
        parquet_path = self.output_path / "summary.parquet"
        if not parquet_path.exists():
            return None
        
        return pd.read_parquet(parquet_path)
    
    def load_detailed_results(self, symbol: str, strategy_name: str) -> Optional[Dict]:
        """
        Load detailed results for a specific backtest from Zarr.
        
        Args:
            symbol: Stock symbol
            strategy_name: Strategy name
            
        Returns:
            Dictionary with detailed results or None if not found
        """
        if not self.zarr_path.exists():
            return None
        
        store = zarr.open(str(self.zarr_path), mode='r')
        
        # Find matching group
        if symbol in store:
            symbol_group = store[symbol]
            for group_name in symbol_group.group_keys():
                if strategy_name in group_name:
                    group = symbol_group[group_name]
                    return {
                        'equity': group['equity'][:],
                        'positions': group['positions'][:],
                        'signals': group['signals'][:],
                        'dates': group['dates'][:],
                        'metrics': dict(group.attrs['metrics']),
                        'params': dict(group.attrs['params'])
                    }
        
        return None
