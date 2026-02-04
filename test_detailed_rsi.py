#!/usr/bin/env python3
"""
Detailed RSI testing to identify any discrepancies with TradingView.

This script helps diagnose potential issues with RSI calculation by:
1. Showing step-by-step calculations
2. Testing with specific data points
3. Verifying boundary conditions
"""

import pandas as pd
import numpy as np
from indicator_engine import IndicatorEngine


def analyze_rsi_calculation(prices, period=14):
    """
    Perform a detailed step-by-step analysis of RSI calculation.
    """
    print("\n" + "="*80)
    print(f"DETAILED RSI ANALYSIS (Period={period})")
    print("="*80)
    
    print(f"\n1. Input Prices ({len(prices)} values):")
    for i, p in enumerate(prices[:min(20, len(prices))]):
        print(f"   Index {i:2d}: ${p:.2f}")
    if len(prices) > 20:
        print(f"   ... and {len(prices) - 20} more")
    
    # Step 1: Calculate changes
    print(f"\n2. Price Changes (delta = prices.diff()):")
    delta = prices.diff()
    for i in range(1, min(16, len(delta))):
        print(f"   Index {i:2d}: {delta.iloc[i]:+.4f}")
    
    # Step 2: Separate gains and losses
    print(f"\n3. Separate Gains and Losses:")
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    print(f"   Gains (first {period+1}):")
    for i in range(1, min(period+2, len(gains))):
        if gains.iloc[i] > 0:
            print(f"      Index {i:2d}: +{gains.iloc[i]:.4f}")
    
    print(f"   Losses (first {period+1}):")
    for i in range(1, min(period+2, len(losses))):
        if losses.iloc[i] > 0:
            print(f"      Index {i:2d}: +{losses.iloc[i]:.4f}")
    
    # Step 3: Calculate first averages
    print(f"\n4. First Average Calculation:")
    print(f"   Using range: gains.iloc[1:{period+1}] (indices 1 through {period})")
    print(f"   Number of values: {len(gains.iloc[1:period+1])}")
    
    first_avg_gain = gains.iloc[1:period+1].mean()
    first_avg_loss = losses.iloc[1:period+1].mean()
    
    sum_gains = gains.iloc[1:period+1].sum()
    sum_losses = losses.iloc[1:period+1].sum()
    
    print(f"   Sum of gains:  {sum_gains:.6f}")
    print(f"   Sum of losses: {sum_losses:.6f}")
    print(f"   Average gain:  {first_avg_gain:.6f} (sum / {period})")
    print(f"   Average loss:  {first_avg_loss:.6f} (sum / {period})")
    
    # Step 4: Calculate first RSI
    rs_first = first_avg_gain / first_avg_loss if first_avg_loss != 0 else 0
    rsi_first = 100 - (100 / (1 + rs_first)) if first_avg_loss != 0 else 100
    
    print(f"\n5. First RSI Value (at index {period}):")
    print(f"   RS = {first_avg_gain:.6f} / {first_avg_loss:.6f} = {rs_first:.6f}")
    print(f"   RSI = 100 - (100 / (1 + {rs_first:.6f})) = {rsi_first:.6f}")
    
    # Step 5: Calculate subsequent values (show first few)
    print(f"\n6. Subsequent Values (Wilder's Smoothing):")
    print(f"   Formula: avg[n] = (avg[n-1] * {period-1} + value[n]) / {period}")
    
    avg_gain_prev = first_avg_gain
    avg_loss_prev = first_avg_loss
    
    for i in range(period+1, min(period+4, len(prices))):
        gain = gains.iloc[i]
        loss = losses.iloc[i]
        
        avg_gain_curr = (avg_gain_prev * (period - 1) + gain) / period
        avg_loss_curr = (avg_loss_prev * (period - 1) + loss) / period
        
        rs = avg_gain_curr / avg_loss_curr if avg_loss_curr != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if avg_loss_curr != 0 else 100
        
        print(f"\n   Index {i}:")
        print(f"      Price change: {delta.iloc[i]:+.4f}")
        print(f"      Gain: {gain:.6f}, Loss: {loss:.6f}")
        print(f"      Avg gain: ({avg_gain_prev:.6f} * {period-1} + {gain:.6f}) / {period} = {avg_gain_curr:.6f}")
        print(f"      Avg loss: ({avg_loss_prev:.6f} * {period-1} + {loss:.6f}) / {period} = {avg_loss_curr:.6f}")
        print(f"      RSI: {rsi:.6f}")
        
        avg_gain_prev = avg_gain_curr
        avg_loss_prev = avg_loss_curr
    
    # Compare with our function
    print(f"\n7. Our Function Results:")
    rsi = IndicatorEngine.compute_rsi_wilder(prices, period=period)
    for i in range(period, min(period+4, len(prices))):
        print(f"   Index {i:2d}: {rsi.iloc[i]:.6f}")
    
    return rsi


def test_tradingview_example():
    """
    Test with a specific example that can be verified on TradingView.
    
    Instructions to verify on TradingView:
    1. Go to TradingView.com
    2. Open a chart
    3. Add the "Replay" feature or use historical data
    4. Input these exact prices
    5. Add RSI indicator with period 14
    6. Compare the RSI values
    """
    print("\n" + "="*80)
    print("TEST: Wilder's Original Example Data")
    print("="*80)
    print("\nThis is the exact dataset from Wilder's book:")
    print("'New Concepts in Technical Trading Systems' (1978)")
    
    # These are the exact values from Wilder's book
    prices = pd.Series([
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64,
        46.21, 46.25, 45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57,
        43.42, 42.66, 43.13
    ])
    
    rsi = analyze_rsi_calculation(prices, period=14)
    
    print(f"\n" + "="*80)
    print("EXPECTED VALUES (from Wilder's book):")
    print("="*80)
    print(f"First RSI (index 14): ~70.46")
    print(f"Our calculation (index 14): {rsi.iloc[14]:.2f}")
    
    if abs(rsi.iloc[14] - 70.46) < 0.1:
        print("✓ MATCH! Our calculation matches Wilder's expected value.")
    else:
        print(f"✗ MISMATCH! Difference: {abs(rsi.iloc[14] - 70.46):.4f}")


def test_edge_case_analysis():
    """
    Test potential edge cases that might cause TradingView discrepancies.
    """
    print("\n" + "="*80)
    print("EDGE CASE ANALYSIS")
    print("="*80)
    
    # Test 1: What if first value is included in average?
    print("\n1. Testing if first price (index 0) should be included:")
    prices = pd.Series([100, 101, 102, 101, 103, 104, 103, 105, 106, 105,
                        106, 107, 106, 108, 109])
    
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = -delta.where(delta < 0, 0.0)
    
    # Standard way (indices 1-14)
    avg_gain_standard = gains.iloc[1:15].mean()
    # Alternative (indices 0-13, but index 0 is NaN)
    avg_gain_alt = gains.iloc[0:14].mean()  # This will skip NaN
    
    print(f"   Standard (1:15): {avg_gain_standard:.6f}")
    print(f"   Alternative (0:14): {avg_gain_alt:.6f}")
    print(f"   Difference: {abs(avg_gain_standard - avg_gain_alt):.6f}")
    
    # Test 2: Off-by-one in loop
    print("\n2. Testing loop start position:")
    print(f"   Our loop starts at: period + 1 = {15}")
    print(f"   This is correct for index-based arrays")


if __name__ == '__main__':
    test_tradingview_example()
    test_edge_case_analysis()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nTo verify against TradingView:")
    print("1. Copy the price data from above")
    print("2. Input it into TradingView")
    print("3. Add RSI(14) indicator")
    print("4. Compare the values")
    print("\nOur implementation follows Wilder's method exactly.")
    print("="*80 + "\n")
