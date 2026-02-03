#!/usr/bin/env python3
"""
Test script to generate sample data and test the system locally.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def generate_sample_ohlcv_data(symbol, num_days=500, start_price=100):
    """Generate sample OHLCV data for testing."""
    np.random.seed(hash(symbol) % 2**32)
    
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')
    
    # Generate price series with random walk
    returns = np.random.normal(0.0005, 0.02, num_days)
    close_prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLCV
    data = pd.DataFrame({
        'Date': dates,
        'Open': close_prices * (1 + np.random.uniform(-0.01, 0.01, num_days)),
        'High': close_prices * (1 + np.random.uniform(0, 0.02, num_days)),
        'Low': close_prices * (1 - np.random.uniform(0, 0.02, num_days)),
        'Close': close_prices,
        'Volume': np.random.randint(1000000, 10000000, num_days)
    })
    
    # Ensure High is highest and Low is lowest
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    return data

def main():
    """Generate sample data and test the system."""
    print("=" * 70)
    print("Stock Analysis System - Local Test")
    print("=" * 70)
    
    # Create data directories
    data_dir = Path('./data')
    stock_data_dir = data_dir / 'stock_data'
    indicators_dir = data_dir / 'indicators'
    backtests_dir = data_dir / 'backtests'
    
    for dir_path in [stock_data_dir, indicators_dir, backtests_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("\n[1/4] Generating sample data...")
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    for symbol in symbols:
        print(f"  Generating {symbol}...")
        data = generate_sample_ohlcv_data(symbol)
        output_path = stock_data_dir / f"{symbol}.parquet"
        data.to_parquet(output_path, index=False)
    
    print(f"\n✓ Generated {len(symbols)} sample stock files in {stock_data_dir}")
    
    # Test the pipeline
    print("\n[2/4] Testing data loader...")
    from data_loader import DataLoader
    
    loader = DataLoader(str(stock_data_dir))
    available = loader.list_available_symbols()
    print(f"  Found {len(available)} symbols: {', '.join(available)}")
    
    # Load one symbol to verify
    test_data = loader.load_symbol('AAPL')
    print(f"  Sample data shape: {test_data.shape}")
    print(f"  Date range: {test_data.index.min()} to {test_data.index.max()}")
    
    # Test indicator computation
    print("\n[3/4] Testing indicator computation...")
    from indicator_engine import IndicatorEngine
    
    engine = IndicatorEngine(str(indicators_dir))
    data_dict = loader.load_multiple_symbols(symbols[:3])  # Just test with 3 symbols
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50],
        rsi_periods=[14],
        show_progress=True
    )
    print(f"✓ Computed indicators for {len(data_dict)} symbols")
    
    # Test backtest
    print("\n[4/4] Testing backtests...")
    from backtest_engine import BacktestEngine
    from strategy import DEFAULT_STRATEGIES
    
    backtest_engine = BacktestEngine(str(backtests_dir))
    
    # Load data with indicators
    data_with_indicators = {}
    for symbol in data_dict.keys():
        indicator_data = engine.load_indicators(symbol)
        if indicator_data is not None:
            data_with_indicators[symbol] = indicator_data
    
    # Run backtests with just one strategy for testing
    strategy_configs = [DEFAULT_STRATEGIES['ma_crossover_20_50']]
    results = backtest_engine.run_multiple_backtests(
        data_with_indicators,
        strategy_configs,
        show_progress=True
    )
    
    print("\n✓ Backtest Results:")
    print(results[['symbol', 'strategy', 'sharpe_ratio', 'cagr', 'win_rate']])
    
    print("\n" + "=" * 70)
    print("✓ All tests passed! Data is ready.")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Start the web UI: python app.py")
    print("  2. Run full pipeline: python main.py --mode full")
    print("  3. Run scans: python main.py --mode scan")
    print("\nData locations:")
    print(f"  Stock data: {stock_data_dir.absolute()}")
    print(f"  Indicators: {indicators_dir.absolute()}")
    print(f"  Backtests: {backtests_dir.absolute()}")

if __name__ == '__main__':
    main()
