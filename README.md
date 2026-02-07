# Stock Analysis & Trading System (sandt_v1.0)

A complete, modular stock analysis and backtesting system with web UI. Features Numba-accelerated vectorized backtests, technical indicator computation, live scanning, advanced batch backtesting portal, and interactive Dash UI. Deployable locally, on Google Colab, or as a web service on Railway.

> **📌 RSI Values Match TradingView**: Our RSI implementation uses Wilder's recursive averaging method, matching TradingView exactly. To verify: `python verify_rsi.py` or see [RSI_VERIFICATION.md](RSI_VERIFICATION.md)

## New: Three-Page Workflow

The application now features a clear three-page structure for an intuitive workflow:

### 📊 Page 1: Indicators
**Pre-compute technical indicators from price data**
- View computation status: last computation date and symbols processed
- Compute indicators with one click
- See available indicators at a glance
- Required first step before backtesting or scanning

![Indicators Page](https://github.com/user-attachments/assets/4def5659-f3e9-45f4-a3fc-4b89f29663b1)

### 📈 Page 2: Backtest
**Run strategy backtests on computed indicators**
- Data availability notification shows when indicators were last computed
- Select strategies and symbols for batch backtesting
- View comprehensive results with metrics
- Export results to CSV/XLSX

![Backtest Page](https://github.com/user-attachments/assets/75ff26ee-1fa2-4d79-bc43-c9bd0b43802c)

### 🔍 Page 3: Scanner
**Scan for opportunities using indicators and backtest data**
- Multiple scan types (RSI, MA crossover, candlestick patterns, etc.)
- Results include win rate and backtest stats
- Clean interface focused on signal generation

![Scanner Page](https://github.com/user-attachments/assets/752d2346-4757-4ed8-9f99-7bdfbe591e39)

## System Workflow

```
📁 Price Data (Parquet)          ← Input: OHLCV data per symbol
         ↓
🔧 Page 1: Indicators            ← Compute & store technical indicators
         ↓
💾 Indicators Store              ← Output: HDF5/JSON with SMA, RSI, EMA
         ↓
    ┌────┴────┐
    ↓         ↓
📊 Page 2:   🔍 Page 3:          ← Strategy Backtesting & Signal Scanning
  Backtest     Scanner
```

**Critical Step**: The indicator computation (Page 1) is REQUIRED before using any other features.

## Features

### Core Capabilities
- **🆕 Three-Page Workflow**: Clear separation of concerns for better UX
  - **Indicators Page**: Pre-compute indicators with status tracking
  - **Backtest Page**: Run strategies with data availability notification
  - **Scanner Page**: Find opportunities with integrated win rate stats
- **🆕 Improved Session Management**: Graceful initialization and error handling
  - No confusing error messages on first load
  - Auto-recovery from connection issues
  - Clear user feedback on session status
- **🆕 Indicator Metadata Tracking**: Track computation history
  - Last computation date stored in config
  - Symbol count and status monitoring
  - Available indicators display
- **Parquet OHLCV Processing**: Symbol-wise stock price data loading from local filesystem
- **Technical Indicators**: Comprehensive technical analysis library with 230+ indicators (stored in HDF5/JSON)
  - **EMAs**: 215 periods (2-200, then 250-1000 by 50s)
  - **Candlestick Patterns**: 12 patterns (hammer, doji, engulfing, harami, etc.)
  - **Momentum Indicators**: Consecutive higher/lower streaks
  - **High/Low Tracking**: Days since previous high/low
  - **Traditional Indicators**: SMA and RSI with configurable periods
- **Dynamic RSI Period Caching**: Scan with ANY RSI period - automatically computed and cached on-demand (See [DYNAMIC_RSI_CACHING.md](DYNAMIC_RSI_CACHING.md))
- **Universal Indicator Scanner**: Filter stocks by ANY indicator with flexible operators (>, <, ==, etc.)
  - Candlestick pattern scanning
  - Momentum streak detection
  - Custom EMA/SMA combinations
  - Days since high/low breakouts
- **Advanced Backtest Manager**: Professional batch backtesting interface (See [BACKTEST_MANAGER_GUIDE.md](BACKTEST_MANAGER_GUIDE.md))
  - Multi-select strategies and symbols
  - Batch execution with progress tracking
  - Grouped results (by strategy/symbol)
  - CSV/XLSX export
  - Group set management (save/load configurations)
- **Multiple Strategies**: 
  - Moving Average Crossover (arbitrary fast/slow pairs)
  - RSI Mean-Reversion (arbitrary periods/thresholds)
- **Numba-Accelerated Backtesting**: Vectorized backtests with comprehensive metrics
  - Win rate, CAGR, Sharpe ratio, max drawdown, expectancy, trade count
  - Results stored as Zarr chunked arrays for efficiency
- **Live Scanner**: Find stocks matching conditions (e.g., RSI < 20) with backtest cross-reference including win rates
- **Interactive Dash UI**: Web-based interface with three-page workflow
  - **Indicators Page**: One-click computation with status tracking and metadata display
  - **Backtest Page**: Batch strategy testing with data availability notifications
  - **Scanner Page**: 8 scan types with integrated backtest stats (win rate, Sharpe ratio, etc.)
  - Dynamic indicator dropdown populated from available data
  - Flexible comparison operators for custom filtering
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
├── app.py                       # Production web server entry point
├── main.py                      # Pipeline orchestration
├── data_loader.py               # Parquet OHLCV data loading
├── indicator_engine.py          # SMA/RSI computation, HDF5/JSON storage
├── strategy.py                  # Strategy registry and parameterization
├── backtest_engine.py           # Numba-accelerated backtests, Zarr output
├── backtest_store.py            # Centralized backtest storage & retrieval
├── backtest_manager_ui.py       # 🆕 Advanced batch backtesting portal
├── scanner.py                   # Live scanning with backtest cross-reference
├── dash_ui.py                   # Interactive Dash web UI
├── notebooks/
│   └── colab_quickstart.ipynb   # End-to-end Colab demo
├── Procfile                     # Railway/Heroku deployment config
├── railway.json                 # Railway-specific configuration
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── BACKTEST_MANAGER_GUIDE.md    # 🆕 Backtest Manager documentation
└── BACKTEST_STORAGE.md          # Backtest storage system docs
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
python -c "
from indicator_engine import IndicatorEngine
engine = IndicatorEngine('./data/indicators')
symbols = engine.list_available_symbols()
print(f'Symbols with indicators: {len(symbols)}')
print(f'Symbols: {symbols}')
"
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
- **Required Columns**: Date, Open, High, Low, Close, Volume
  - Column names are **case-insensitive** (e.g., `DATE`, `date`, or `Date` all work)
  - The data loader automatically normalizes column names to title case

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

### Using the Scanner with New Indicators

The scanner now supports filtering by ANY indicator with flexible comparison operators:

```python
from indicator_engine import IndicatorEngine
from scanner import Scanner
from backtest_engine import BacktestEngine

# Initialize engines
engine = IndicatorEngine('./data/indicators')
backtest_engine = BacktestEngine('./data/backtests')
scanner = Scanner(engine, backtest_engine)

# Get list of available symbols
symbols = engine.list_available_symbols()

# Example 1: Find stocks with specific candlestick patterns
hammer_stocks = scanner.scan_by_indicator(
    symbols, 
    indicator='hammer',
    operator='==',
    threshold=1
)

# Example 2: Find stocks with strong momentum (5+ consecutive higher highs)
momentum_stocks = scanner.scan_by_indicator(
    symbols,
    indicator='consec_higher_high',
    operator='>=',
    threshold=5
)

# Example 3: Find stocks at new highs (days_since_prev_high > 0 means setting a new high)
# Note: days_since_prev_high is non-zero only on days that set a new record high
breakout_stocks = scanner.scan_by_indicator(
    symbols,
    indicator='days_since_prev_high',
    operator='>',
    threshold=0
)

# Example 4: Find stocks with EMA crossover signals
ema_cross_stocks = scanner.scan_by_indicator(
    symbols,
    indicator='EMA_50',
    operator='>',
    threshold=100
)

# Example 5: Get all available indicators dynamically
available_indicators = scanner.get_available_indicators()
print(f"Available indicators: {available_indicators}")
```

### Web UI Scanner Features

The Dash UI now includes 8 scan types:

1. **RSI Oversold/Overbought**: Traditional RSI scanning with any period
2. **MA Crossover (Bullish/Bearish)**: Moving average crossover detection
3. **Candlestick Patterns** ⭐ NEW: Scan for 12 candlestick patterns
   - Hammer, Doji, Engulfing (Bull/Bear), Shooting Star, etc.
4. **Momentum Streaks** ⭐ NEW: Find stocks with consecutive higher/lower movements
5. **Custom Indicator Filter** ⭐ NEW: Filter by ANY indicator with custom operators
   - Supports all 230+ indicators
   - Flexible operators: >, <, >=, <=, ==, !=
   - Dynamic indicator dropdown
6. **Top Performers**: Ranked by backtest metrics

To use:
1. Start the UI: `python app.py`
2. Click "Compute Indicators" to process your price data
3. Select scan type from dropdown
4. Configure parameters (automatically shown based on scan type)
5. Click "Run Scan" to see results

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

## Technical Indicators

### RSI Implementation - Wilder's Smoothing Method

This system uses **Wilder's recursive averaging** for RSI calculation, which matches TradingView's classic RSI implementation exactly.

#### Formula

The RSI calculation uses the following approach:

1. **Calculate price changes**: `delta = close[i] - close[i-1]`
2. **Separate gains and losses**:
   - `gain = delta if delta > 0 else 0`
   - `loss = -delta if delta < 0 else 0`
3. **First average** (for period n): Simple average of first n gains/losses
4. **Subsequent averages** (Wilder's smoothing):
   ```
   avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i]) / period
   avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i]) / period
   ```
5. **Calculate RS and RSI**:
   ```
   RS = avg_gain / avg_loss
   RSI = 100 - (100 / (1 + RS))
   ```

#### Why Wilder's Method?

**Wilder's recursive averaging** is the **original and correct** method described by J. Welles Wilder Jr. in his 1978 book "New Concepts in Technical Trading Systems". This matches:
- ✅ TradingView's RSI indicator
- ✅ Most professional trading platforms
- ✅ The original definition by Welles Wilder

**Previous Implementation (EWM)**: Earlier versions used pandas' `ewm()` (exponential weighted moving average), which is **different** from Wilder's method and produces different values.

#### Verifying Against TradingView

**Quick Verification**: Run the automated verification tool:
```bash
python verify_rsi.py
```

This will:
- ✅ Test with Wilder's original example data (expected RSI: 70.46)
- ✅ Show you exactly how to compare with TradingView
- ✅ Verify edge cases (all gains, all losses, flat prices)
- ✅ Confirm our implementation matches TradingView exactly

**Manual Verification** with your own data:

1. **Export your price data**:
   ```python
   from data_loader import DataLoader
   loader = DataLoader('./data/prices')
   data = loader.load_symbol('AAPL')
   print(data['Close'].tail(20))  # Last 20 close prices
   ```

2. **In TradingView**:
   - Create a new chart for the same symbol
   - Add "Relative Strength Index" indicator
   - Set period to 14 (or your chosen period)
   - Compare the RSI values at the same time points

3. **Compare values**: The RSI values should match exactly (within rounding precision)

**For complete details**, see [RSI_VERIFICATION.md](RSI_VERIFICATION.md)

#### Testing RSI Implementation

Run comprehensive tests:
```bash
python test_rsi_wilder.py         # Compare Wilder's vs EWM methods
python test_detailed_rsi.py       # Step-by-step calculation details
python verify_rsi.py              # Quick verification (recommended)
```

#### Using RSI in Code

RSI is computed automatically when you run `compute_indicators.py`. To use it programmatically:

```python
from indicator_engine import IndicatorEngine

# Compute RSI for a price series
rsi = IndicatorEngine.compute_rsi_wilder(prices, period=14)

# Or use the alias (same result)
rsi = IndicatorEngine.compute_rsi(prices, period=14)
```

Both methods are equivalent - `compute_rsi()` now calls `compute_rsi_wilder()` internally.

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
- **Indicator Caching**: Pre-computed indicators stored to HDF5 for 100x faster loading
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

## Documentation

Additional documentation files:
- **[BACKTEST_MANAGER_GUIDE.md](BACKTEST_MANAGER_GUIDE.md)** - 🆕 Complete guide to the Backtest Manager Portal
- **[BACKTEST_STORAGE.md](BACKTEST_STORAGE.md)** - Backtest storage and retrieval system
- **[INDICATOR_CACHING.md](INDICATOR_CACHING.md)** - Complete guide to indicator caching/storage system
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference for all modules and methods
- **[RSI_VERIFICATION.md](RSI_VERIFICATION.md)** - RSI calculation verification and TradingView comparison
- **[docs/UI_ENHANCEMENTS.md](docs/UI_ENHANCEMENTS.md)** - 🆕 UI/UX enhancements guide with modern design details
- **[docs/SESSION_TROUBLESHOOTING.md](docs/SESSION_TROUBLESHOOTING.md)** - 🆕 Session management troubleshooting guide
- **[docs/DESIGN_DOC.md](docs/DESIGN_DOC.md)** - 🆕 Complete design system documentation with before/after comparisons

Run `python demo_caching.py` to see the caching system in action with live performance metrics.

## Acknowledgments

Built with:
- Pandas & NumPy for data manipulation
- Numba for performance optimization
- Dash & Plotly for visualization
- PyTables, Zarr, PyArrow for efficient storage

---

**Note**: This system is designed for educational and research purposes. Always validate strategies thoroughly before live trading.
