"""
Indicator Engine Module
========================
Computes technical indicators (SMA, RSI) and stores them to HDF5/JSON.
Configurable periods and parameters with efficient computation.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import tables as tb
from tqdm import tqdm


class IndicatorEngine:
    """
    Computes and stores technical indicators.
    
    Design:
    - Computes SMA and RSI indicators with configurable periods
    - Stores indicators to HDF5 for efficient array storage
    - Stores metadata/config to JSON for readability
    - Supports batch processing across multiple symbols
    """
    
    def __init__(self, output_path: str = "/content/drive/MyDrive/indicators"):
        """
        Initialize IndicatorEngine.
        
        Args:
            output_path: Directory to store indicator outputs
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.hdf5_path = self.output_path / "indicators.h5"
        self.config_path = self.output_path / "config.json"
    
    @staticmethod
    def compute_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Compute Simple Moving Average.
        
        Args:
            prices: Price series (typically Close prices)
            period: Moving average period
            
        Returns:
            SMA series with same index as input
        """
        return prices.rolling(window=period, min_periods=period).mean()
    
    @staticmethod
    def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Compute Relative Strength Index (RSI).
        
        Args:
            prices: Price series (typically Close prices)
            period: RSI period (default 14)
            
        Returns:
            RSI series with values between 0-100
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Calculate average gains and losses using exponential moving average
        avg_gains = gains.ewm(span=period, min_periods=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, min_periods=period, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def compute_indicators(
        self,
        data: pd.DataFrame,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14]
    ) -> pd.DataFrame:
        """
        Compute all configured indicators for a given dataset.
        
        Args:
            data: OHLCV DataFrame with DatetimeIndex
            sma_periods: List of SMA periods to compute
            rsi_periods: List of RSI periods to compute
            
        Returns:
            DataFrame with original data + computed indicators
        """
        result = data.copy()
        
        # Compute SMAs
        for period in sma_periods:
            col_name = f"SMA_{period}"
            result[col_name] = self.compute_sma(data['Close'], period)
        
        # Compute RSIs
        for period in rsi_periods:
            col_name = f"RSI_{period}"
            result[col_name] = self.compute_rsi(data['Close'], period)
        
        return result
    
    def process_and_store(
        self,
        symbol: str,
        data: pd.DataFrame,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14]
    ):
        """
        Compute indicators and store to HDF5.
        
        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
        """
        # Compute indicators
        indicators_df = self.compute_indicators(data, sma_periods, rsi_periods)
        
        # Store to HDF5
        with pd.HDFStore(self.hdf5_path, mode='a', complevel=9, complib='zlib') as store:
            store.put(f"/{symbol}", indicators_df, format='table')
        
        # Update config
        self._update_config(symbol, sma_periods, rsi_periods)
    
    def process_multiple_symbols(
        self,
        data_dict: Dict[str, pd.DataFrame],
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14],
        show_progress: bool = True
    ):
        """
        Process indicators for multiple symbols.
        
        Args:
            data_dict: Dictionary mapping symbol to OHLCV DataFrame
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
            show_progress: Whether to show progress bar
        """
        symbols = list(data_dict.keys())
        iterator = tqdm(symbols, desc="Computing indicators") if show_progress else symbols
        
        for symbol in iterator:
            try:
                self.process_and_store(
                    symbol, 
                    data_dict[symbol], 
                    sma_periods, 
                    rsi_periods
                )
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
    
    def load_indicators(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Load indicators for a symbol from HDF5.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            DataFrame with indicators or None if not found
        """
        if not self.hdf5_path.exists():
            return None
        
        try:
            with pd.HDFStore(self.hdf5_path, mode='r') as store:
                if f"/{symbol}" in store:
                    return store.get(f"/{symbol}")
        except Exception as e:
            print(f"Error loading indicators for {symbol}: {e}")
        
        return None
    
    def list_available_symbols(self) -> List[str]:
        """
        List symbols with computed indicators.
        
        Returns:
            List of available symbols
        """
        if not self.hdf5_path.exists():
            return []
        
        try:
            with pd.HDFStore(self.hdf5_path, mode='r') as store:
                return [key.strip('/') for key in store.keys()]
        except Exception as e:
            print(f"Error listing symbols: {e}")
            return []
    
    def _update_config(self, symbol: str, sma_periods: List[int], rsi_periods: List[int]):
        """
        Update configuration JSON with indicator parameters.
        
        Args:
            symbol: Stock symbol
            sma_periods: SMA periods used
            rsi_periods: RSI periods used
        """
        config = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        
        config[symbol] = {
            'sma_periods': sma_periods,
            'rsi_periods': rsi_periods
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_config(self) -> Dict:
        """
        Load configuration.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
