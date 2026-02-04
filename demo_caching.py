#!/usr/bin/env python3
"""
Demonstrate Indicator Caching System

This script shows how the indicator caching/storage system works:
1. First computation: Slow (computes and stores)
2. Subsequent loads: Fast (loads from cache)
3. Verification: Shows cache files and contents
"""

import time
import os
from pathlib import Path
import pandas as pd

from data_loader import DataLoader
from indicator_engine import IndicatorEngine


def print_banner(text):
    """Print a section banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def check_cache_exists(cache_path):
    """Check if cache files exist"""
    hdf5_path = Path(cache_path) / "indicators.h5"
    config_path = Path(cache_path) / "config.json"
    
    return hdf5_path.exists() and config_path.exists()


def get_cache_size(cache_path):
    """Get total size of cache files"""
    hdf5_path = Path(cache_path) / "indicators.h5"
    config_path = Path(cache_path) / "config.json"
    
    total_size = 0
    if hdf5_path.exists():
        total_size += hdf5_path.stat().st_size
    if config_path.exists():
        total_size += config_path.stat().st_size
    
    return total_size


def format_size(bytes_size):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def demo_caching():
    """Demonstrate the caching system"""
    
    print_banner("Indicator Caching System Demo")
    
    # Use a test cache directory
    cache_path = "./data/demo_indicators"
    
    # Clean up any existing demo cache
    if os.path.exists(cache_path):
        import shutil
        shutil.rmtree(cache_path)
        print(f"✓ Cleaned up old demo cache")
    
    # Load sample data
    print_banner("Step 1: Load Sample Price Data")
    loader = DataLoader("./data/prices")
    symbols = loader.list_available_symbols()[:3]  # Use first 3 symbols
    
    if not symbols:
        print("❌ No price data found in ./data/prices/")
        print("   Please ensure you have Parquet files in the data/prices directory")
        return
    
    print(f"✓ Found {len(symbols)} symbols: {symbols}")
    data_dict = loader.load_multiple_symbols(symbols)
    print(f"✓ Loaded {len(data_dict)} symbols")
    
    for symbol, df in data_dict.items():
        print(f"  - {symbol}: {len(df)} rows, date range {df.index[0].date()} to {df.index[-1].date()}")
    
    # First computation (slow)
    print_banner("Step 2: First Computation (Computing + Storing)")
    engine = IndicatorEngine(cache_path)
    
    print("Computing indicators for the first time...")
    print("This will compute SMA and RSI indicators and store them to disk.")
    print()
    
    start_time = time.time()
    engine.process_multiple_symbols(
        data_dict,
        sma_periods=[20, 50, 200],
        rsi_periods=[7, 14, 21, 28],
        show_progress=False
    )
    compute_time = time.time() - start_time
    
    print(f"✓ Computed and stored indicators in {compute_time:.3f} seconds")
    
    # Check cache files
    cache_size = get_cache_size(cache_path)
    print(f"✓ Cache files created: {format_size(cache_size)}")
    print(f"  - {cache_path}/indicators.h5")
    print(f"  - {cache_path}/config.json")
    
    # Subsequent load (fast)
    print_banner("Step 3: Subsequent Load (From Cache)")
    
    # Create a new engine instance to simulate fresh session
    engine2 = IndicatorEngine(cache_path)
    
    print("Loading indicators from cache (no computation)...")
    print()
    
    load_times = []
    for symbol in symbols:
        start_time = time.time()
        data = engine2.load_indicators(symbol)
        load_time = time.time() - start_time
        load_times.append(load_time)
        
        print(f"✓ Loaded {symbol}: {len(data)} rows in {load_time:.4f} seconds")
        print(f"  Columns: {', '.join(data.columns.tolist())}")
    
    avg_load_time = sum(load_times) / len(load_times)
    speedup = compute_time / avg_load_time if avg_load_time > 0 else 0
    
    print()
    print(f"Average load time: {avg_load_time:.4f} seconds")
    print(f"Speedup: {speedup:.1f}x faster than computing!")
    
    # Verify cache contents
    print_banner("Step 4: Verify Cache Contents")
    
    # Show configuration
    config = engine2.get_config()
    print("Configuration (from config.json):")
    for symbol, params in config.items():
        print(f"  {symbol}:")
        print(f"    SMA periods: {params['sma_periods']}")
        print(f"    RSI periods: {params['rsi_periods']}")
    
    # Show available symbols
    available_symbols = engine2.list_available_symbols()
    print(f"\nAvailable symbols in cache: {available_symbols}")
    
    # Show sample data
    print("\nSample data (last 5 rows of first symbol):")
    sample_data = engine2.load_indicators(symbols[0])
    
    # Select available columns (in case periods were changed)
    display_cols = ['Close']
    for col in ['SMA_20', 'SMA_50', 'RSI_14', 'RSI_21']:
        if col in sample_data.columns:
            display_cols.append(col)
    
    print(sample_data.tail(5)[display_cols].to_string())
    
    # Demonstrate cache persistence
    print_banner("Step 5: Cache Persistence Test")
    
    print("Simulating application restart...")
    print("Creating new IndicatorEngine instance (as if app restarted)")
    print()
    
    # Simulate restart by creating completely new engine
    engine3 = IndicatorEngine(cache_path)
    
    start_time = time.time()
    reloaded_data = engine3.load_indicators(symbols[0])
    reload_time = time.time() - start_time
    
    print(f"✓ Successfully loaded {symbols[0]} from persistent cache")
    print(f"✓ Load time: {reload_time:.4f} seconds")
    print(f"✓ Data shape: {reloaded_data.shape}")
    print()
    print("Cache persists across application restarts! ✓")
    
    # Summary
    print_banner("Summary")
    
    print("✓ Indicators ARE cached and stored for each symbol")
    print(f"✓ Storage location: {cache_path}/")
    print(f"✓ Storage format: HDF5 (indicators.h5) + JSON (config.json)")
    print(f"✓ Cache size: {format_size(cache_size)}")
    print(f"✓ Performance improvement: {speedup:.1f}x faster")
    print()
    print("Benefits:")
    print("  - No need to recompute indicators every time")
    print("  - Instant loading from disk")
    print("  - Persists across application restarts")
    print("  - Compressed storage saves disk space")
    print()
    print("To use in production:")
    print("  1. Run 'python compute_indicators.py' once")
    print("  2. All subsequent scans use cached indicators")
    print("  3. Rerun compute_indicators.py when you have new price data")
    
    # Cleanup
    print_banner("Cleanup")
    print(f"Demo cache remains at: {cache_path}/")
    print("You can safely delete it or keep it for reference")
    print()


if __name__ == '__main__':
    try:
        demo_caching()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
