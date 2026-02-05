#!/usr/bin/env python3
"""
Indicator Computation Script
=============================
Standalone script to compute technical indicators from Parquet price data.

This is the REQUIRED first step before using the scanner/web UI.
Run this script whenever:
- Setting up the system for the first time
- After uploading new price data (Parquet files)
- To recompute indicators with different parameters

Usage:
    python compute_indicators.py                    # Use default paths
    python compute_indicators.py --help             # Show all options
    
Environment:
    Works locally, on Railway shell, or in Google Colab
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

from data_loader import DataLoader
from indicator_engine import IndicatorEngine


def print_banner():
    """Print a nice banner."""
    print("=" * 70)
    print("Stock Analysis System - Indicator Computation")
    print("=" * 70)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print("=" * 70)


def validate_data_directory(data_path: Path) -> tuple[bool, str]:
    """
    Validate that the data directory exists and contains Parquet files.
    
    Args:
        data_path: Path to the data directory
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not data_path.exists():
        return False, f"Data directory does not exist: {data_path}"
    
    parquet_files = list(data_path.glob("*.parquet"))
    if not parquet_files:
        return False, f"No Parquet files found in: {data_path}"
    
    return True, f"Found {len(parquet_files)} Parquet files"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compute technical indicators from Parquet price data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute indicators for all symbols with default settings
  python compute_indicators.py
  
  # Use custom data path
  python compute_indicators.py --data-path ./my_data/prices
  
  # Compute only specific symbols
  python compute_indicators.py --symbols AAPL GOOGL MSFT
  
  # Use custom SMA periods
  python compute_indicators.py --sma-periods 10 20 50 100 200
  
  # Use custom RSI periods
  python compute_indicators.py --rsi-periods 7 14 21

Notes:
  - This script MUST be run before using the scanner or web UI
  - Re-run after uploading new price data (Parquet files)
  - Indicators are stored in: data/indicators/indicators.h5 and config.json
        """
    )
    
    parser.add_argument(
        '--data-path',
        default='./data/prices',
        help='Path to Parquet price data directory (default: ./data/prices)'
    )
    
    parser.add_argument(
        '--indicator-path',
        default='./data/indicators',
        help='Path to store computed indicators (default: ./data/indicators)'
    )
    
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Specific symbols to process (default: all available)'
    )
    
    parser.add_argument(
        '--sma-periods',
        type=int,
        nargs='+',
        default=[20, 50, 200],
        help='SMA periods to compute (default: 20 50 200)'
    )
    
    parser.add_argument(
        '--rsi-periods',
        type=int,
        nargs='+',
        default=[7, 14, 21, 28],
        help='RSI periods to compute (default: 7 14 21 28)'
    )
    
    parser.add_argument(
        '--ema-periods',
        type=int,
        nargs='+',
        help='EMA periods to compute (default: 2-200, then 250-1000 by 50s)'
    )
    
    parser.add_argument(
        '--no-candlestick-patterns',
        action='store_true',
        help='Skip candlestick pattern detection'
    )
    
    parser.add_argument(
        '--no-streak-indicators',
        action='store_true',
        help='Skip consecutive higher/lower streak indicators'
    )
    
    parser.add_argument(
        '--no-high-low-days',
        action='store_true',
        help='Skip days since prev high/low indicators'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    data_path = Path(args.data_path)
    indicator_path = Path(args.indicator_path)
    
    if not args.quiet:
        print_banner()
        print("\nConfiguration:")
        print(f"  Data path:       {data_path.absolute()}")
        print(f"  Indicator path:  {indicator_path.absolute()}")
        print(f"  SMA periods:     {args.sma_periods}")
        print(f"  RSI periods:     {args.rsi_periods}")
    
    # Step 1: Validate data directory
    if not args.quiet:
        print_section("Step 1/3: Validating Data Directory")
    
    is_valid, message = validate_data_directory(data_path)
    if not is_valid:
        print(f"\n❌ ERROR: {message}")
        print("\nPlease ensure:")
        print("  1. Price data (Parquet files) exists in the data directory")
        print("  2. The path is correct (use --data-path to specify)")
        print("\nExample Parquet file structure:")
        print("  data/prices/AAPL.parquet")
        print("  data/prices/GOOGL.parquet")
        print("  data/prices/MSFT.parquet")
        sys.exit(1)
    
    if not args.quiet:
        print(f"✓ {message}")
    
    # Step 2: Load price data
    if not args.quiet:
        print_section("Step 2/3: Loading Price Data")
    
    try:
        loader = DataLoader(str(data_path))
        
        if args.symbols:
            symbols = args.symbols
            if not args.quiet:
                print(f"Loading specified symbols: {', '.join(symbols)}")
        else:
            symbols = loader.list_available_symbols()
            if not args.quiet:
                print(f"Loading all available symbols ({len(symbols)} found)")
        
        if not symbols:
            print("\n❌ ERROR: No symbols to process")
            sys.exit(1)
        
        data_dict = loader.load_multiple_symbols(symbols)
        
        if not data_dict:
            print("\n❌ ERROR: Failed to load any symbols")
            sys.exit(1)
        
        if not args.quiet:
            print(f"✓ Successfully loaded {len(data_dict)} symbols")
            print(f"  Symbols: {', '.join(list(data_dict.keys())[:10])}")
            if len(data_dict) > 10:
                print(f"           ... and {len(data_dict) - 10} more")
            
            # Show sample data info
            sample_symbol = list(data_dict.keys())[0]
            sample_data = data_dict[sample_symbol]
            print(f"\n  Sample data ({sample_symbol}):")
            print(f"    Rows: {len(sample_data)}")
            print(f"    Date range: {sample_data.index.min().date()} to {sample_data.index.max().date()}")
            print(f"    Columns: {', '.join(sample_data.columns.tolist())}")
    
    except Exception as e:
        print(f"\n❌ ERROR loading data: {e}")
        sys.exit(1)
    
    # Step 3: Compute indicators
    if not args.quiet:
        print_section("Step 3/3: Computing Technical Indicators")
        print(f"\nComputing indicators for {len(data_dict)} symbols...")
        print(f"  SMA periods: {args.sma_periods}")
        print(f"  RSI periods: {args.rsi_periods}")
        if args.ema_periods:
            print(f"  EMA periods: {args.ema_periods[:5]}... ({len(args.ema_periods)} total)")
        else:
            print(f"  EMA periods: 2-200, then 250-1000 by 50s (default)")
        print(f"  Candlestick patterns: {'No' if args.no_candlestick_patterns else 'Yes'}")
        print(f"  Streak indicators: {'No' if args.no_streak_indicators else 'Yes'}")
        print(f"  High/Low day tracking: {'No' if args.no_high_low_days else 'Yes'}")
        print()
    
    try:
        # Create output directory
        indicator_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize engine
        engine = IndicatorEngine(str(indicator_path))
        
        # Process all symbols
        engine.process_multiple_symbols(
            data_dict,
            sma_periods=args.sma_periods,
            rsi_periods=args.rsi_periods,
            ema_periods=args.ema_periods,
            include_candlestick_patterns=not args.no_candlestick_patterns,
            include_streak_indicators=not args.no_streak_indicators,
            include_high_low_days=not args.no_high_low_days,
            show_progress=not args.quiet
        )
        
        if not args.quiet:
            print(f"\n✓ Indicators computed successfully!")
            print(f"\nOutput files:")
            print(f"  HDF5 store: {indicator_path / 'indicators.h5'}")
            print(f"  Config JSON: {indicator_path / 'config.json'}")
            
            # Verify output
            available_symbols = engine.list_available_symbols()
            print(f"\n  {len(available_symbols)} symbols available in indicator store")
    
    except Exception as e:
        print(f"\n❌ ERROR computing indicators: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Success message
    if not args.quiet:
        print_section("Success!")
        print("\n✓ Indicator computation completed successfully!")
        print("\nNext steps:")
        print("  1. Start the web UI:   python app.py")
        print("  2. Or run full pipeline: python main.py --mode full")
        print("  3. Or run a scan:      python main.py --mode scan")
        print("\n" + "=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
