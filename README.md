# Stock Analysis & Trading System (sandt_v1.0)

A complete, modular stock analysis and backtesting system optimized for Google Colab + Google Drive workflow. Features Numba-accelerated vectorized backtests, technical indicator computation, live scanning, and interactive Dash UI.

## Features

### Core Capabilities
- **Parquet OHLCV Processing**: Symbol-wise stock price data loading from Google Drive
- **Technical Indicators**: SMA and RSI computation with configurable periods (stored in HDF5/JSON)
- **Multiple Strategies**: 
  - Moving Average Crossover (arbitrary fast/slow pairs)
  - RSI Mean-Reversion (arbitrary periods/thresholds)
- **Numba-Accelerated Backtesting**: Vectorized backtests with comprehensive metrics
  - Win rate, CAGR, Sharpe ratio, max drawdown, expectancy, trade count
  - Results stored as Zarr chunked arrays for efficiency
- **Live Scanner**: Find stocks matching conditions (e.g., RSI < 20) with backtest cross-reference
- **Interactive Dash UI**: Web-based interface for scanning and results visualization
- **Colab-Optimized**: Fully integrated with Google Drive for data persistence

### Performance Metrics
All backtests output standardized metrics per [strategy, symbol] pair:
- Total Return & CAGR
- Sharpe Ratio
- Win Rate
- Maximum Drawdown
- Trade Count & Expectancy

## Project Structure

```
sandt_v1.0/
├── main.py                   # Pipeline orchestration
├── data_loader.py            # Parquet OHLCV data loading
├── indicator_engine.py       # SMA/RSI computation, HDF5/JSON storage
├── strategy.py               # Strategy registry and parameterization
├── backtest_engine.py        # Numba-accelerated backtests, Zarr output
├── scanner.py                # Live scanning with backtest cross-reference
├── dash_ui.py                # Interactive Dash web UI
├── notebooks/
│   └── colab_quickstart.ipynb  # End-to-end Colab demo
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Installation

### Google Colab (Recommended)

```python
# In Colab notebook
!git clone https://github.com/vimala1500/sandt_v1.0.git
%cd sandt_v1.0
!pip install -r requirements.txt
```

### Local Installation

```bash
git clone https://github.com/vimala1500/sandt_v1.0.git
cd sandt_v1.0
pip install -r requirements.txt
```

## Quick Start

### 1. Using Colab Notebook (Easiest)

Open `notebooks/colab_quickstart.ipynb` in Google Colab and run all cells. The notebook demonstrates:
- Google Drive mounting
- Sample data generation
- Indicator computation
- Backtesting multiple strategies
- Live scanning
- UI launch

### 2. Using Python Scripts

```python
from main import Pipeline

# Initialize pipeline
pipeline = Pipeline(
    data_path='/content/drive/MyDrive/stock_data',
    indicator_path='/content/drive/MyDrive/indicators',
    backtest_path='/content/drive/MyDrive/backtests'
)

# Run complete pipeline
pipeline.run_full_pipeline()
```

### 3. Command Line Interface

```bash
# Full pipeline
python main.py --mode full

# Indicators only
python main.py --mode indicators --symbols AAPL GOOGL MSFT

# Backtests only
python main.py --mode backtest

# Custom paths
python main.py --mode full \
    --data-path /path/to/data \
    --indicator-path /path/to/indicators \
    --backtest-path /path/to/backtests
```

## Usage Examples

### Computing Indicators

```python
from data_loader import DataLoader
from indicator_engine import IndicatorEngine

# Load data
loader = DataLoader('/content/drive/MyDrive/stock_data')
symbols = ['AAPL', 'GOOGL', 'MSFT']
data_dict = loader.load_multiple_symbols(symbols)

# Compute indicators
engine = IndicatorEngine('/content/drive/MyDrive/indicators')
engine.process_multiple_symbols(
    data_dict,
    sma_periods=[20, 50, 200],
    rsi_periods=[14],
    show_progress=True
)
```

### Running Backtests

```python
from backtest_engine import BacktestEngine
from strategy import DEFAULT_STRATEGIES

# Initialize
backtest_engine = BacktestEngine('/content/drive/MyDrive/backtests')

# Run backtests
strategy_configs = list(DEFAULT_STRATEGIES.values())
results = backtest_engine.run_multiple_backtests(
    data_with_indicators,
    strategy_configs,
    show_progress=True
)

# View results
print(results.nlargest(10, 'sharpe_ratio'))
```

### Scanning for Opportunities

```python
from scanner import Scanner

scanner = Scanner(indicator_engine, backtest_engine)

# Find oversold stocks
oversold = scanner.scan_rsi_oversold(
    symbols,
    rsi_period=14,
    threshold=30
)

# Find MA crossovers
crossovers = scanner.scan_ma_crossover(
    symbols,
    fast_period=20,
    slow_period=50,
    direction='bullish'
)

# Get top performers
top = scanner.get_top_performers(
    'rsi_meanrev',
    metric='sharpe_ratio',
    min_trades=10,
    top_n=20
)
```

### Launching Dash UI

```python
from dash_ui import create_app

ui = create_app(
    indicator_path='/content/drive/MyDrive/indicators',
    backtest_path='/content/drive/MyDrive/backtests'
)

ui.run(host='0.0.0.0', port=8050, debug=False)
```

## Data Organization

### Input: Stock Data
- **Location**: `/content/drive/MyDrive/stock_data/`
- **Format**: Parquet files, one per symbol (e.g., `AAPL.parquet`)
- **Required Columns**: Date, Open, High, Low, Close, Volume

### Output: Indicators
- **Location**: `/content/drive/MyDrive/indicators/`
- **Files**:
  - `indicators.h5`: HDF5 database with indicator time series
  - `config.json`: Indicator configuration metadata

### Output: Backtests
- **Location**: `/content/drive/MyDrive/backtests/`
- **Files**:
  - `results.zarr/`: Zarr chunked arrays with detailed results
  - `summary.parquet`: Summary statistics for all backtests
  - `metadata.json`: Backtest configuration metadata

## Strategies

### Built-in Strategies

1. **Moving Average Crossover** (`ma_crossover`)
   - Parameters: `fast_period`, `slow_period`
   - Signal: Long when fast > slow, short when fast < slow
   - Defaults: 20/50, 50/200 (Golden Cross)

2. **RSI Mean-Reversion** (`rsi_meanrev`)
   - Parameters: `rsi_period`, `oversold`, `overbought`
   - Signal: Long when RSI < oversold, short when RSI > overbought
   - Defaults: RSI(14) with 30/70 or 20/80 thresholds

### Adding Custom Strategies

Extend the `StrategyRegistry` class in `strategy.py`:

```python
@staticmethod
def my_strategy(data: pd.DataFrame, **params) -> pd.Series:
    """
    Custom strategy implementation.
    
    Returns:
        Series of signals (1=long, -1=short, 0=neutral)
    """
    # Your logic here
    signals = pd.Series(0, index=data.index)
    # ... compute signals ...
    return signals
```

## Architecture & Design

### Modular Components
- **DataLoader**: Clean abstraction for Parquet I/O
- **IndicatorEngine**: Pluggable indicator computation with efficient storage
- **StrategyRegistry**: Centralized strategy definitions
- **BacktestEngine**: Vectorized backtesting with Numba acceleration
- **Scanner**: Live condition matching with historical performance
- **DashUI**: Interactive visualization layer

### Storage Optimization
- **HDF5**: Compressed time series for indicators
- **Zarr**: Chunked arrays for large backtest results
- **Parquet**: Efficient columnar storage for summaries
- **JSON**: Human-readable metadata

### Performance Features
- Numba JIT compilation for backtesting loops
- Vectorized operations with NumPy/Pandas
- Lazy loading and caching
- Compressed storage formats

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy >= 1.24.0
- numba >= 0.57.0
- pyarrow >= 12.0.0
- tables >= 3.8.0
- zarr >= 2.16.0
- dash >= 2.14.0
- plotly >= 5.17.0

See `requirements.txt` for complete list.

## Development

### Running Tests
```bash
# Coming soon: unit tests for all modules
pytest tests/
```

### Code Style
- PEP 8 compliant
- Type hints for key interfaces
- Comprehensive docstrings

## Limitations & Future Enhancements

### Current Limitations
- Basic Dash UI (not production-ready)
- Limited to daily OHLCV data
- Two built-in strategies (extensible)

### Planned Enhancements
- [ ] More technical indicators (MACD, Bollinger Bands, etc.)
- [ ] Additional strategies (momentum, volatility-based)
- [ ] Portfolio-level backtesting
- [ ] Risk management features
- [ ] Real-time data integration
- [ ] Enhanced UI with charting
- [ ] Parallel processing for large datasets

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

Built with:
- Pandas & NumPy for data manipulation
- Numba for performance optimization
- Dash & Plotly for visualization
- PyTables, Zarr, PyArrow for efficient storage

---

**Note**: This system is designed for educational and research purposes. Always validate strategies thoroughly before live trading.
