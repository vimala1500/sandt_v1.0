"""
Strategy Module
===============
Defines trading strategies with configurable parameters.
Supports Moving Average Crossover and RSI Mean-Reversion strategies.
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class StrategyRegistry:
    """
    Registry for trading strategies.
    
    Design:
    - Centralizes strategy definitions
    - Allows parameterization for backtesting
    - Generates signals (1=long, -1=short, 0=neutral)
    """
    
    def __init__(self):
        self.strategies: Dict[str, Callable] = {
            'ma_crossover': self.ma_crossover_strategy,
            'rsi_meanrev': self.rsi_meanrev_strategy
        }
    
    @staticmethod
    def ma_crossover_strategy(
        data: pd.DataFrame,
        fast_period: int = 20,
        slow_period: int = 50
    ) -> pd.Series:
        """
        Moving Average Crossover Strategy.
        
        Generates long signal when fast MA crosses above slow MA,
        short signal when fast MA crosses below slow MA.
        
        Args:
            data: DataFrame with price data and indicators
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            
        Returns:
            Series of signals (1=long, -1=short, 0=neutral)
        """
        fast_ma_col = f"SMA_{fast_period}"
        slow_ma_col = f"SMA_{slow_period}"
        
        # Check if required columns exist
        if fast_ma_col not in data.columns or slow_ma_col not in data.columns:
            raise ValueError(f"Required columns {fast_ma_col} or {slow_ma_col} not found in data")
        
        fast_ma = data[fast_ma_col]
        slow_ma = data[slow_ma_col]
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Long when fast > slow
        signals[fast_ma > slow_ma] = 1
        
        # Short when fast < slow
        signals[fast_ma < slow_ma] = -1
        
        return signals
    
    @staticmethod
    def rsi_meanrev_strategy(
        data: pd.DataFrame,
        rsi_period: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ) -> pd.Series:
        """
        RSI Mean-Reversion Strategy.
        
        Generates long signal when RSI crosses below oversold threshold,
        short signal when RSI crosses above overbought threshold.
        
        Args:
            data: DataFrame with price data and indicators
            rsi_period: RSI period
            oversold: Oversold threshold (default 30)
            overbought: Overbought threshold (default 70)
            
        Returns:
            Series of signals (1=long, -1=short, 0=neutral)
        """
        rsi_col = f"RSI_{rsi_period}"
        
        # Check if required column exists
        if rsi_col not in data.columns:
            raise ValueError(f"Required column {rsi_col} not found in data")
        
        rsi = data[rsi_col]
        
        # Generate signals
        signals = pd.Series(0, index=data.index)
        
        # Long when RSI < oversold (expecting bounce)
        signals[rsi < oversold] = 1
        
        # Short when RSI > overbought (expecting pullback)
        signals[rsi > overbought] = -1
        
        return signals
    
    def get_strategy(self, strategy_name: str) -> Callable:
        """
        Get strategy function by name.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy function
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(self.strategies.keys())}")
        
        return self.strategies[strategy_name]
    
    def list_strategies(self) -> List[str]:
        """
        List all available strategies.
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())
    
    def create_config(
        self,
        strategy_name: str,
        params: Dict[str, Any],
        description: str = ""
    ) -> StrategyConfig:
        """
        Create a strategy configuration.
        
        Args:
            strategy_name: Name of the strategy
            params: Strategy parameters
            description: Optional description
            
        Returns:
            StrategyConfig instance
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return StrategyConfig(
            name=strategy_name,
            params=params,
            description=description
        )
    
    def generate_param_combinations(
        self,
        strategy_name: str,
        param_grid: Dict[str, List[Any]]
    ) -> List[StrategyConfig]:
        """
        Generate multiple strategy configurations from parameter grid.
        
        Args:
            strategy_name: Name of the strategy
            param_grid: Dictionary mapping parameter names to lists of values
            
        Returns:
            List of StrategyConfig instances
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        # Generate all combinations
        import itertools
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        configs = []
        for combination in itertools.product(*values):
            params = dict(zip(keys, combination))
            config = StrategyConfig(
                name=strategy_name,
                params=params,
                description=f"{strategy_name}_{params}"
            )
            configs.append(config)
        
        return configs


# Predefined strategy configurations for common use cases
DEFAULT_STRATEGIES = {
    'ma_crossover_20_50': StrategyConfig(
        name='ma_crossover',
        params={'fast_period': 20, 'slow_period': 50},
        description='20/50 MA Crossover'
    ),
    'ma_crossover_50_200': StrategyConfig(
        name='ma_crossover',
        params={'fast_period': 50, 'slow_period': 200},
        description='50/200 MA Crossover (Golden Cross)'
    ),
    'rsi_meanrev_14': StrategyConfig(
        name='rsi_meanrev',
        params={'rsi_period': 14, 'oversold': 30, 'overbought': 70},
        description='RSI(14) Mean Reversion 30/70'
    ),
    'rsi_meanrev_14_tight': StrategyConfig(
        name='rsi_meanrev',
        params={'rsi_period': 14, 'oversold': 20, 'overbought': 80},
        description='RSI(14) Mean Reversion 20/80 (Tight)'
    )
}
