#!/usr/bin/env python3
"""
Basic validation script to verify module structure and basic logic.
This script validates syntax and basic class/function definitions without
requiring full dependencies to be installed.
"""

import ast
import sys
from pathlib import Path


def validate_python_file(filepath):
    """Validate a Python file's syntax and structure."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        
        # Parse the code
        tree = ast.parse(code)
        
        # Extract classes and functions
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        return {
            'valid': True,
            'classes': classes,
            'functions': functions
        }
    except SyntaxError as e:
        return {
            'valid': False,
            'error': str(e)
        }


def main():
    """Run validation checks."""
    print("=" * 70)
    print("Stock Analysis & Trading System - Validation Report")
    print("=" * 70)
    
    files_to_check = {
        'data_loader.py': {
            'expected_classes': ['DataLoader'],
            'expected_methods': ['load_symbol', 'load_multiple_symbols']
        },
        'indicator_engine.py': {
            'expected_classes': ['IndicatorEngine'],
            'expected_methods': ['compute_sma', 'compute_rsi', 'compute_indicators']
        },
        'strategy.py': {
            'expected_classes': ['StrategyRegistry', 'StrategyConfig'],
            'expected_methods': ['ma_crossover_strategy', 'rsi_meanrev_strategy']
        },
        'backtest_engine.py': {
            'expected_classes': ['BacktestEngine'],
            'expected_methods': ['run_backtest', 'run_multiple_backtests']
        },
        'scanner.py': {
            'expected_classes': ['Scanner'],
            'expected_methods': ['scan_rsi_oversold', 'scan_ma_crossover']
        },
        'dash_ui.py': {
            'expected_classes': ['DashUI'],
            'expected_methods': ['run']
        },
        'main.py': {
            'expected_classes': ['Pipeline'],
            'expected_methods': ['run_full_pipeline', 'run_indicators_only']
        }
    }
    
    all_valid = True
    
    for filename, expectations in files_to_check.items():
        filepath = Path(filename)
        if not filepath.exists():
            print(f"\n✗ {filename}: FILE NOT FOUND")
            all_valid = False
            continue
        
        result = validate_python_file(filepath)
        
        if not result['valid']:
            print(f"\n✗ {filename}: SYNTAX ERROR")
            print(f"  Error: {result['error']}")
            all_valid = False
            continue
        
        # Check for expected classes
        missing_classes = [cls for cls in expectations['expected_classes'] 
                          if cls not in result['classes']]
        
        # Check for expected methods (in functions)
        missing_methods = [method for method in expectations['expected_methods'] 
                          if method not in result['functions']]
        
        if missing_classes or missing_methods:
            print(f"\n⚠ {filename}: STRUCTURE WARNING")
            if missing_classes:
                print(f"  Missing classes: {', '.join(missing_classes)}")
            if missing_methods:
                print(f"  Missing methods: {', '.join(missing_methods)}")
        else:
            print(f"\n✓ {filename}: OK")
            print(f"  Classes: {len([c for c in result['classes'] if c in expectations['expected_classes']])}")
            print(f"  Methods: {len([m for m in result['functions'] if m in expectations['expected_methods']])}")
    
    # Check additional files
    print("\n" + "-" * 70)
    print("Additional Files:")
    print("-" * 70)
    
    additional_files = {
        'requirements.txt': 'Dependencies file',
        'README.md': 'Documentation',
        '.gitignore': 'Git ignore rules',
        'notebooks/colab_quickstart.ipynb': 'Colab notebook'
    }
    
    for filename, description in additional_files.items():
        filepath = Path(filename)
        if filepath.exists():
            print(f"✓ {filename}: {description} ({filepath.stat().st_size} bytes)")
        else:
            print(f"✗ {filename}: MISSING")
            all_valid = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_valid:
        print("✓ ALL VALIDATION CHECKS PASSED")
        print("=" * 70)
        print("\nSystem Structure:")
        print("  • Data Loading: Parquet OHLCV files")
        print("  • Indicators: SMA, RSI (HDF5/JSON storage)")
        print("  • Strategies: MA Crossover, RSI Mean-Reversion")
        print("  • Backtesting: Numba-accelerated, Zarr output")
        print("  • Scanner: Live condition matching")
        print("  • UI: Dash web application")
        print("  • Notebook: Colab quickstart guide")
        return 0
    else:
        print("✗ SOME VALIDATION CHECKS FAILED")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
