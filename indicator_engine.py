"""
Indicator Engine Module
========================
Computes technical indicators (SMA, RSI, EMA, candlestick patterns, etc.) and stores them to HDF5/JSON.
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
from candlestick_patterns import compute_all_patterns


class IndicatorEngine:
    """
    Computes and stores technical indicators.
    
    Design:
    - Computes SMA and RSI indicators with configurable periods
    - Stores indicators to HDF5 for efficient array storage
    - Stores metadata/config to JSON for readability
    - Supports batch processing across multiple symbols
    """
    
    def __init__(self, output_path: str = "./data/indicators"):
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
    def compute_rsi_wilder(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Compute Relative Strength Index (RSI) using Wilder's smoothing method.
        
        This matches TradingView's RSI implementation exactly, using Wilder's
        recursive averaging instead of exponential moving average (EWM).
        
        Formula:
        - For the first 'period' rows: Use simple average of gains/losses
        - For subsequent rows (n > period):
            avg_gain[n] = (avg_gain[n-1] * (period-1) + gain[n]) / period
            avg_loss[n] = (avg_loss[n-1] * (period-1) + loss[n]) / period
        
        Args:
            prices: Price series (typically Close prices)
            period: RSI period (default 14)
            
        Returns:
            RSI series with values between 0-100, matching TradingView calculations
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Initialize arrays for average gain and loss (all NaN initially)
        avg_gains = pd.Series(index=prices.index, dtype=float)
        avg_losses = pd.Series(index=prices.index, dtype=float)
        
        # Calculate the first average using simple mean for the first 'period' values
        # Note: First value after diff is NaN, so we use values from index 1 to period
        first_avg_gain = gains.iloc[1:period+1].mean()
        first_avg_loss = losses.iloc[1:period+1].mean()
        
        avg_gains.iloc[period] = first_avg_gain
        avg_losses.iloc[period] = first_avg_loss
        
        # Apply Wilder's smoothing for subsequent values
        for i in range(period + 1, len(prices)):
            avg_gains.iloc[i] = (avg_gains.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_losses.iloc[i] = (avg_losses.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        # Handle special case: when avg_losses = 0, RS is infinite, RSI = 100
        # But keep NaN where we don't have enough data
        rsi = rsi.where(pd.notna(avg_gains) & pd.notna(avg_losses), np.nan)
        rsi = rsi.where(avg_losses != 0, 100.0)
        
        return rsi
    
    @staticmethod
    def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Compute Relative Strength Index (RSI) using Wilder's smoothing method.
        
        This is an alias for compute_rsi_wilder() to maintain backwards compatibility.
        See compute_rsi_wilder() for detailed documentation.
        
        Args:
            prices: Price series (typically Close prices)
            period: RSI period (default 14)
            
        Returns:
            RSI series with values between 0-100
        """
        return IndicatorEngine.compute_rsi_wilder(prices, period)
    
    @staticmethod
    def compute_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Compute Exponential Moving Average.
        
        Args:
            prices: Price series (typically Close prices)
            period: EMA period
            
        Returns:
            EMA series with same index as input
        """
        return prices.ewm(span=period, adjust=False, min_periods=period).mean()
    
    @staticmethod
    def compute_days_since_prev_high(df: pd.DataFrame, lookback_years: int = 5) -> pd.Series:
        """
        Compute days since previous all-time high.
        
        For each date, if the High is a new all-time high (over lookback period),
        mark with the number of trading days since the previous record high.
        Fill with 0 otherwise.
        
        Args:
            df: DataFrame with OHLC data
            lookback_years: Number of years to look back (default 5)
            
        Returns:
            Series with days since previous high
        """
        high_prices = df['High'].copy()
        result = pd.Series(0, index=df.index, dtype=int)
        
        # Use expanding window for initial period, then rolling for lookback period
        lookback_days = lookback_years * 252  # Approximate trading days per year
        
        for i in range(1, len(high_prices)):
            # Determine lookback window
            start_idx = max(0, i - lookback_days)
            window = high_prices.iloc[start_idx:i]
            
            if len(window) == 0:
                continue
            
            current_high = high_prices.iloc[i]
            prev_max = window.max()
            
            # Check if current is new all-time high in the window
            if current_high > prev_max:
                # Find the index of the previous high
                prev_high_indices = window[window == prev_max].index
                if len(prev_high_indices) > 0:
                    prev_high_idx = df.index.get_loc(prev_high_indices[-1])
                    days_since = i - prev_high_idx
                    result.iloc[i] = days_since
        
        return result
    
    @staticmethod
    def compute_days_since_prev_low(df: pd.DataFrame, lookback_years: int = 5) -> pd.Series:
        """
        Compute days since previous all-time low.
        
        For each date, if the Low is a new all-time low (over lookback period),
        mark with the number of trading days since the previous record low.
        Fill with 0 otherwise.
        
        Args:
            df: DataFrame with OHLC data
            lookback_years: Number of years to look back (default 5)
            
        Returns:
            Series with days since previous low
        """
        low_prices = df['Low'].copy()
        result = pd.Series(0, index=df.index, dtype=int)
        
        # Use expanding window for initial period, then rolling for lookback period
        lookback_days = lookback_years * 252  # Approximate trading days per year
        
        for i in range(1, len(low_prices)):
            # Determine lookback window
            start_idx = max(0, i - lookback_days)
            window = low_prices.iloc[start_idx:i]
            
            if len(window) == 0:
                continue
            
            current_low = low_prices.iloc[i]
            prev_min = window.min()
            
            # Check if current is new all-time low in the window
            if current_low < prev_min:
                # Find the index of the previous low
                prev_low_indices = window[window == prev_min].index
                if len(prev_low_indices) > 0:
                    prev_low_idx = df.index.get_loc(prev_low_indices[-1])
                    days_since = i - prev_low_idx
                    result.iloc[i] = days_since
        
        return result
    
    @staticmethod
    def compute_consec_higher_high(df: pd.DataFrame) -> pd.Series:
        """
        Compute streak of consecutive days with strictly higher highs.
        
        For each row, count the number of consecutive days where High is
        strictly higher than the previous day's High.
        
        Args:
            df: DataFrame with High column
            
        Returns:
            Series with consecutive higher high count
        """
        high_prices = df['High']
        result = pd.Series(0, index=df.index, dtype=int)
        
        streak = 0
        for i in range(1, len(high_prices)):
            if high_prices.iloc[i] > high_prices.iloc[i-1]:
                streak += 1
            else:
                streak = 0
            result.iloc[i] = streak
        
        return result
    
    @staticmethod
    def compute_consec_lower_low(df: pd.DataFrame) -> pd.Series:
        """
        Compute streak of consecutive days with strictly lower lows.
        
        For each row, count the number of consecutive days where Low is
        strictly lower than the previous day's Low.
        
        Args:
            df: DataFrame with Low column
            
        Returns:
            Series with consecutive lower low count
        """
        low_prices = df['Low']
        result = pd.Series(0, index=df.index, dtype=int)
        
        streak = 0
        for i in range(1, len(low_prices)):
            if low_prices.iloc[i] < low_prices.iloc[i-1]:
                streak += 1
            else:
                streak = 0
            result.iloc[i] = streak
        
        return result
    
    def compute_indicators(
        self,
        data: pd.DataFrame,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14],
        ema_periods: Optional[List[int]] = None,
        include_candlestick_patterns: bool = True,
        include_streak_indicators: bool = True,
        include_high_low_days: bool = True
    ) -> pd.DataFrame:
        """
        Compute all configured indicators for a given dataset.
        
        Args:
            data: OHLCV DataFrame with DatetimeIndex
            sma_periods: List of SMA periods to compute
            rsi_periods: List of RSI periods to compute
            ema_periods: List of EMA periods to compute (default: 2-200, then 250-1000 by 50s)
            include_candlestick_patterns: Whether to compute candlestick patterns
            include_streak_indicators: Whether to compute consecutive higher/lower streaks
            include_high_low_days: Whether to compute days since prev high/low
            
        Returns:
            DataFrame with original data + computed indicators
        """
        # Start with original data
        result = data.copy()
        
        # Collect all new columns in a dictionary for efficient concatenation
        new_columns = {}
        
        # Compute SMAs
        for period in sma_periods:
            col_name = f"SMA_{period}"
            new_columns[col_name] = self.compute_sma(data['Close'], period)
        
        # Compute RSIs
        for period in rsi_periods:
            col_name = f"RSI_{period}"
            new_columns[col_name] = self.compute_rsi(data['Close'], period)
        
        # Compute EMAs (2-200, then 250, 300, ..., 1000)
        if ema_periods is None:
            ema_periods = list(range(2, 201)) + list(range(250, 1001, 50))
        
        for period in ema_periods:
            col_name = f"EMA_{period}"
            new_columns[col_name] = self.compute_ema(data['Close'], period)
        
        # Compute candlestick patterns
        if include_candlestick_patterns:
            patterns = compute_all_patterns(data)
            new_columns.update(patterns)
        
        # Compute streak indicators
        if include_streak_indicators:
            new_columns['consec_higher_high'] = self.compute_consec_higher_high(data)
            new_columns['consec_lower_low'] = self.compute_consec_lower_low(data)
        
        # Compute days since prev high/low
        if include_high_low_days:
            new_columns['days_since_prev_high'] = self.compute_days_since_prev_high(data)
            new_columns['days_since_prev_low'] = self.compute_days_since_prev_low(data)
        
        # Concatenate all new columns at once to avoid fragmentation
        if new_columns:
            new_df = pd.DataFrame(new_columns, index=data.index)
            result = pd.concat([result, new_df], axis=1)
        
        return result
    
    def process_and_store(
        self,
        symbol: str,
        data: pd.DataFrame,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14],
        ema_periods: Optional[List[int]] = None,
        include_candlestick_patterns: bool = True,
        include_streak_indicators: bool = True,
        include_high_low_days: bool = True
    ):
        """
        Compute indicators and store to HDF5.
        
        Args:
            symbol: Stock symbol
            data: OHLCV DataFrame
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
            ema_periods: EMA periods to compute
            include_candlestick_patterns: Whether to compute candlestick patterns
            include_streak_indicators: Whether to compute consecutive higher/lower streaks
            include_high_low_days: Whether to compute days since prev high/low
        """
        # Compute indicators
        indicators_df = self.compute_indicators(
            data, 
            sma_periods, 
            rsi_periods,
            ema_periods,
            include_candlestick_patterns,
            include_streak_indicators,
            include_high_low_days
        )
        
        # Store to HDF5
        with pd.HDFStore(self.hdf5_path, mode='a', complevel=9, complib='zlib') as store:
            store.put(f"/{symbol}", indicators_df, format='table')
        
        # Update config
        self._update_config(
            symbol, 
            sma_periods, 
            rsi_periods, 
            ema_periods,
            include_candlestick_patterns,
            include_streak_indicators,
            include_high_low_days
        )
    
    def process_multiple_symbols(
        self,
        data_dict: Dict[str, pd.DataFrame],
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [14],
        ema_periods: Optional[List[int]] = None,
        include_candlestick_patterns: bool = True,
        include_streak_indicators: bool = True,
        include_high_low_days: bool = True,
        show_progress: bool = True
    ):
        """
        Process indicators for multiple symbols.
        
        Args:
            data_dict: Dictionary mapping symbol to OHLCV DataFrame
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
            ema_periods: EMA periods to compute
            include_candlestick_patterns: Whether to compute candlestick patterns
            include_streak_indicators: Whether to compute consecutive higher/lower streaks
            include_high_low_days: Whether to compute days since prev high/low
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
                    rsi_periods,
                    ema_periods,
                    include_candlestick_patterns,
                    include_streak_indicators,
                    include_high_low_days
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
    
    def _update_config(
        self, 
        symbol: str, 
        sma_periods: List[int], 
        rsi_periods: List[int],
        ema_periods: Optional[List[int]] = None,
        include_candlestick_patterns: bool = True,
        include_streak_indicators: bool = True,
        include_high_low_days: bool = True
    ):
        """
        Update configuration JSON with indicator parameters.
        
        Args:
            symbol: Stock symbol
            sma_periods: SMA periods used
            rsi_periods: RSI periods used
            ema_periods: EMA periods used
            include_candlestick_patterns: Whether candlestick patterns were computed
            include_streak_indicators: Whether streak indicators were computed
            include_high_low_days: Whether days since prev high/low were computed
        """
        from datetime import datetime
        
        config = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        
        if ema_periods is None:
            ema_periods = list(range(2, 201)) + list(range(250, 1001, 50))
        
        config[symbol] = {
            'sma_periods': sma_periods,
            'rsi_periods': rsi_periods,
            'ema_periods': ema_periods,
            'candlestick_patterns': include_candlestick_patterns,
            'streak_indicators': include_streak_indicators,
            'high_low_days': include_high_low_days,
            'last_computed': datetime.now().isoformat()
        }
        
        # Update global metadata
        if '_metadata' not in config:
            config['_metadata'] = {}
        
        config['_metadata']['last_computation_date'] = datetime.now().isoformat()
        config['_metadata']['symbols_count'] = sum(1 for k in config.keys() if k != '_metadata')
        
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
    
    def has_rsi_period(self, symbol: str, period: int) -> bool:
        """
        Check if a specific RSI period is cached for a symbol.
        
        Args:
            symbol: Stock symbol
            period: RSI period to check
            
        Returns:
            True if the RSI period is cached, False otherwise
        """
        data = self.load_indicators(symbol)
        if data is None:
            return False
        
        rsi_col = f"RSI_{period}"
        return rsi_col in data.columns
    
    def compute_and_cache_rsi_period(self, symbol: str, period: int) -> bool:
        """
        Compute and cache a specific RSI period for a symbol.
        
        This method loads the existing cached data, computes the new RSI period,
        and updates the cache. If the symbol doesn't have any cached data,
        it will return False.
        
        Args:
            symbol: Stock symbol
            period: RSI period to compute
            
        Returns:
            True if successful, False otherwise
        """
        # Load existing cached data
        data = self.load_indicators(symbol)
        if data is None:
            return False
        
        # Check if this RSI period already exists
        rsi_col = f"RSI_{period}"
        if rsi_col in data.columns:
            # Already cached, nothing to do
            return True
        
        # Compute the new RSI period
        try:
            data[rsi_col] = self.compute_rsi(data['Close'], period)
            
            # Store updated data back to HDF5
            with pd.HDFStore(self.hdf5_path, mode='a', complevel=9, complib='zlib') as store:
                store.put(f"/{symbol}", data, format='table')
            
            # Update config to include this new period
            config = self.get_config()
            if symbol in config:
                config[symbol]['rsi_periods'].append(period)
                config[symbol]['rsi_periods'].sort()
            else:
                config[symbol] = {
                    'sma_periods': [],
                    'rsi_periods': [period]
                }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error computing RSI({period}) for {symbol}: {e}")
            return False
    
    def ensure_rsi_period(self, symbol: str, period: int) -> Tuple[bool, bool]:
        """
        Ensure that a specific RSI period is available for a symbol.
        
        This method checks if the RSI period exists in the cache, and if not,
        computes and caches it on-the-fly.
        
        Args:
            symbol: Stock symbol
            period: RSI period needed
            
        Returns:
            Tuple of (success, was_computed) where:
            - success: True if the RSI period is available
            - was_computed: True if the period was just computed (cache updated)
        """
        if self.has_rsi_period(symbol, period):
            return True, False
        
        success = self.compute_and_cache_rsi_period(symbol, period)
        return success, success
    
    def get_metadata(self) -> Dict:
        """
        Get metadata about indicators computation.
        
        Returns:
            Dictionary with last_computation_date and symbols_count
        """
        config = self.get_config()
        metadata = config.get('_metadata', {})
        
        # Fallback if metadata doesn't exist
        if not metadata:
            symbols = self.list_available_symbols()
            metadata = {
                'last_computation_date': None,
                'symbols_count': len(symbols)
            }
        
        return metadata
