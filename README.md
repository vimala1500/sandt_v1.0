# Stock Analysis & Trading System (sandt_v1.0)

A complete, modular stock analysis and backtesting system with web UI. Features Numba-accelerated vectorized backtests, technical indicator computation, live scanning, and interactive Dash UI. Deployable locally, on Google Colab, or as a web service on Railway.

## System Workflow

```
📁 Price Data (Parquet)          ← Input: OHLCV data per symbol
         ↓
🔧 Compute Indicators            ← REQUIRED: Run compute_indicators.py
         ↓
💾 Indicators Store              ← Output: HDF5/JSON with SMA, RSI
         ↓
    ┌────┴────┐
    ↓         ↓
🎯 Scanner  📊 Backtests         ← Analysis & Strategy Testing
    ↓         ↓
🌐 Web UI (Dash)                 ← Interactive Dashboard
```

**Critical Step**: The indicator computation (`compute_indicators.py`) is REQUIRED before using any other features. See [First-Time Setup](#first-time-setup-required) below.

## Features

### Core Capabilities
- **Parquet OHLCV Processing**: Symbol-wise stock price data loading from local filesystem
- **Technical Indicators**: SMA and RSI computation with configurable periods (stored in HDF5/JSON)
- **Multiple Strategies**: 
  - Moving Average Crossover (arbitrary fast/slow pairs)
  - RSI Mean-Reversion (arbitrary periods/thresholds)
- **Numba-Accelerated Backtesting**: Vectorized backtests with comprehensive metrics
  - Win rate, CAGR, Sharpe ratio, max drawdown, expectancy, trade count
  - Results stored as Zarr chunked arrays for efficiency
- **Live Scanner**: Find stocks matching conditions (e.g., RSI < 20) with backtest cross-reference
- **Interactive Dash UI**: Web-based interface for scanning and results visualization
- **Flexible Deployment**: Run locally, on Google Colab, or deploy as a web service

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
├── app.py                     # Production web server entry point
├── main.py                    # Pipeline orchestration
├── data_loader.py             # Parquet OHLCV data loading
├── indicator_engine.py        # SMA/RSI computation, HDF5/JSON storage
├── strategy.py                # Strategy registry and parameterization
├── backtest_engine.py         # Numba-accelerated backtests, Zarr output
├── scanner.py                 # Live scanning with backtest cross-reference
├── dash_ui.py                 # Interactive Dash web UI
├── notebooks/
│   └── colab_quickstart.ipynb # End-to-end Colab demo
├── Procfile                   # Railway/Heroku deployment config
├── railway.json               # Railway-specific configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

### Railway Deployment (Web Service)

Deploy directly to Railway for a production web service:

1. **Fork this repository** to your GitHub account

2. **Connect to Railway**:
   - Go to [Railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

3. **Configure Environment** (optional):
   ```
   INDICATOR_PATH=./data/indicators
   BACKTEST_PATH=./data/backtests
   PORT=8050
   ```

4. **Railway will automatically**:
   - Install dependencies from `requirements.txt`
   - Start the web server using `Procfile`
   - Expose your Dash UI at the generated Railway URL

5. **⚠️ IMPORTANT: Compute Indicators on Railway**:
   
   After deployment, you MUST compute indicators before the UI will work:
   
   a. Open Railway project dashboard → Select your service
   
   b. Go to "Settings" tab → Click "Deploy" section → Open "Deploy Logs"
   
   c. Click "Shell" or "Terminal" button to open Railway shell
   
   d. In the Railway shell, run:
   ```bash
   python compute_indicators.py
   ```
   
   This will process the Parquet files in `data/prices/` and create indicators.

⚠️ **Important Notes about Railway Storage**:
- Railway uses **ephemeral filesystem** - data is lost on redeploy/restart
- Pre-computed indicators/backtests should be committed to Git (if small) or use external storage
- For persistent data storage, consider:
  - **Railway Volumes**: Persistent storage (paid feature)
  - **AWS S3 / Google Cloud Storage**: Store data files externally
  - **Remote Database**: Store processed data in PostgreSQL/MongoDB
  - **Pre-deployment**: Run backtests locally, commit results to Git

### Local Installation

```bash
git clone https://github.com/vimala1500/sandt_v1.0.git
cd sandt_v1.0
pip install -r requirements.txt
```

### Google Colab

```python
# In Colab notebook
!git clone https://github.com/vimala1500/sandt_v1.0.git
%cd sandt_v1.0
!pip install -r requirements.txt
```

## First-Time Setup (REQUIRED)

⚠️ **Important**: Before using the scanner or web UI, you MUST compute indicators from your price data.

### Prerequisites

Ensure you have price data in Parquet format in the `data/prices/` directory:
```
data/prices/
├── AAPL.parquet
├── GOOGL.parquet
├── MSFT.parquet
└── ...
```

Each Parquet file should contain OHLCV columns: Date/DATE, Open/OPEN, High/HIGH, Low/LOW, Close/CLOSE, Volume/VOLUME

### Step 1: Compute Indicators (First-Time & After Data Updates)

Run the indicator computation script to generate technical indicators from your price data:

```bash
# Basic usage - processes all symbols in data/prices/
python compute_indicators.py

# Process specific symbols only
python compute_indicators.py --symbols AAPL GOOGL MSFT

# Use custom paths (e.g., on Railway shell)
python compute_indicators.py --data-path ./data/prices --indicator-path ./data/indicators

# Customize indicator periods
python compute_indicators.py --sma-periods 10 20 50 100 200 --rsi-periods 7 14 21

# See all options
python compute_indicators.py --help
```

**What this does:**
- Reads Parquet files from `data/prices/`
- Computes SMA (Simple Moving Average) and RSI (Relative Strength Index) indicators
- Saves results to:
  - `data/indicators/indicators.h5` (HDF5 time series data)
  - `data/indicators/config.json` (metadata)

**When to run:**
- ✅ **First-time setup** - before using the system
- ✅ **After uploading new price data** - to include new symbols
- ✅ **After data updates** - when you add more historical data
- ✅ **To change indicator parameters** - different SMA/RSI periods

### Step 2: Verify Indicators

Verify indicators were created successfully:

```bash
# Check output files exist
ls -lh data/indicators/
# Should see: indicators.h5 and config.json

# List available symbols with indicators
python -c "from indicator_engine import IndicatorEngine; engine = IndicatorEngine('./data/indicators'); print(f'Symbols with indicators: {len(engine.list_available_symbols())}')"
```

### Step 3: Ready to Use!

Once indicators are computed, you can:
- 🚀 Start the web UI (see Quick Start below)
- 📊 Run backtests
- 🔍 Use the live scanner

---

## Quick Start

### 1. Web UI (Production/Railway)

For Railway deployment, the Dash UI starts automatically. For local development:

```bash
# Start the web server
python app.py

# Or use gunicorn for production-like environment
gunicorn app:server --bind 0.0.0.0:8050 --workers 2
```

Then open your browser to `http://localhost:8050`

**Environment Variables**:
- `PORT`: Server port (default: 8050)
- `HOST`: Server host (default: 0.0.0.0)
- `INDICATOR_PATH`: Path to indicators (default: ./data/indicators)
- `BACKTEST_PATH`: Path to backtests (default: ./data/backtests)
- `DEBUG`: Enable debug mode (default: False)

### 2. Using Colab Notebook

Open `notebooks/colab_quickstart.ipynb` in Google Colab and run all cells. The notebook demonstrates:
- Google Drive mounting
- Sample data generation
- Indicator computation
- Backtesting multiple strategies
- Live scanning
- UI launch

### 3. Using Python Scripts (Local)

```python
from main import Pipeline

# Initialize pipeline with local paths
pipeline = Pipeline(
    data_path='./data/stock_data',
    indicator_path='./data/indicators',
    backtest_path='./data/backtests'
)

# Run complete pipeline
pipeline.run_full_pipeline()
```

### 4. Command Line Interface

#### Indicator Computation (Recommended - Use First)

```bash
# Compute indicators from Parquet files (REQUIRED first step)
python compute_indicators.py

# With custom paths
python compute_indicators.py --data-path ./data/prices --indicator-path ./data/indicators

# Process specific symbols only
python compute_indicators.py --symbols AAPL GOOGL MSFT
```

#### Full Pipeline

```bash
# Full pipeline with default local paths
python main.py --mode full

# Indicators only (alternative to compute_indicators.py)
python main.py --mode indicators --symbols AAPL GOOGL MSFT

# Backtests only (requires indicators to be computed first)
python main.py --mode backtest

# Custom paths
python main.py --mode full \
    --data-path ./my_data \
    --indicator-path ./my_indicators \
    --backtest-path ./my_backtests
```

## Data Organization

### Input: Stock Data
- **Location**: `./data/prices/` (default) or custom path
- **Format**: Parquet files, one per symbol (e.g., `AAPL.parquet`)
- **Required Columns**: Date/DATE, Open/OPEN, High/HIGH, Low/LOW, Close/CLOSE, Volume/VOLUME
  - Column names are case-insensitive (automatically normalized)

### Output: Indicators
- **Location**: `./data/indicators/` (default) or custom path
- **Files**:
  - `indicators.h5`: HDF5 database with indicator time series (SMA, RSI)
  - `config.json`: Indicator configuration metadata
- **Generated by**: `python compute_indicators.py` (REQUIRED first step)

### Output: Backtests
- **Location**: `./data/backtests/` (default) or custom path
- **Files**:
  - `results.zarr/`: Zarr chunked arrays with detailed results
  - `summary.parquet`: Summary statistics for all backtests
  - `metadata.json`: Backtest configuration metadata

### Data Persistence for Railway

Railway uses **ephemeral storage** - files are deleted on restart. Options for persistence:

1. **Railway Volumes** (Recommended for production):
   ```bash
   # Mount a volume to /app/data in Railway dashboard
   # Update environment variables:
   INDICATOR_PATH=/app/data/indicators
   BACKTEST_PATH=/app/data/backtests
   ```

2. **External Storage** (S3, GCS):
   - Store data files in S3/GCS buckets
   - Modify loader classes to read from cloud storage
   - Use libraries like `boto3` (AWS) or `google-cloud-storage`

3. **Commit Pre-computed Results**:
   - Run backtests locally
   - Commit small result files to Git
   - UI displays pre-computed data

4. **Database Backend**:
   - Replace file storage with PostgreSQL/MongoDB
   - Railway provides managed databases

## Usage Examples

### Computing Indicators

**Recommended Method**: Use the standalone script (easiest):

```bash
# Compute indicators for all symbols
python compute_indicators.py

# See all options
python compute_indicators.py --help
```

**Alternative Method**: Use Python API directly:

```python
from data_loader import DataLoader
from indicator_engine import IndicatorEngine

# Load data (use local paths)
loader = DataLoader('./data/prices')
symbols = loader.list_available_symbols()
data_dict = loader.load_multiple_symbols(symbols)

# Compute indicators
engine = IndicatorEngine('./data/indicators')
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
backtest_engine = BacktestEngine('./data/backtests')

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
    indicator_path='./data/indicators',
    backtest_path='./data/backtests'
)

ui.run(host='0.0.0.0', port=8050, debug=False)
```

Or simply run:
```bash
python app.py
```

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
