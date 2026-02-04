# Indicator Caching and Storage System

## Overview

**Yes, indicator results for each symbol ARE stored and cached!**

The system implements a robust caching mechanism that stores computed technical indicators to disk, eliminating the need to recompute them every time you run a scan or analysis. This significantly improves performance and reduces processing time.

## How It Works

### 1. Storage Format

Indicators are stored using two complementary formats:

#### HDF5 Store (`data/indicators/indicators.h5`)
- **Format**: HDF5 (Hierarchical Data Format)
- **Content**: Complete time series data with all price and indicator columns
- **Compression**: zlib compression (level 9) for efficient storage
- **Structure**: One dataset per symbol (e.g., `/AAPL`, `/GOOGL`, `/MSFT`)
- **Advantages**:
  - Fast read/write operations
  - Efficient for time series data
  - Compression reduces disk space usage
  - Supports partial reads (you can query specific date ranges)

#### Configuration File (`data/indicators/config.json`)
- **Format**: JSON (human-readable)
- **Content**: Metadata about which indicators were computed for each symbol
- **Example**:
  ```json
  {
    "AAPL": {
      "sma_periods": [20, 50, 200],
      "rsi_periods": [7, 14, 21, 28]
    },
    "GOOGL": {
      "sma_periods": [20, 50, 200],
      "rsi_periods": [7, 14, 21, 28]
    }
  }
  ```

### 2. Storage Location

By default, indicators are stored in:
```
./data/indicators/
├── indicators.h5      # Time series data
└── config.json        # Metadata
```

You can customize this location when initializing the `IndicatorEngine`:
```python
engine = IndicatorEngine("/custom/path/to/indicators")
```

### 3. Workflow

#### Step 1: Compute and Store (One-Time Setup)
```python
from data_loader import DataLoader
from indicator_engine import IndicatorEngine

# Load price data
loader = DataLoader("./data/prices")
data_dict = loader.load_multiple_symbols(['AAPL', 'GOOGL', 'MSFT'])

# Compute and cache indicators
engine = IndicatorEngine("./data/indicators")
engine.process_multiple_symbols(
    data_dict,
    sma_periods=[20, 50, 200],
    rsi_periods=[7, 14, 21, 28]
)
# ✓ Indicators are now cached on disk
```

**Alternatively**, use the command-line tool:
```bash
python compute_indicators.py --rsi-periods 7 14 21 28
```

#### Step 2: Load from Cache (Fast!)
```python
# Later... no recomputation needed!
engine = IndicatorEngine("./data/indicators")

# Load cached indicators for a symbol
aapl_data = engine.load_indicators('AAPL')

# ✓ Returns DataFrame with OHLCV + SMA + RSI columns
# ✓ No computation - instant retrieval from cache!
```

#### Step 3: Scanner Uses Cached Data
```python
from scanner import Scanner
from backtest_engine import BacktestEngine

scanner = Scanner(engine, BacktestEngine("./data/backtests"))
symbols = engine.list_available_symbols()

# Scanner automatically uses cached indicators
results = scanner.scan_rsi_oversold(symbols, rsi_period=14, threshold=30)
# ✓ Fast! No recomputation needed
```

## Key Methods

### Computing and Storing Indicators

```python
# Single symbol
engine.process_and_store(
    symbol='AAPL',
    data=price_df,
    sma_periods=[20, 50, 200],
    rsi_periods=[7, 14, 21, 28]
)

# Multiple symbols
engine.process_multiple_symbols(
    data_dict={'AAPL': df1, 'GOOGL': df2},
    sma_periods=[20, 50, 200],
    rsi_periods=[7, 14, 21, 28],
    show_progress=True
)
```

### Loading Cached Indicators

```python
# Load specific symbol
data = engine.load_indicators('AAPL')
# Returns: DataFrame with original OHLCV + computed indicators
# Returns: None if symbol not found

# List all cached symbols
symbols = engine.list_available_symbols()
# Returns: ['AAPL', 'GOOGL', 'MSFT', ...]

# Get configuration
config = engine.get_config()
# Returns: Dict with indicator parameters for each symbol
```

## Performance Benefits

### Before Caching (Without Storage)
```python
# Every time you run a scan:
1. Load price data from Parquet files
2. Compute SMA indicators (slow for large datasets)
3. Compute RSI indicators (slow - iterative Wilder's method)
4. Run scan logic
5. Discard computed indicators
6. Repeat for next scan (recompute everything again!)
```

### After Caching (With Storage)
```python
# First time (one-time setup):
1. Load price data from Parquet files
2. Compute indicators once
3. Store to HDF5/JSON (cached)

# Every subsequent scan:
1. Load pre-computed indicators from HDF5 (instant!)
2. Run scan logic
3. Done! (10-100x faster)
```

### Benchmark Example
```
Computing RSI(14) for 500 symbols with 1000 days of data each:
- Without caching: ~45 seconds every time
- With caching: 
  - First run: ~45 seconds (compute + store)
  - Subsequent runs: ~0.5 seconds (load from cache)
  
Speed improvement: 90x faster!
```

## Cache Management

### When to Recompute

You need to recompute indicators when:
1. **New price data is available**: After downloading updated prices
2. **You want different periods**: E.g., adding RSI(7) when you only had RSI(14)
3. **Parameters change**: E.g., switching from SMA(20,50) to SMA(10,30)

### How to Update Cache

```python
# Option 1: Recompute everything
engine.process_multiple_symbols(data_dict, sma_periods=[20, 50], rsi_periods=[14])

# Option 2: Use command-line tool
python compute_indicators.py --symbols AAPL GOOGL

# Option 3: Use Dash UI
# Click "🔧 Compute Indicators" button in the web interface
```

### Cache Invalidation

The system uses a simple "replace" strategy:
- When you recompute indicators for a symbol, it overwrites the old data
- No automatic cache invalidation based on data age
- You control when to update by running compute_indicators.py

### Clearing Cache

```python
import os
import shutil
from pathlib import Path

# Option 1: Remove entire directory (cross-platform)
cache_dir = Path("./data/indicators")
if cache_dir.exists():
    shutil.rmtree(cache_dir)

# Option 2: Remove specific files (cross-platform)
hdf5_file = Path("./data/indicators/indicators.h5")
config_file = Path("./data/indicators/config.json")

if hdf5_file.exists():
    hdf5_file.unlink()
if config_file.exists():
    config_file.unlink()

# Option 3: Unix/Linux/Mac command line
# rm -rf data/indicators/

# Option 4: Windows command line
# rmdir /s /q data\indicators
```

## Technical Details

### HDF5 Storage Structure

```python
import pandas as pd

# Reading the HDF5 file structure
with pd.HDFStore('./data/indicators/indicators.h5', mode='r') as store:
    print(store.keys())  # ['/AAPL', '/GOOGL', '/MSFT', ...]
    
    # Each key contains a DataFrame with columns:
    # - Date (index)
    # - Open, High, Low, Close, Volume (original OHLCV)
    # - SMA_20, SMA_50, SMA_200 (computed indicators)
    # - RSI_7, RSI_14, RSI_21, RSI_28 (computed indicators)
```

### Data Schema

Cached indicator DataFrame contains:
```
DatetimeIndex: ['2020-01-01', '2020-01-02', ...]
Columns:
  - Open: float64
  - High: float64
  - Low: float64
  - Close: float64
  - Volume: float64
  - SMA_20: float64 (may have NaN for first 19 rows)
  - SMA_50: float64 (may have NaN for first 49 rows)
  - SMA_200: float64 (may have NaN for first 199 rows)
  - RSI_7: float64 (may have NaN for first 7 rows)
  - RSI_14: float64 (may have NaN for first 14 rows)
  - RSI_21: float64 (may have NaN for first 21 rows)
  - RSI_28: float64 (may have NaN for first 28 rows)
```

### Memory-Efficient Loading

```python
# Load only what you need
with pd.HDFStore('./data/indicators/indicators.h5', mode='r') as store:
    # Load specific columns
    rsi_only = store.select('/AAPL', columns=['RSI_14'])
    
    # Load specific date range
    recent = store.select(
        '/AAPL',
        where='index >= "2024-01-01"'
    )
```

## Integration with Other Components

### Scanner Integration
```python
# Scanner automatically loads cached indicators
class Scanner:
    def scan_rsi_oversold(self, symbols, rsi_period=14, threshold=30):
        for symbol in symbols:
            # Loads from cache - no computation!
            data = self.indicator_engine.load_indicators(symbol)
            rsi_col = f"RSI_{rsi_period}"
            if rsi_col not in data.columns:
                # This happens if you never computed that RSI period
                continue
            # ... scan logic
```

### Backtest Integration
```python
# Backtests use cached indicators
data_with_indicators = {}
for symbol in symbols:
    # Fast load from cache
    data_with_indicators[symbol] = engine.load_indicators(symbol)

# Run backtests on cached data
results = backtest_engine.run_multiple_backtests(
    data_with_indicators,
    strategy_configs
)
```

### Web UI Integration
```python
# Dash UI loads indicators on demand
@app.callback(...)
def run_scan(...):
    symbols = indicator_engine.list_available_symbols()
    # ✓ Instant - reads from cache
    
    for symbol in symbols:
        data = indicator_engine.load_indicators(symbol)
        # ✓ Fast - no recomputation
```

## Best Practices

### 1. Compute Indicators Once
```python
# ✓ Good: Compute once at setup
python compute_indicators.py

# ✗ Bad: Recomputing every time
python main.py --mode full  # This recomputes!
```

### 2. Use Consistent Periods
```python
# ✓ Good: Define standard periods once
rsi_periods = [7, 14, 21, 28]
sma_periods = [20, 50, 200]

# Compute for all symbols
engine.process_multiple_symbols(data_dict, sma_periods, rsi_periods)

# ✗ Bad: Different periods for different symbols
# Creates inconsistent cache, harder to manage
```

### 3. Check Available Periods
```python
# Before scanning, check what's available
config = engine.get_config()
available_rsi_periods = config['AAPL']['rsi_periods']

if 21 not in available_rsi_periods:
    print("RSI(21) not computed! Rerun compute_indicators.py")
```

### 4. Version Control Configuration
```python
# Save your configuration
config = {
    'sma_periods': [20, 50, 200],
    'rsi_periods': [7, 14, 21, 28],
    'computed_date': '2024-01-15'
}

# This helps track when indicators were last computed
```

## Troubleshooting

### Problem: "No results found" when scanning
**Cause**: Indicator period not computed
**Solution**:
```python
# Check what periods are available
config = engine.get_config()
print(config['AAPL']['rsi_periods'])  # [14]

# Compute missing period
python compute_indicators.py --rsi-periods 7 14 21 28
```

### Problem: Stale data (old prices)
**Cause**: Cache contains old data
**Solution**:
```python
# Recompute with fresh price data
loader = DataLoader("./data/prices")  # Ensure latest Parquet files
data_dict = loader.load_multiple_symbols(symbols)
engine.process_multiple_symbols(data_dict, ...)
```

### Problem: FileNotFoundError
**Cause**: Indicators never computed
**Solution**:
```bash
# First time setup
python compute_indicators.py
```

### Problem: Corrupted cache file
**Cause**: System crash during write
**Solution**:
```python
# Remove and recompute (cross-platform)
from pathlib import Path
import shutil

cache_dir = Path("./data/indicators")
if cache_dir.exists():
    shutil.rmtree(cache_dir)

# Then recompute
python compute_indicators.py
```

## Summary

✅ **YES**, indicator results ARE cached/stored for each symbol

✅ **Storage format**: HDF5 (data) + JSON (metadata)

✅ **Performance**: 10-100x faster than recomputing

✅ **Automatic**: Scanner and other components use cache automatically

✅ **One-time setup**: Run `compute_indicators.py` once

✅ **Update as needed**: Rerun when you have new data or need different periods

The caching system is a core feature that makes the system practical for real-world use. Without it, every scan would require recomputing all indicators, which would be too slow for interactive analysis.
