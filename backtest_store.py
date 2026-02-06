"""
Backtest Storage and Retrieval System
=====================================
Centralized Zarr-based storage for backtest results with instant lookup.

Design:
- Single Zarr store (not per-symbol files) for efficient subsetting/querying
- Stores all backtest results with strategy/parameter/exit rule metadata
- Fast lookups by (symbol, strategy, params, exit_rule) combinations
- Scalable for all stocks/strategies without query slowdown
- Supports adding win_rate/num_trades to scanner signal rows
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import zarr
from numcodecs import Blosc, JSON
from datetime import datetime


class BacktestStore:
    """
    Centralized backtest storage and retrieval using Zarr format.
    
    Design:
    - Single Zarr store for all backtests
    - Metadata stored in structured arrays for fast filtering
    - Trade-level details stored separately for memory efficiency
    - Supports quick stats lookup and detailed trade log retrieval
    """
    
    def __init__(self, store_path: str = "./data/backtests/store.zarr"):
        """
        Initialize BacktestStore.
        
        Args:
            store_path: Path to Zarr store
        """
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_store()
    
    def _init_store(self):
        """Initialize or open Zarr store with appropriate structure."""
        # Open store in read/write mode
        self.root = zarr.open(str(self.store_path), mode='a')
        
        # Initialize metadata array if not exists
        if 'metadata' not in self.root:
            # Create structured array for metadata
            # This allows fast filtering without loading all data
            self.root.create_dataset(
                'metadata',
                shape=(0,),
                dtype=[
                    ('symbol', 'U20'),
                    ('strategy', 'U50'),
                    ('params_hash', 'U32'),
                    ('exit_rule', 'U50'),
                    ('win_rate', 'f4'),
                    ('num_trades', 'i4'),
                    ('total_return', 'f4'),
                    ('cagr', 'f4'),
                    ('sharpe_ratio', 'f4'),
                    ('max_drawdown', 'f4'),
                    ('expectancy', 'f4'),
                    ('start_date', 'U10'),
                    ('end_date', 'U10'),
                    ('timestamp', 'U32')
                ],
                chunks=(1000,)
            )
        
        # Initialize params lookup if not exists
        if 'params_lookup' not in self.root:
            self.root.create_group('params_lookup')
        
        # Initialize trade details if not exists
        if 'trade_details' not in self.root:
            self.root.create_group('trade_details')
        
        # Initialize equity curves if not exists
        if 'equity_curves' not in self.root:
            self.root.create_group('equity_curves')
    
    def _hash_params(self, params: Dict[str, Any]) -> str:
        """Create stable hash for parameter dictionary."""
        # Sort keys for stable hash
        sorted_params = json.dumps(params, sort_keys=True)
        return str(hash(sorted_params) % (10**10))
    
    def store_backtest(
        self,
        symbol: str,
        strategy: str,
        params: Dict[str, Any],
        exit_rule: str,
        metrics: Dict[str, float],
        equity_curve: Optional[np.ndarray] = None,
        positions: Optional[np.ndarray] = None,
        dates: Optional[np.ndarray] = None,
        trades: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Store backtest results.
        
        Args:
            symbol: Stock symbol
            strategy: Strategy name
            params: Strategy parameters
            exit_rule: Exit rule identifier
            metrics: Performance metrics dict
            equity_curve: Equity curve array (optional)
            positions: Position array (optional)
            dates: Date array (optional)
            trades: Trade log DataFrame (optional)
            
        Returns:
            Unique identifier for this backtest
        """
        params_hash = self._hash_params(params)
        backtest_id = f"{symbol}_{strategy}_{params_hash}_{exit_rule}"
        
        # Prepare metadata entry
        metadata_entry = np.array(
            [(
                symbol,
                strategy,
                params_hash,
                exit_rule,
                metrics.get('win_rate', 0.0),
                metrics.get('num_trades', 0),
                metrics.get('total_return', 0.0),
                metrics.get('cagr', 0.0),
                metrics.get('sharpe_ratio', 0.0),
                metrics.get('max_drawdown', 0.0),
                metrics.get('expectancy', 0.0),
                dates[0] if dates is not None and len(dates) > 0 else '',
                dates[-1] if dates is not None and len(dates) > 0 else '',
                datetime.now().isoformat()
            )],
            dtype=self.root['metadata'].dtype
        )
        
        # Append to metadata
        current_size = self.root['metadata'].shape[0]
        self.root['metadata'].resize(current_size + 1)
        self.root['metadata'][current_size] = metadata_entry[0]
        
        # Store params in metadata attributes (simpler than separate array)
        # We'll store as attribute on a dummy dataset
        params_group = self.root['params_lookup']
        if params_hash not in params_group:
            # Create a small dummy array to hold the params as attrs
            params_array = params_group.create_dataset(
                params_hash,
                shape=(1,),
                dtype='i1'
            )
            params_array.attrs['params'] = json.dumps(params)
        
        # Store equity curve if provided
        if equity_curve is not None:
            equity_group = self.root['equity_curves']
            if backtest_id in equity_group:
                del equity_group[backtest_id]
            
            equity_data = equity_group.create_dataset(
                backtest_id,
                shape=equity_curve.shape,
                dtype=equity_curve.dtype,
                data=equity_curve,
                chunks=(min(len(equity_curve), 1000),)
            )
            
            # Store dates and positions as attributes
            if dates is not None:
                equity_data.attrs['dates'] = [str(d) for d in dates]
            if positions is not None:
                equity_data.attrs['positions'] = positions.tolist()
        
        # Store trade details if provided
        if trades is not None and len(trades) > 0:
            trade_group = self.root['trade_details']
            if backtest_id in trade_group:
                del trade_group[backtest_id]
            
            # Convert DataFrame to JSON-serializable dict
            trades_dict = trades.to_dict('records')
            # Convert any datetime objects to strings
            for trade in trades_dict:
                for key, value in trade.items():
                    if pd.api.types.is_datetime64_any_dtype(type(value)) or isinstance(value, (pd.Timestamp, np.datetime64)):
                        trade[key] = str(value)
            
            # Store as JSON in a text array
            trades_json = json.dumps(trades_dict)
            # Use a simple string array
            trade_data = trade_group.create_dataset(
                backtest_id,
                shape=(1,),
                dtype=f'U{len(trades_json)}'  # Unicode string with appropriate length
            )
            trade_data[0] = trades_json
        
        return backtest_id
    
    def get_stats(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        exit_rule: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve backtest statistics with optional filtering.
        
        Args:
            symbol: Filter by symbol (optional)
            strategy: Filter by strategy (optional)
            params: Filter by exact params (optional)
            exit_rule: Filter by exit rule (optional)
            
        Returns:
            DataFrame with matching backtest statistics
        """
        if 'metadata' not in self.root or self.root['metadata'].shape[0] == 0:
            return pd.DataFrame()
        
        # Load metadata
        metadata = self.root['metadata'][:]
        df = pd.DataFrame(metadata)
        
        # Apply filters
        if symbol is not None:
            df = df[df['symbol'] == symbol]
        
        if strategy is not None:
            df = df[df['strategy'] == strategy]
        
        if params is not None:
            params_hash = self._hash_params(params)
            df = df[df['params_hash'] == params_hash]
        
        if exit_rule is not None:
            df = df[df['exit_rule'] == exit_rule]
        
        # Decode params for readability
        if len(df) > 0:
            params_lookup = self.root['params_lookup']
            def get_params(h):
                if h in params_lookup:
                    return json.loads(params_lookup[h].attrs['params'])
                return {}
            df['params'] = df['params_hash'].apply(get_params)
        
        return df
    
    def get_detailed_results(
        self,
        symbol: str,
        strategy: str,
        params: Dict[str, Any],
        exit_rule: str = 'default'
    ) -> Optional[Dict]:
        """
        Retrieve detailed backtest results including equity curve and trades.
        
        Args:
            symbol: Stock symbol
            strategy: Strategy name
            params: Strategy parameters
            exit_rule: Exit rule identifier
            
        Returns:
            Dictionary with detailed results or None if not found
        """
        params_hash = self._hash_params(params)
        backtest_id = f"{symbol}_{strategy}_{params_hash}_{exit_rule}"
        
        # Get stats from metadata
        stats_df = self.get_stats(symbol, strategy, params, exit_rule)
        if len(stats_df) == 0:
            return None
        
        stats = stats_df.iloc[0].to_dict()
        
        result = {
            'symbol': symbol,
            'strategy': strategy,
            'params': params,
            'exit_rule': exit_rule,
            'metrics': {
                'win_rate': float(stats['win_rate']),
                'num_trades': int(stats['num_trades']),
                'total_return': float(stats['total_return']),
                'cagr': float(stats['cagr']),
                'sharpe_ratio': float(stats['sharpe_ratio']),
                'max_drawdown': float(stats['max_drawdown']),
                'expectancy': float(stats['expectancy'])
            }
        }
        
        # Load equity curve if available
        equity_group = self.root.get('equity_curves')
        if equity_group is not None and backtest_id in equity_group:
            equity_data = equity_group[backtest_id]
            result['equity_curve'] = equity_data[:]
            
            if 'dates' in equity_data.attrs:
                result['dates'] = equity_data.attrs['dates']
            if 'positions' in equity_data.attrs:
                result['positions'] = equity_data.attrs['positions']
        
        # Load trade details if available
        trade_group = self.root.get('trade_details')
        if trade_group is not None and backtest_id in trade_group:
            trade_json = trade_group[backtest_id][0]
            trades_dict = json.loads(trade_json)
            result['trades'] = pd.DataFrame(trades_dict)
        
        return result
    
    def bulk_get_stats(
        self,
        lookups: List[Tuple[str, str, Dict[str, Any], str]]
    ) -> pd.DataFrame:
        """
        Efficiently retrieve stats for multiple backtest combinations.
        
        Args:
            lookups: List of (symbol, strategy, params, exit_rule) tuples
            
        Returns:
            DataFrame with stats for all requested combinations
        """
        results = []
        
        for symbol, strategy, params, exit_rule in lookups:
            stats_df = self.get_stats(symbol, strategy, params, exit_rule)
            if len(stats_df) > 0:
                results.append(stats_df.iloc[0])
        
        if not results:
            return pd.DataFrame()
        
        return pd.DataFrame(results)
    
    def get_all_stats(self) -> pd.DataFrame:
        """
        Get statistics for all stored backtests.
        
        Returns:
            DataFrame with all backtest statistics
        """
        return self.get_stats()
    
    def delete_backtest(
        self,
        symbol: str,
        strategy: str,
        params: Dict[str, Any],
        exit_rule: str = 'default'
    ) -> bool:
        """
        Delete a specific backtest from the store.
        
        Args:
            symbol: Stock symbol
            strategy: Strategy name
            params: Strategy parameters
            exit_rule: Exit rule identifier
            
        Returns:
            True if deleted, False if not found
        """
        params_hash = self._hash_params(params)
        backtest_id = f"{symbol}_{strategy}_{params_hash}_{exit_rule}"
        
        # Find and remove from metadata
        metadata = self.root['metadata'][:]
        mask = ~((metadata['symbol'] == symbol) &
                 (metadata['strategy'] == strategy) &
                 (metadata['params_hash'] == params_hash) &
                 (metadata['exit_rule'] == exit_rule))
        
        if np.all(mask):
            return False  # Not found
        
        # Update metadata
        filtered_metadata = metadata[mask]
        self.root['metadata'].resize(len(filtered_metadata))
        self.root['metadata'][:] = filtered_metadata
        
        # Delete equity curve if exists
        equity_group = self.root.get('equity_curves')
        if equity_group is not None and backtest_id in equity_group:
            del equity_group[backtest_id]
        
        # Delete trade details if exists
        trade_group = self.root.get('trade_details')
        if trade_group is not None and backtest_id in trade_group:
            del trade_group[backtest_id]
        
        return True
    
    def clear_all(self):
        """Clear all backtest data from the store."""
        # Recreate metadata with empty array
        if 'metadata' in self.root:
            del self.root['metadata']
        
        # Recreate groups
        for group_name in ['params_lookup', 'trade_details', 'equity_curves']:
            if group_name in self.root:
                del self.root[group_name]
        
        # Reinitialize
        self._init_store()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the backtest store.
        
        Returns:
            Dictionary with summary stats
        """
        if 'metadata' not in self.root or self.root['metadata'].shape[0] == 0:
            return {
                'total_backtests': 0,
                'unique_symbols': 0,
                'unique_strategies': 0,
                'storage_size_mb': 0
            }
        
        metadata = self.root['metadata'][:]
        df = pd.DataFrame(metadata)
        
        # Calculate storage size
        storage_size = 0
        if self.store_path.exists():
            for path in self.store_path.rglob('*'):
                if path.is_file():
                    storage_size += path.stat().st_size
        
        return {
            'total_backtests': len(df),
            'unique_symbols': df['symbol'].nunique(),
            'unique_strategies': df['strategy'].nunique(),
            'storage_size_mb': storage_size / (1024 * 1024)
        }
    
    def save_group_set(self, name: str, symbols: List[str], strategies: List[str], 
                       params_list: List[Dict[str, Any]], exit_rules: List[str]) -> None:
        """
        Save a group set (collection of symbol/strategy/params/exit combinations).
        
        Args:
            name: Name for the group set
            symbols: List of symbols
            strategies: List of strategy names
            params_list: List of parameter dictionaries (one per strategy)
            exit_rules: List of exit rules
        """
        # Initialize group sets storage if not exists
        if 'group_sets' not in self.root:
            self.root.create_group('group_sets')
        
        group_sets = self.root['group_sets']
        
        # Create or update group set
        if name in group_sets:
            del group_sets[name]
        
        group_data = group_sets.create_group(name)
        group_data.attrs['symbols'] = json.dumps(symbols)
        group_data.attrs['strategies'] = json.dumps(strategies)
        group_data.attrs['params_list'] = json.dumps(params_list)
        group_data.attrs['exit_rules'] = json.dumps(exit_rules)
        group_data.attrs['created_at'] = datetime.now().isoformat()
    
    def load_group_set(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved group set.
        
        Args:
            name: Name of the group set
            
        Returns:
            Dictionary with group set data or None if not found
        """
        if 'group_sets' not in self.root:
            return None
        
        group_sets = self.root['group_sets']
        if name not in group_sets:
            return None
        
        group_data = group_sets[name]
        return {
            'name': name,
            'symbols': json.loads(group_data.attrs['symbols']),
            'strategies': json.loads(group_data.attrs['strategies']),
            'params_list': json.loads(group_data.attrs['params_list']),
            'exit_rules': json.loads(group_data.attrs['exit_rules']),
            'created_at': group_data.attrs.get('created_at', '')
        }
    
    def list_group_sets(self) -> List[str]:
        """
        List all saved group sets.
        
        Returns:
            List of group set names
        """
        if 'group_sets' not in self.root:
            return []
        
        return list(self.root['group_sets'].keys())
    
    def delete_group_set(self, name: str) -> bool:
        """
        Delete a saved group set.
        
        Args:
            name: Name of the group set
            
        Returns:
            True if deleted, False if not found
        """
        if 'group_sets' not in self.root:
            return False
        
        group_sets = self.root['group_sets']
        if name not in group_sets:
            return False
        
        del group_sets[name]
        return True
