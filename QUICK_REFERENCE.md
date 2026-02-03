# Quick Reference Guide

## Module Overview

### data_loader.py
**Purpose**: Load OHLCV data from Parquet files

**Key Classes**:
- `DataLoader`: Main data loading interface

**Key Methods**:
```python
loader = DataLoader('/path/to/data')
df = loader.load_symbol('AAPL')
data_dict = loader.load_multiple_symbols(['AAPL', 'GOOGL'])
symbols = loader.list_available_symbols()
```

---

### indicator_engine.py
**Purpose**: Compute technical indicators (SMA, RSI)

**Key Classes**:
- `IndicatorEngine`: Indicator computation and storage

**Key Methods**:
```python
engine = IndicatorEngine('/path/to/indicators')
# Compute for single symbol
engine.process_and_store(symbol, data, sma_periods=[20, 50], rsi_periods=[14])
# Compute for multiple symbols
engine.process_multiple_symbols(data_dict, sma_periods=[20, 50, 200])
# Load computed indicators
indicators_df = engine.load_indicators('AAPL')
```

**Storage**:
- HDF5 format: `indicators.h5` (time series data)
- JSON format: `config.json` (metadata)

---

### strategy.py
**Purpose**: Define trading strategies

**Key Classes**:
- `StrategyRegistry`: Central strategy repository
- `StrategyConfig`: Strategy configuration dataclass

**Built-in Strategies**:
1. **Moving Average Crossover** (`ma_crossover`)
   ```python
   config = StrategyConfig(
       name='ma_crossover',
       params={'fast_period': 20, 'slow_period': 50}
   )
   ```

2. **RSI Mean-Reversion** (`rsi_meanrev`)
   ```python
   config = StrategyConfig(
       name='rsi_meanrev',
       params={'rsi_period': 14, 'oversold': 30, 'overbought': 70}
   )
   ```

**Usage**:
```python
registry = StrategyRegistry()
strategy_func = registry.get_strategy('ma_crossover')
signals = strategy_func(data, fast_period=20, slow_period=50)
```

---

### backtest_engine.py
**Purpose**: Run vectorized backtests with Numba acceleration

**Key Classes**:
- `BacktestEngine`: Backtesting orchestrator

**Key Methods**:
```python
engine = BacktestEngine('/path/to/backtests')
# Single backtest
result = engine.run_backtest(data, strategy_config)
# Multiple backtests
results_df = engine.run_multiple_backtests(data_dict, strategy_configs)
# Load results
summary = engine.load_summary()
detailed = engine.load_detailed_results('AAPL', 'ma_crossover')
```

**Output Metrics**:
- CAGR (Compound Annual Growth Rate)
- Sharpe Ratio
- Win Rate
- Maximum Drawdown
- Number of Trades
- Expectancy (average return per trade)

**Storage**:
- Zarr format: `results.zarr/` (detailed results, chunked arrays)
- Parquet format: `summary.parquet` (summary statistics)
- JSON format: `metadata.json` (configuration)

---

### scanner.py
**Purpose**: Find stocks matching live conditions

**Key Classes**:
- `Scanner`: Live scanning engine

**Key Methods**:
```python
scanner = Scanner(indicator_engine, backtest_engine)

# Scan for RSI conditions
oversold = scanner.scan_rsi_oversold(symbols, rsi_period=14, threshold=30)
overbought = scanner.scan_rsi_overbought(symbols, rsi_period=14, threshold=70)

# Scan for MA crossovers
bullish = scanner.scan_ma_crossover(symbols, fast_period=20, slow_period=50, direction='bullish')

# Get top performers
top = scanner.get_top_performers('rsi_meanrev', metric='sharpe_ratio', min_trades=10, top_n=20)

# Custom scan
def my_condition(df):
    return df['RSI_14'].iloc[-1] < 25 and df['Close'].iloc[-1] > df['SMA_50'].iloc[-1]
    
matches = scanner.custom_scan(symbols, my_condition, strategy_name='rsi_meanrev')
```

**Features**:
- Cross-references scan results with historical backtest performance
- Flexible condition matching
- Sorted and ranked results

---

### dash_ui.py
**Purpose**: Web-based UI for scanning and visualization

**Key Classes**:
- `DashUI`: Dash application wrapper

**Usage**:
```python
from dash_ui import create_app

ui = create_app(
    indicator_path='/path/to/indicators',
    backtest_path='/path/to/backtests'
)

# Run server
ui.run(host='0.0.0.0', port=8050, debug=False)
```

**Features**:
- Scanner configuration interface
- Results table with sorting/filtering
- Backtest summary statistics
- Lightweight for Colab environment

**Colab Integration**:
```python
# Use with ngrok for public URL
!pip install pyngrok
from pyngrok import ngrok
public_url = ngrok.connect(8050)
print(f"Dash app at: {public_url}")
```

---

### main.py
**Purpose**: Pipeline orchestration

**Key Classes**:
- `Pipeline`: Main orchestrator

**Usage**:
```python
from main import Pipeline

pipeline = Pipeline(
    data_path='/content/drive/MyDrive/stock_data',
    indicator_path='/content/drive/MyDrive/indicators',
    backtest_path='/content/drive/MyDrive/backtests'
)

# Full pipeline
pipeline.run_full_pipeline()

# Individual stages
pipeline.run_indicators_only(symbols=['AAPL', 'GOOGL'])
pipeline.run_backtests_only()
pipeline.run_scan('rsi_oversold', threshold=25)
```

**CLI Usage**:
```bash
# Full pipeline
python main.py --mode full

# Specific symbols
python main.py --mode full --symbols AAPL GOOGL MSFT

# Custom paths
python main.py --mode full \
    --data-path /custom/data \
    --indicator-path /custom/indicators \
    --backtest-path /custom/backtests
```

---

## Typical Workflow

### 1. Setup (Colab)
```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Clone and install
!git clone https://github.com/vimala1500/sandt_v1.0.git
%cd sandt_v1.0
!pip install -q -r requirements.txt
```

### 2. Prepare Data
Place Parquet files in `/content/drive/MyDrive/stock_data/`
- Format: `SYMBOL.parquet` (e.g., `AAPL.parquet`)
- Required columns: Date, Open, High, Low, Close, Volume

### 3. Run Pipeline
```python
from main import Pipeline

pipeline = Pipeline()
pipeline.run_full_pipeline()
```

### 4. Analyze Results
```python
# View backtest summary
summary = pipeline.backtest_engine.load_summary()
print(summary.nlargest(10, 'sharpe_ratio'))

# Run scans
oversold = pipeline.scanner.scan_rsi_oversold(
    pipeline.indicator_engine.list_available_symbols(),
    threshold=25
)
```

### 5. Launch UI
```python
from dash_ui import create_app
ui = create_app()
ui.run()
```

---

## Performance Considerations

### Numba Optimization
- Backtesting uses `@jit(nopython=True)` for speed
- 10-100x faster than pure Python loops
- Compiles on first run (slight delay)

### Storage Formats
- **Parquet**: Columnar, compressed, fast queries
- **HDF5**: Efficient for time series, compression
- **Zarr**: Chunked arrays, parallel access, cloud-friendly
- **JSON**: Human-readable metadata

### Caching
- DataLoader caches loaded data
- IndicatorEngine stores pre-computed indicators
- Avoid redundant computations

### Google Drive
- All paths support `/content/drive/MyDrive/` prefix
- Data persists across Colab sessions
- Optimize chunk sizes for Drive I/O

---

## Extending the System

### Adding Indicators
Edit `indicator_engine.py`:
```python
@staticmethod
def compute_macd(prices: pd.Series, fast=12, slow=26, signal=9):
    # Your implementation
    pass
```

### Adding Strategies
Edit `strategy.py`:
```python
@staticmethod
def my_strategy(data: pd.DataFrame, **params) -> pd.Series:
    signals = pd.Series(0, index=data.index)
    # Your logic
    return signals
```

Register in `__init__`:
```python
self.strategies['my_strategy'] = self.my_strategy
```

### Custom Scans
Use `scanner.custom_scan()`:
```python
def complex_condition(df):
    rsi = df['RSI_14'].iloc[-1]
    sma_20 = df['SMA_20'].iloc[-1]
    sma_50 = df['SMA_50'].iloc[-1]
    close = df['Close'].iloc[-1]
    
    return (rsi < 30 and 
            sma_20 > sma_50 and 
            close > sma_20)

results = scanner.custom_scan(symbols, complex_condition)
```

---

## Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Data Not Found
```python
# Check data path
loader = DataLoader('/content/drive/MyDrive/stock_data')
print(loader.list_available_symbols())
```

### Memory Issues
- Process symbols in batches
- Clear caches: `loader.clear_cache()`
- Use smaller date ranges

### Slow Backtests
- Numba compiles on first run (one-time delay)
- Reduce number of symbols/strategies
- Check for NaN values in indicators

---

## Best Practices

1. **Always validate data** before processing
2. **Use version control** for strategy parameters
3. **Document custom strategies** clearly
4. **Backup results** regularly to Drive
5. **Test on small datasets** first
6. **Monitor memory usage** in Colab
7. **Use descriptive strategy names**
8. **Keep indicator periods consistent**
9. **Validate backtest results** manually for key stocks
10. **Never trade real money** without thorough validation

---

## Resources

- **Repository**: https://github.com/vimala1500/sandt_v1.0
- **Notebook**: `notebooks/colab_quickstart.ipynb`
- **Documentation**: `README.md`

## Support

Open an issue on GitHub for:
- Bug reports
- Feature requests
- Questions
- Contributions
