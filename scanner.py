"""
Scanner Module
==============
Finds stocks matching live conditions and cross-references with backtest stats.
Supports configurable scanning criteria (e.g., RSI < 20, MA crossovers).
"""

from typing import Dict, List, Optional, Callable
import pandas as pd
import numpy as np
from datetime import datetime


class Scanner:
    """
    Live stock scanner for finding opportunities.
    
    Design:
    - Loads latest indicator values
    - Evaluates custom scan conditions
    - Cross-links with historical backtest performance
    - Returns ranked results
    """
    
    def __init__(self, indicator_engine, backtest_engine):
        """
        Initialize Scanner.
        
        Args:
            indicator_engine: IndicatorEngine instance
            backtest_engine: BacktestEngine instance
        """
        self.indicator_engine = indicator_engine
        self.backtest_engine = backtest_engine
    
    def scan_rsi_oversold(
        self,
        symbols: List[str],
        rsi_period: int = 14,
        threshold: float = 30
    ) -> pd.DataFrame:
        """
        Scan for stocks with RSI below threshold (oversold).
        
        Args:
            symbols: List of symbols to scan
            rsi_period: RSI period
            threshold: Oversold threshold
            
        Returns:
            DataFrame with matching stocks and their metrics
        """
        results = []
        
        for symbol in symbols:
            try:
                # Load indicators
                data = self.indicator_engine.load_indicators(symbol)
                if data is None or len(data) == 0:
                    continue
                
                # Ensure RSI period is available (compute on-demand if needed)
                success, was_computed = self.indicator_engine.ensure_rsi_period(symbol, rsi_period)
                if not success:
                    continue
                
                # Reload data only if we just computed a new RSI period
                if was_computed:
                    data = self.indicator_engine.load_indicators(symbol)
                    if data is None:
                        continue
                
                # Get latest RSI value
                rsi_col = f"RSI_{rsi_period}"
                if rsi_col not in data.columns:
                    continue
                
                latest_rsi = data[rsi_col].iloc[-1]
                
                # Check condition
                if pd.notna(latest_rsi) and latest_rsi < threshold:
                    results.append({
                        'symbol': symbol,
                        'rsi': float(latest_rsi),
                        'close': float(data['Close'].iloc[-1]),
                        'date': data.index[-1]
                    })
            
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Add backtest stats if available
        df = self._add_backtest_stats(df, 'rsi_meanrev')
        
        # Sort by RSI (most oversold first)
        df = df.sort_values('rsi')
        
        return df
    
    def scan_rsi_overbought(
        self,
        symbols: List[str],
        rsi_period: int = 14,
        threshold: float = 70
    ) -> pd.DataFrame:
        """
        Scan for stocks with RSI above threshold (overbought).
        
        Args:
            symbols: List of symbols to scan
            rsi_period: RSI period
            threshold: Overbought threshold
            
        Returns:
            DataFrame with matching stocks and their metrics
        """
        results = []
        
        for symbol in symbols:
            try:
                # Load indicators
                data = self.indicator_engine.load_indicators(symbol)
                if data is None or len(data) == 0:
                    continue
                
                # Ensure RSI period is available (compute on-demand if needed)
                success, was_computed = self.indicator_engine.ensure_rsi_period(symbol, rsi_period)
                if not success:
                    continue
                
                # Reload data only if we just computed a new RSI period
                if was_computed:
                    data = self.indicator_engine.load_indicators(symbol)
                    if data is None:
                        continue
                
                # Get latest RSI value
                rsi_col = f"RSI_{rsi_period}"
                if rsi_col not in data.columns:
                    continue
                
                latest_rsi = data[rsi_col].iloc[-1]
                
                # Check condition
                if pd.notna(latest_rsi) and latest_rsi > threshold:
                    results.append({
                        'symbol': symbol,
                        'rsi': float(latest_rsi),
                        'close': float(data['Close'].iloc[-1]),
                        'date': data.index[-1]
                    })
            
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Add backtest stats if available
        df = self._add_backtest_stats(df, 'rsi_meanrev')
        
        # Sort by RSI (most overbought first)
        df = df.sort_values('rsi', ascending=False)
        
        return df
    
    def scan_ma_crossover(
        self,
        symbols: List[str],
        fast_period: int = 20,
        slow_period: int = 50,
        direction: str = 'bullish'
    ) -> pd.DataFrame:
        """
        Scan for moving average crossovers.
        
        Args:
            symbols: List of symbols to scan
            fast_period: Fast MA period
            slow_period: Slow MA period
            direction: 'bullish' for fast > slow, 'bearish' for fast < slow
            
        Returns:
            DataFrame with matching stocks and their metrics
        """
        results = []
        
        for symbol in symbols:
            try:
                # Load indicators
                data = self.indicator_engine.load_indicators(symbol)
                if data is None or len(data) < 2:
                    continue
                
                # Get MA columns
                fast_col = f"SMA_{fast_period}"
                slow_col = f"SMA_{slow_period}"
                
                if fast_col not in data.columns or slow_col not in data.columns:
                    continue
                
                # Get latest and previous values
                fast_current = data[fast_col].iloc[-1]
                fast_prev = data[fast_col].iloc[-2]
                slow_current = data[slow_col].iloc[-1]
                slow_prev = data[slow_col].iloc[-2]
                
                # Check for crossover
                is_match = False
                if direction == 'bullish':
                    # Fast crossed above slow
                    is_match = (fast_prev <= slow_prev) and (fast_current > slow_current)
                elif direction == 'bearish':
                    # Fast crossed below slow
                    is_match = (fast_prev >= slow_prev) and (fast_current < slow_current)
                
                if is_match and pd.notna(fast_current) and pd.notna(slow_current):
                    results.append({
                        'symbol': symbol,
                        f'sma_{fast_period}': float(fast_current),
                        f'sma_{slow_period}': float(slow_current),
                        'close': float(data['Close'].iloc[-1]),
                        'date': data.index[-1],
                        'crossover_type': direction
                    })
            
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Add backtest stats if available
        df = self._add_backtest_stats(df, 'ma_crossover')
        
        return df
    
    def scan_by_indicator(
        self,
        symbols: List[str],
        indicator: str,
        operator: str,
        threshold: float,
        include_value: bool = True
    ) -> pd.DataFrame:
        """
        Scan stocks by any indicator with flexible comparison operators.
        
        Args:
            symbols: List of symbols to scan
            indicator: Indicator column name (e.g., 'RSI_14', 'EMA_50', 'hammer')
            operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
            threshold: Threshold value to compare against
            include_value: Whether to include the indicator value in results
            
        Returns:
            DataFrame with matching stocks and their metrics
        """
        results = []
        
        for symbol in symbols:
            try:
                # Load indicators
                data = self.indicator_engine.load_indicators(symbol)
                if data is None or len(data) == 0:
                    continue
                
                # Check if indicator exists
                if indicator not in data.columns:
                    continue
                
                # Get latest value
                latest_value = data[indicator].iloc[-1]
                
                # Skip NaN values
                if pd.isna(latest_value):
                    continue
                
                # Evaluate condition
                is_match = False
                if operator == '>':
                    is_match = latest_value > threshold
                elif operator == '<':
                    is_match = latest_value < threshold
                elif operator == '>=':
                    is_match = latest_value >= threshold
                elif operator == '<=':
                    is_match = latest_value <= threshold
                elif operator == '==':
                    is_match = latest_value == threshold
                elif operator == '!=':
                    is_match = latest_value != threshold
                else:
                    print(f"Unknown operator: {operator}")
                    continue
                
                if is_match:
                    result_dict = {
                        'symbol': symbol,
                        'close': float(data['Close'].iloc[-1]),
                        'date': data.index[-1]
                    }
                    if include_value:
                        result_dict[indicator] = float(latest_value)
                    results.append(result_dict)
            
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Sort by indicator value if included
        if include_value and indicator in df.columns:
            df = df.sort_values(indicator)
        
        return df
    
    def custom_scan(
        self,
        symbols: List[str],
        condition_func: Callable[[pd.DataFrame], bool],
        strategy_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Run a custom scan with user-defined condition.
        
        Args:
            symbols: List of symbols to scan
            condition_func: Function that takes DataFrame and returns True if condition met
            strategy_name: Optional strategy name for linking backtest stats
            
        Returns:
            DataFrame with matching stocks
        """
        results = []
        
        for symbol in symbols:
            try:
                # Load indicators
                data = self.indicator_engine.load_indicators(symbol)
                if data is None or len(data) == 0:
                    continue
                
                # Check condition
                if condition_func(data):
                    results.append({
                        'symbol': symbol,
                        'close': float(data['Close'].iloc[-1]),
                        'date': data.index[-1]
                    })
            
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Add backtest stats if available and strategy specified
        if strategy_name:
            df = self._add_backtest_stats(df, strategy_name)
        
        return df
    
    def get_available_indicators(self) -> List[str]:
        """
        Get list of available indicators from stored data.
        
        Returns:
            List of indicator column names
        """
        # Try to get indicators from first available symbol
        symbols = self.indicator_engine.list_available_symbols()
        if not symbols:
            return []
        
        # Load first symbol to get column names
        data = self.indicator_engine.load_indicators(symbols[0])
        if data is None:
            return []
        
        # Filter out OHLCV columns
        ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        indicator_cols = [col for col in data.columns if col not in ohlcv_cols]
        
        return sorted(indicator_cols)
    
    def _add_backtest_stats(self, scan_df: pd.DataFrame, strategy_name: str) -> pd.DataFrame:
        """
        Add backtest statistics to scan results.
        
        Args:
            scan_df: DataFrame with scan results
            strategy_name: Strategy name to look up
            
        Returns:
            DataFrame with added backtest metrics
        """
        # Load backtest summary
        summary = self.backtest_engine.load_summary()
        if summary is None or len(summary) == 0:
            return scan_df
        
        # Filter to relevant strategy
        strategy_results = summary[summary['strategy'] == strategy_name]
        if len(strategy_results) == 0:
            return scan_df
        
        # Merge on symbol
        merged = scan_df.merge(
            strategy_results[['symbol', 'cagr', 'sharpe_ratio', 'win_rate', 'max_drawdown', 'num_trades']],
            on='symbol',
            how='left'
        )
        
        return merged
    
    def get_top_performers(
        self,
        strategy_name: str,
        metric: str = 'sharpe_ratio',
        min_trades: int = 10,
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        Get top performing stocks for a strategy based on backtest results.
        
        Args:
            strategy_name: Strategy name
            metric: Metric to rank by (e.g., 'sharpe_ratio', 'cagr', 'win_rate')
            min_trades: Minimum number of trades required
            top_n: Number of top stocks to return
            
        Returns:
            DataFrame with top performers
        """
        # Load backtest summary
        summary = self.backtest_engine.load_summary()
        if summary is None or len(summary) == 0:
            return pd.DataFrame()
        
        # Filter to strategy and minimum trades
        filtered = summary[
            (summary['strategy'] == strategy_name) &
            (summary['num_trades'] >= min_trades)
        ]
        
        if len(filtered) == 0:
            return pd.DataFrame()
        
        # Sort by metric and take top N
        top = filtered.sort_values(metric, ascending=False).head(top_n)
        
        return top
