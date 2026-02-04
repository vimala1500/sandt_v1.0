# Change Log

## Version 1.1.0 - RSI Wilder's Averaging Update (2026-02-04)

### RSI Indicator Implementation Update

**Breaking Change**: RSI calculation now uses Wilder's recursive averaging method instead of pandas EWM.

**What Changed**:
- RSI now uses Wilder's recursive averaging: `avg[n] = (avg[n-1] * (period-1) + value[n]) / period`
- Previous implementation used pandas `ewm()` which produces different values
- New implementation matches TradingView's classic RSI exactly

**Impact**:
- ✅ RSI values now match TradingView and other professional platforms
- ⚠️ RSI values will be different from previous versions
- ✅ All modules automatically use new calculation
- ✅ Backward compatible API (`compute_rsi()` still works)

**Files Modified**:
- `indicator_engine.py`: Added `compute_rsi_wilder()` method, updated `compute_rsi()` to call it
- `README.md`: Added technical documentation section explaining RSI calculation
- `test_rsi_wilder.py`: New validation test comparing old vs new method

**Verification**:
```bash
python test_rsi_wilder.py  # Validates against TradingView values
```

**Why This Matters**:
- Professional traders expect RSI to match TradingView/MetaTrader/Bloomberg
- Backtests now reflect real-world trading indicators
- Strategy signals will match what traders see on their platforms

---

# Railway Deployment Refactoring - Change Log

## Overview
This refactoring transforms the Stock Analysis & Trading System from a Google Colab-focused project into a Railway-deployable web service while maintaining full backward compatibility.

## Files Added (6)

### 1. `app.py`
**Purpose**: Production web server entry point
- Exports Flask server for gunicorn
- Environment variable configuration
- Compatible with Railway's PORT binding

### 2. `Procfile`
**Purpose**: Railway/Heroku deployment configuration
- Starts gunicorn with 2 workers
- 120-second timeout for long-running operations
- Binds to Railway's dynamic PORT

### 3. `railway.json`
**Purpose**: Railway-specific deployment settings
- Specifies Nixpacks builder
- Defines start command
- Restart policy configuration

### 4. `test_local.py`
**Purpose**: Local testing script with sample data
- Generates synthetic OHLCV data
- Tests all pipeline components
- Validates local filesystem compatibility

### 5. `RAILWAY_DEPLOYMENT.md`
**Purpose**: Comprehensive deployment guide
- Step-by-step Railway deployment
- Data persistence strategies (4 options)
- Troubleshooting and cost estimation
- Migration guide from Colab

### 6. `.env.example`
**Purpose**: Environment variable template
- Documents all configuration options
- Reference for Railway dashboard setup
- Local development guide

## Files Modified (8)

### 1. `main.py`
**Changes**:
- Default paths: `/content/drive/MyDrive/*` → `./data/*`
- CLI argument defaults updated
- Maintains path customization via arguments

### 2. `dash_ui.py`
**Changes**:
- Default paths updated to local
- Fixed Dash API: `run_server()` → `run()`
- Compatible with Dash 2.14+

### 3. `data_loader.py`
**Changes**:
- Default path: `/content/drive/MyDrive/stock_data` → `./data/stock_data`
- No functional changes, just defaults

### 4. `indicator_engine.py`
**Changes**:
- Default path: `/content/drive/MyDrive/indicators` → `./data/indicators`
- No functional changes, just defaults

### 5. `backtest_engine.py`
**Changes**:
- Default path: `/content/drive/MyDrive/backtests` → `./data/backtests`
- Fixed Zarr storage compatibility (numpy array handling)
- Improved error messages with actionable guidance
- Graceful fallback if Zarr storage fails

### 6. `requirements.txt`
**Additions**:
- `gunicorn>=21.2.0` - Production web server
- `numcodecs>=0.11.0` - Compression support for Zarr

### 7. `README.md`
**Major Updates**:
- New Railway deployment section (step-by-step)
- Environment variable documentation
- Data persistence strategies section
- Updated all code examples (local paths)
- Quick start guide for Railway/local/Colab
- Storage limitations and solutions

### 8. `.gitignore`
**Additions**:
- `indicators/` - Local indicator storage
- `backtests/` - Local backtest results
- `stock_data/` - Local stock data
- `.env` - Environment configuration
- `.env.local` - Local overrides

## Backward Compatibility

### ✅ Still Works
- Local execution unchanged
- Google Colab compatible (override paths)
- CLI arguments for custom paths
- All existing features preserved
- Notebook workflows unchanged

### 🆕 New Capabilities
- Railway deployment ready
- Production web server
- Environment variable configuration
- Local development friendly
- Persistent storage options

## Testing Summary

### Automated Tests
- ✅ Data loading from local filesystem
- ✅ Indicator computation (SMA/RSI)
- ✅ Backtesting with metrics
- ✅ Zarr storage (with fallback)
- ✅ Parquet summary export

### Manual Tests
- ✅ Dash UI loads and displays
- ✅ Scanner configuration works
- ✅ Backtest summary displays
- ✅ Environment variables work
- ✅ Gunicorn production server

### Security
- ✅ CodeQL scan: 0 vulnerabilities
- ✅ Code review feedback addressed
- ✅ No hardcoded credentials
- ✅ Proper error handling

## Migration Impact

### For Current Users
**No changes required** for local/Colab usage. The system works exactly as before.

**Optional**: Can now deploy to Railway for web access.

### For New Users
**Recommended**: Start with Railway deployment for easiest setup.

**Alternative**: Still can use locally or in Colab.

## Environment Variables

| Variable | Default | Railway | Description |
|----------|---------|---------|-------------|
| PORT | 8050 | Auto-set | Server port |
| HOST | 0.0.0.0 | Auto-set | Server host |
| INDICATOR_PATH | ./data/indicators | Customize | Indicator storage |
| BACKTEST_PATH | ./data/backtests | Customize | Backtest storage |
| DEBUG | false | false | Debug mode |

## Data Persistence Options

1. **Railway Volumes**: Persistent storage ($5/mo per GB)
2. **Cloud Storage**: AWS S3, Google Cloud Storage
3. **Database**: PostgreSQL, MongoDB via Railway
4. **Pre-computed**: Commit small result files to Git

## Deployment Steps

### Railway (5 minutes)
1. Fork repository
2. Connect to Railway
3. Deploy from GitHub
4. Access at generated URL

### Local (3 minutes)
```bash
git clone <repo>
pip install -r requirements.txt
python test_local.py
python app.py
```

## Support

- **Issues**: GitHub Issues
- **Documentation**: README.md, RAILWAY_DEPLOYMENT.md
- **Railway Help**: docs.railway.app

## Future Enhancements

Potential future improvements:
- Real-time data feeds
- WebSocket for live updates
- Database migration scripts
- Docker configuration
- API endpoints for programmatic access

---

**Version**: 1.0.0 (Railway Ready)  
**Date**: 2026-02-03  
**Status**: Production Ready ✅
