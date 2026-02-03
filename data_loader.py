"""
Data Loader Module
==================
Handles loading and processing of Parquet OHLCV stock price files.
Optimized for Google Drive storage with symbol-wise file organization.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import pyarrow.parquet as pq


class DataLoader:
    """
    Loads OHLCV price data from Parquet files.
    
    Design:
    - Reads symbol-wise Parquet files from Google Drive (or local path)
    - Standard OHLCV columns: Date, Open, High, Low, Close, Volume
    - Returns pandas DataFrames with DatetimeIndex
    """
    
    def __init__(self, data_path: str = "./data/stock_data"):
        """
        Initialize DataLoader with path to Parquet files.
        
        Args:
            data_path: Root directory containing symbol-wise Parquet files
        """
        self.data_path = Path(data_path)
        self.cache: Dict[str, pd.DataFrame] = {}
    
    def load_symbol(self, symbol: str, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        Load OHLCV data for a single symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with OHLCV data, DatetimeIndex, or None if not found
        """
        if use_cache and symbol in self.cache:
            return self.cache[symbol]
        
        file_path = self.data_path / f"{symbol}.parquet"
        
        if not file_path.exists():
            print(f"Warning: Data file not found for {symbol} at {file_path}")
            return None
        
        try:
            df = pd.read_parquet(file_path)
            
            # Normalize column names to title case for consistency
            df.columns = df.columns.str.title()
            
            # Ensure datetime index
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.set_index('Date')
            elif not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Sort by date
            df = df.sort_index()
            
            # Validate required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                print(f"Warning: Missing columns for {symbol}: {missing}")
                return None
            
            if use_cache:
                self.cache[symbol] = df
            
            return df
            
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
            return None
    
    def load_multiple_symbols(self, symbols: List[str], use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Load OHLCV data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        result = {}
        for symbol in symbols:
            df = self.load_symbol(symbol, use_cache=use_cache)
            if df is not None:
                result[symbol] = df
        return result
    
    def list_available_symbols(self) -> List[str]:
        """
        List all available symbols in the data directory.
        
        Returns:
            List of available stock symbols
        """
        if not self.data_path.exists():
            return []
        
        parquet_files = list(self.data_path.glob("*.parquet"))
        symbols = [f.stem for f in parquet_files]
        return sorted(symbols)
    
    def get_date_range(self, symbol: str) -> Optional[tuple]:
        """
        Get the date range for a symbol's data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (start_date, end_date) or None if not found
        """
        df = self.load_symbol(symbol)
        if df is None or len(df) == 0:
            return None
        return (df.index.min(), df.index.max())
    
    def clear_cache(self):
        """Clear the data cache."""
        self.cache.clear()
