#!/usr/bin/env python3
"""
Test script to demonstrate the new indicator scanning UI features.
Sets up test data with indicators and launches the Dash UI.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from indicator_engine import IndicatorEngine
from data_loader import DataLoader

def setup_test_data():
    """Setup test data with indicators for UI demonstration."""
    print("Setting up test data with indicators...")
    
    # Use existing price data
    data_loader = DataLoader("./data/prices")
    symbols = data_loader.list_available_symbols()[:5]  # Use first 5 symbols
    
    if not symbols:
        print("No price data found. Creating synthetic test data...")
        # Create synthetic data
        dates = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='D')
        np.random.seed(42)
        
        symbols = ['TESTSTOCK1', 'TESTSTOCK2', 'TESTSTOCK3']
        data_dict = {}
        
        for i, symbol in enumerate(symbols):
            # Create varied price patterns for different stocks
            base_price = 100 + i * 50
            trend = np.cumsum(np.random.randn(200) * 2)
            close_prices = base_price + trend
            
            df = pd.DataFrame({
                'Open': close_prices + np.random.randn(200) * 0.5,
                'High': close_prices + np.abs(np.random.randn(200) * 1),
                'Low': close_prices - np.abs(np.random.randn(200) * 1),
                'Close': close_prices,
                'Volume': np.random.randint(1000000, 10000000, 200)
            }, index=dates)
            data_dict[symbol] = df
    else:
        print(f"Found {len(symbols)} symbols in price data. Computing indicators...")
        data_dict = data_loader.load_multiple_symbols(symbols)
    
    # Compute indicators with all new features
    engine = IndicatorEngine("./data/indicators")
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50, 200],
        rsi_periods=[7, 14, 21, 28],
        ema_periods=[10, 20, 50, 100, 200],  # Subset for demo
        include_candlestick_patterns=True,
        include_streak_indicators=True,
        include_high_low_days=True,
        show_progress=True
    )
    
    print(f"\n✅ Indicators computed for {len(symbols)} symbols")
    print("\nAvailable indicators include:")
    print("  - RSI (7, 14, 21, 28 periods)")
    print("  - SMA (20, 50, 200 periods)")
    print("  - EMA (10, 20, 50, 100, 200 periods)")
    print("  - 12 Candlestick patterns (hammer, doji, engulfing, etc.)")
    print("  - Consecutive higher/lower streaks")
    print("  - Days since previous high/low")
    
    return symbols

if __name__ == '__main__':
    # Setup test data
    symbols = setup_test_data()
    
    print("\n" + "="*70)
    print("Starting Dash UI...")
    print("Open your browser to: http://localhost:8050")
    print("="*70 + "\n")
    
    # Launch UI
    from dash_ui import create_app
    ui = create_app()
    ui.run(host='0.0.0.0', port=8050, debug=False)
