"""
Main Orchestration Module
==========================
Coordinates the full pipeline: data loading, indicator computation,
backtesting, scanning, and reporting.
"""

import os
import argparse
from pathlib import Path
from typing import List, Optional
import json

from data_loader import DataLoader
from indicator_engine import IndicatorEngine
from strategy import StrategyRegistry, DEFAULT_STRATEGIES
from backtest_engine import BacktestEngine
from scanner import Scanner


class Pipeline:
    """
    Main orchestration class for the stock analysis pipeline.
    
    Design:
    - Coordinates all pipeline stages
    - Configurable for different workflows
    - Supports both full runs and individual stages
    """
    
    def __init__(
        self,
        data_path: str = "./data/stock_data",
        indicator_path: str = "./data/indicators",
        backtest_path: str = "./data/backtests"
    ):
        """
        Initialize pipeline with paths.
        
        Args:
            data_path: Path to Parquet stock data
            indicator_path: Path to store indicators
            backtest_path: Path to store backtest results
        """
        self.data_loader = DataLoader(data_path)
        self.indicator_engine = IndicatorEngine(indicator_path)
        self.backtest_engine = BacktestEngine(backtest_path)
        self.strategy_registry = StrategyRegistry()
        self.scanner = Scanner(self.indicator_engine, self.backtest_engine)
    
    def run_full_pipeline(
        self,
        symbols: Optional[List[str]] = None,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [7, 14, 21, 28],
        strategy_names: Optional[List[str]] = None
    ):
        """
        Run the complete pipeline from data loading to backtesting.
        
        Args:
            symbols: List of symbols to process (None = all available)
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
            strategy_names: Strategy names to backtest (None = use defaults)
        """
        print("=" * 60)
        print("Stock Analysis & Trading Pipeline - Full Run")
        print("=" * 60)
        
        # Stage 1: Load data
        print("\n[Stage 1/4] Loading stock data...")
        if symbols is None:
            symbols = self.data_loader.list_available_symbols()
        
        if not symbols:
            print("Error: No symbols found. Please ensure data files are available.")
            return
        
        print(f"Loading data for {len(symbols)} symbols...")
        data_dict = self.data_loader.load_multiple_symbols(symbols)
        print(f"Successfully loaded {len(data_dict)} symbols")
        
        # Stage 2: Compute indicators
        print("\n[Stage 2/4] Computing technical indicators...")
        print(f"SMA periods: {sma_periods}")
        print(f"RSI periods: {rsi_periods}")
        self.indicator_engine.process_multiple_symbols(
            data_dict,
            sma_periods=sma_periods,
            rsi_periods=rsi_periods,
            show_progress=True
        )
        print("Indicators computed and stored to HDF5/JSON")
        
        # Stage 3: Run backtests
        print("\n[Stage 3/4] Running backtests...")
        
        # Prepare strategy configs
        if strategy_names is None:
            strategy_configs = list(DEFAULT_STRATEGIES.values())
        else:
            strategy_configs = [DEFAULT_STRATEGIES[name] for name in strategy_names 
                              if name in DEFAULT_STRATEGIES]
        
        print(f"Testing {len(strategy_configs)} strategies on {len(data_dict)} symbols...")
        
        # Load data with indicators
        data_with_indicators = {}
        for symbol in data_dict.keys():
            indicator_data = self.indicator_engine.load_indicators(symbol)
            if indicator_data is not None:
                data_with_indicators[symbol] = indicator_data
        
        results_df = self.backtest_engine.run_multiple_backtests(
            data_with_indicators,
            strategy_configs,
            show_progress=True
        )
        
        print(f"\nBacktest results: {len(results_df)} total runs")
        print("\nTop 5 by Sharpe Ratio:")
        print(results_df.nlargest(5, 'sharpe_ratio')[
            ['symbol', 'strategy', 'sharpe_ratio', 'cagr', 'win_rate']
        ])
        
        # Stage 4: Generate summary
        print("\n[Stage 4/4] Generating summary...")
        self._generate_summary(results_df)
        
        print("\n" + "=" * 60)
        print("Pipeline completed successfully!")
        print("=" * 60)
    
    def run_indicators_only(
        self,
        symbols: Optional[List[str]] = None,
        sma_periods: List[int] = [20, 50, 200],
        rsi_periods: List[int] = [7, 14, 21, 28]
    ):
        """
        Run indicator computation only.
        
        Args:
            symbols: List of symbols to process
            sma_periods: SMA periods to compute
            rsi_periods: RSI periods to compute
        """
        print("Computing indicators only...")
        
        if symbols is None:
            symbols = self.data_loader.list_available_symbols()
        
        data_dict = self.data_loader.load_multiple_symbols(symbols)
        
        self.indicator_engine.process_multiple_symbols(
            data_dict,
            sma_periods=sma_periods,
            rsi_periods=rsi_periods,
            show_progress=True
        )
        
        print(f"Indicators computed for {len(data_dict)} symbols")
    
    def run_backtests_only(
        self,
        symbols: Optional[List[str]] = None,
        strategy_names: Optional[List[str]] = None
    ):
        """
        Run backtests only (requires indicators to be pre-computed).
        
        Args:
            symbols: List of symbols to backtest
            strategy_names: Strategy names to test
        """
        print("Running backtests only...")
        
        # Load symbols with indicators
        if symbols is None:
            symbols = self.indicator_engine.list_available_symbols()
        
        data_dict = {}
        for symbol in symbols:
            data = self.indicator_engine.load_indicators(symbol)
            if data is not None:
                data_dict[symbol] = data
        
        # Prepare strategies
        if strategy_names is None:
            strategy_configs = list(DEFAULT_STRATEGIES.values())
        else:
            strategy_configs = [DEFAULT_STRATEGIES[name] for name in strategy_names 
                              if name in DEFAULT_STRATEGIES]
        
        # Run backtests
        results_df = self.backtest_engine.run_multiple_backtests(
            data_dict,
            strategy_configs,
            show_progress=True
        )
        
        print(f"\nBacktest results: {len(results_df)} total runs")
        print(results_df.describe())
    
    def run_scan(
        self,
        scan_type: str = 'rsi_oversold',
        **kwargs
    ):
        """
        Run a live scan.
        
        Args:
            scan_type: Type of scan to run
            **kwargs: Scan parameters
        """
        print(f"Running {scan_type} scan...")
        
        symbols = self.indicator_engine.list_available_symbols()
        
        if scan_type == 'rsi_oversold':
            results = self.scanner.scan_rsi_oversold(
                symbols,
                rsi_period=kwargs.get('rsi_period', 14),
                threshold=kwargs.get('threshold', 30)
            )
        elif scan_type == 'rsi_overbought':
            results = self.scanner.scan_rsi_overbought(
                symbols,
                rsi_period=kwargs.get('rsi_period', 14),
                threshold=kwargs.get('threshold', 70)
            )
        elif scan_type == 'ma_crossover':
            results = self.scanner.scan_ma_crossover(
                symbols,
                fast_period=kwargs.get('fast_period', 20),
                slow_period=kwargs.get('slow_period', 50),
                direction=kwargs.get('direction', 'bullish')
            )
        else:
            print(f"Unknown scan type: {scan_type}")
            return
        
        print(f"\nScan results: {len(results)} matches")
        if len(results) > 0:
            print(results)
    
    def _generate_summary(self, results_df):
        """
        Generate and save pipeline summary.
        
        Args:
            results_df: DataFrame with backtest results
        """
        summary = {
            'total_backtests': len(results_df),
            'strategies_tested': results_df['strategy'].nunique(),
            'symbols_tested': results_df['symbol'].nunique(),
            'avg_sharpe': float(results_df['sharpe_ratio'].mean()),
            'avg_cagr': float(results_df['cagr'].mean()),
            'avg_win_rate': float(results_df['win_rate'].mean()),
            'best_strategy': results_df.loc[results_df['sharpe_ratio'].idxmax(), 'strategy'],
            'best_symbol': results_df.loc[results_df['sharpe_ratio'].idxmax(), 'symbol']
        }
        
        print(json.dumps(summary, indent=2))


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description='Stock Analysis & Trading Pipeline')
    
    parser.add_argument(
        '--mode',
        choices=['full', 'indicators', 'backtest', 'scan'],
        default='full',
        help='Pipeline mode to run'
    )
    
    parser.add_argument(
        '--data-path',
        default='./data/stock_data',
        help='Path to Parquet stock data'
    )
    
    parser.add_argument(
        '--indicator-path',
        default='./data/indicators',
        help='Path to store indicators'
    )
    
    parser.add_argument(
        '--backtest-path',
        default='./data/backtests',
        help='Path to store backtest results'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='List of symbols to process (default: all available)'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = Pipeline(
        data_path=args.data_path,
        indicator_path=args.indicator_path,
        backtest_path=args.backtest_path
    )
    
    # Run appropriate mode
    if args.mode == 'full':
        pipeline.run_full_pipeline(symbols=args.symbols)
    elif args.mode == 'indicators':
        pipeline.run_indicators_only(symbols=args.symbols)
    elif args.mode == 'backtest':
        pipeline.run_backtests_only(symbols=args.symbols)
    elif args.mode == 'scan':
        pipeline.run_scan()


if __name__ == '__main__':
    main()
