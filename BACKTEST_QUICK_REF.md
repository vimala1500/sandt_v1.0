# Backtest Storage System - Quick Reference

## Quick Start

### 1. Run a Backtest and Store Results

```python
from backtest_engine import BacktestEngine
from indicator_engine import IndicatorEngine

# Initialize engines
indicator_engine = IndicatorEngine("./data/indicators")
backtest_engine = BacktestEngine("./data/backtests")

# Load data with indicators
data = indicator_engine.load_indicators("AAPL")

# Run and store backtest (automatically saved to centralized store)
result = backtest_engine.run_single_backtest(
    symbol="AAPL",
    strategy_name="rsi_meanrev",
    params={"rsi_period": 14, "oversold": 30, "overbought": 70}
)

print(f"Win Rate: {result['metrics']['win_rate']:.1%}")
print(f"Trades: {result['metrics']['num_trades']}")
print(f"Sharpe: {result['metrics']['sharpe_ratio']:.2f}")
```

### 2. Retrieve Backtest Statistics

```python
# Get stats for specific backtest
stats = backtest_engine.get_backtest_stats(
    symbol="AAPL",
    strategy="rsi_meanrev",
    params={"rsi_period": 14, "oversold": 30, "overbought": 70}
)

if stats:
    print(f"Win Rate: {stats['win_rate']:.1%}")
    print(f"Num Trades: {stats['num_trades']}")
    print(f"CAGR: {stats['cagr']:.1%}")
```

### 3. Query All Backtests

```python
# Get all stored backtests
all_backtests = backtest_engine.store.get_all_stats()
print(all_backtests[['symbol', 'strategy', 'win_rate', 'sharpe_ratio', 'cagr']])

# Filter by symbol
aapl_backtests = backtest_engine.store.get_stats(symbol="AAPL")

# Filter by strategy
rsi_backtests = backtest_engine.store.get_stats(strategy="rsi_meanrev")
```

### 4. Add Stats to Scanner Results

```python
from scanner import Scanner

scanner = Scanner(indicator_engine, backtest_engine)

# Run scan
scan_results = scanner.scan_rsi_oversold(
    symbols=['AAPL', 'GOOGL', 'MSFT'],
    rsi_period=14,
    threshold=30
)

# Stats are automatically added, including win_rate and num_trades
print(scan_results[['symbol', 'rsi', 'win_rate', 'num_trades', 'sharpe_ratio']])
```

### 5. Get Detailed Results (Equity Curve, Trades)

```python
# Get full backtest details
details = backtest_engine.store.get_detailed_results(
    symbol="AAPL",
    strategy="rsi_meanrev",
    params={"rsi_period": 14, "oversold": 30, "overbought": 70}
)

if details:
    # Plot equity curve
    import matplotlib.pyplot as plt
    plt.plot(details['equity_curve'])
    plt.title(f"{details['symbol']} - {details['strategy']}")
    plt.ylabel("Portfolio Value")
    plt.show()
    
    # Access trades if available
    if 'trades' in details:
        print(details['trades'])
```

## Using the Web UI

### Run Manual Backtest

1. Navigate to the **Backtest Manager** section
2. Select strategy: `RSI Mean Reversion` or `MA Crossover`
3. Enter symbol: e.g., `AAPL`
4. Enter parameters as JSON:
   ```json
   {"rsi_period": 14, "oversold": 30, "overbought": 70}
   ```
5. Click **Run Backtest**
6. View results with metrics cards and equity curve

### View Backtest Summary

The **Backtest Summary** section shows all stored backtests in a sortable table.

## Common Use Cases

### Find Best Strategy for a Symbol

```python
# Get all backtests for AAPL
aapl_results = backtest_engine.store.get_stats(symbol="AAPL")

# Sort by Sharpe ratio
best = aapl_results.nlargest(5, 'sharpe_ratio')
print(best[['strategy', 'params', 'sharpe_ratio', 'win_rate']])
```

### Compare Different Parameters

```python
# Test multiple RSI periods
for period in [7, 14, 21, 28]:
    result = backtest_engine.run_single_backtest(
        symbol="AAPL",
        strategy_name="rsi_meanrev",
        params={"rsi_period": period, "oversold": 30, "overbought": 70}
    )
    print(f"RSI({period}): Sharpe={result['metrics']['sharpe_ratio']:.2f}")

# Results are automatically stored and can be queried later
```

### Bulk Analysis

```python
# Get all backtests and analyze
all_stats = backtest_engine.store.get_all_stats()

# Average metrics by strategy
by_strategy = all_stats.groupby('strategy').agg({
    'sharpe_ratio': 'mean',
    'win_rate': 'mean',
    'cagr': 'mean'
})
print(by_strategy)

# Top performers overall
top10 = all_stats.nlargest(10, 'sharpe_ratio')
print(top10[['symbol', 'strategy', 'sharpe_ratio', 'cagr', 'win_rate']])
```

## Performance Tips

1. **Query Metadata First**: Use `get_stats()` for fast filtering before loading detailed results
2. **Bulk Retrieval**: Use `bulk_get_stats()` for multiple lookups
3. **Filter Early**: Apply filters (symbol, strategy) to reduce data loaded
4. **Cache Results**: Store query results in memory if using repeatedly

## Storage Location

- **Store Path**: `./data/backtests/store.zarr`
- **Legacy Summary**: `./data/backtests/summary.parquet` (maintained for compatibility)
- **Metadata**: `./data/backtests/metadata.json`

## Exit Rules (Advanced)

Different exit strategies can be tested with the same entry:

```python
# Same entry, different exits
for exit_rule in ['fixed_stop', 'trailing_stop', 'profit_target']:
    result = backtest_engine.run_single_backtest(
        symbol="AAPL",
        strategy_name="rsi_meanrev",
        params={"rsi_period": 14},
        exit_rule=exit_rule
    )
```

Query by exit rule:

```python
stats = backtest_engine.store.get_stats(
    symbol="AAPL",
    strategy="rsi_meanrev",
    exit_rule="trailing_stop"
)
```

## Troubleshooting

### No Stats Found
- Ensure backtests have been run and stored
- Check symbol/strategy/params match exactly
- Use `get_all_stats()` to see what's available

### Slow Queries
- Normal query time: < 10ms
- If slower: check filter criteria, use more specific filters

### Storage Size
- Check: `backtest_engine.store.get_summary_stats()`
- Typical: ~10-50 MB per 100 backtests
- Clear old results: `backtest_engine.store.clear_all()` (caution!)

## For More Information

- Full documentation: `BACKTEST_STORAGE.md`
- Run tests: `python test_backtest_store.py`
- Run demo: `python demo_backtest_storage.py`
