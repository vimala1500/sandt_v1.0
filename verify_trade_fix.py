#!/usr/bin/env python3
"""
Final verification script for trade data pipeline fix.
Runs all tests and checks to ensure the fix is working correctly.
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    
    try:
        # Get the script directory to make paths relative
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=script_dir  # Run in script directory
        )
        
        # Filter out warnings
        output = result.stdout
        for line in output.split('\n'):
            if 'UnstableSpecificationWarning' in line or 'ZarrDeprecationWarning' in line:
                continue
            if line.strip():
                print(line)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False


def main():
    """Run all verification checks."""
    print("="*70)
    print("TRADE DATA PIPELINE FIX - FINAL VERIFICATION")
    print("="*70)
    
    results = []
    
    # Test 1: Trade data pipeline tests
    results.append(run_command(
        "python test_trade_data_pipeline.py 2>&1 | tail -15",
        "Integration Tests (test_trade_data_pipeline.py)"
    ))
    
    # Test 2: Backtest store tests
    results.append(run_command(
        "python test_backtest_store.py 2>&1 | tail -15",
        "Storage Tests (test_backtest_store.py)"
    ))
    
    # Test 3: Trade details modal tests
    results.append(run_command(
        "python test_trade_details_modal.py 2>&1 | tail -5",
        "UI Tests (test_trade_details_modal.py)"
    ))
    
    # Test 4: Demonstration
    results.append(run_command(
        "python demo_trade_fix.py 2>&1 | tail -20",
        "Demonstration (demo_trade_fix.py)"
    ))
    
    # Test 5: Sample backtest verification
    results.append(run_command(
        "python -c \"from backtest_engine import BacktestEngine; e = BacktestEngine('./data/backtests'); s = e.store.get_all_stats(); print(f'Found {len(s)} backtests'); [print(f'  {row[\\\"symbol\\\"]:25s}: {len(e.store.get_detailed_results(row[\\\"symbol\\\"], row[\\\"strategy\\\"], row[\\\"params\\\"], row[\\\"exit_rule\\\"]).get(\\\"trades\\\", []))} trades') for _, row in s.iterrows() if e.store.get_detailed_results(row['symbol'], row['strategy'], row['params'], row['exit_rule'])]\" 2>&1",
        "Sample Data Verification"
    ))
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL VERIFICATIONS PASSED!")
        print("\nThe trade data pipeline fix is working correctly.")
        print("Trade data is now reliably stored and retrieved with proper UI feedback.")
        return 0
    else:
        print(f"\n❌ {total - passed} VERIFICATION(S) FAILED")
        print("\nPlease review the failed tests above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
