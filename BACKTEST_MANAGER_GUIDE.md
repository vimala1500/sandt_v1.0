# Backtest Manager Portal Guide

## Overview

The Backtest Manager Portal is an advanced batch backtesting interface that allows you to run and analyze multiple strategies across multiple symbols simultaneously. It provides professional-grade results visualization, group set management, and comprehensive export capabilities.

## Features

### 1. Multi-Select Interface

#### Strategy Selection
- **Multiple Strategy Types**: Select from available strategies (RSI Mean Reversion, MA Crossover, etc.)
- **Parameter Variations**: Each strategy includes multiple parameter sets automatically
- **Select All/Clear**: Quick buttons to select or deselect all strategies
- **Parameter Preview**: See all parameter combinations that will be tested

#### Symbol Selection
- **Search & Filter**: Type to filter symbols from your indicator database
- **Bulk Import**: Paste comma or newline-separated symbol lists
- **Select All/Clear**: Quick selection controls
- **Dynamic Loading**: Only shows symbols with computed indicators

### 2. Batch Execution

#### Job Configuration
- **Exit Rules**: Choose from multiple exit strategies (Default, Trailing Stop, Profit Target)
- **Job Summary**: Real-time calculation of total jobs to be executed
- **Progress Tracking**: Visual progress bar with status updates
- **Error Handling**: Graceful handling of failed backtests with detailed reporting

#### Execution Flow
```python
Total Jobs = (Number of Symbols) × (Number of Parameter Sets) × (Number of Exit Rules)

Example:
- 10 symbols
- 2 strategies with 3 param sets each = 6 param sets
- 2 exit rules
= 10 × 6 × 2 = 120 total backtest jobs
```

### 3. Results Display

#### Grouped Views

**Strategy-Grouped View**
- Results organized by strategy type
- Summary statistics per strategy
- Easy comparison of strategy performance across symbols
- Sortable and filterable tables

**Symbol-Grouped View**
- Results organized by symbol
- Summary statistics per symbol
- Compare different strategies on the same stock
- Identify best-performing strategies per symbol

#### Summary Statistics
Each group shows:
- Average Win Rate
- Average Sharpe Ratio
- Average CAGR (Compound Annual Growth Rate)
- Total Number of Trades

#### Result Columns
- **Symbol/Strategy**: Identifier
- **Params**: Parameter configuration used
- **Exit**: Exit rule applied
- **Win Rate**: Percentage of winning trades
- **Trades**: Total number of trades executed
- **CAGR**: Annualized growth rate
- **Sharpe**: Risk-adjusted return metric
- **Max DD**: Maximum drawdown
- **Total Ret**: Total return percentage

#### Visual Highlights
- High Sharpe ratios (>1.0) are highlighted in green
- High win rates (>60%) are highlighted in green
- Alternating row colors for readability

### 4. Group Set Management

#### Save Group Sets
- Save your current strategy/symbol configuration
- Name your group sets (e.g., "My S&P500 Momentum")
- Persists across sessions
- Includes all selections: strategies, symbols, params, exit rules

#### Load Group Sets
- Quickly restore previously saved configurations
- One-click setup for recurring analyses
- Share configurations with team members

#### List & Delete
- View all saved group sets
- Delete unused configurations
- Rename and organize your sets

### 5. Export Capabilities

#### CSV Export
- Export results to CSV format
- Compatible with Excel, Google Sheets, etc.
- Includes all result columns
- Preserves parameter configurations as JSON strings

#### XLSX Export
- Native Excel format export
- Better formatting preservation
- Easier for business users
- Multiple sheets for different views (future enhancement)

## Usage Guide

### Quick Start

1. **Access the Portal**
   ```bash
   python app.py
   # Navigate to http://localhost:8050
   # Click on "🚀 Backtest Manager" tab
   ```

2. **Select Strategies**
   - Check the strategies you want to test
   - Review parameter sets in the preview panel
   - Use "Select All" for comprehensive testing

3. **Select Symbols**
   - Use search box to filter symbols
   - Check individual symbols or use "Select All"
   - Or paste a list of symbols in the bulk import box and click "Import Symbols"

4. **Choose Exit Rules**
   - Select one or more exit rule variations
   - Default is recommended for initial testing

5. **Launch Batch**
   - Review the job summary
   - Click "🚀 Launch Batch Backtest"
   - Monitor progress bar

6. **View Results**
   - Toggle between "By Strategy" and "By Symbol" views
   - Sort and filter results
   - Export to CSV or XLSX

### Advanced Workflows

#### Comparing Strategy Performance
1. Select all strategies
2. Choose 5-10 representative symbols
3. Use default exit rules
4. Launch batch
5. Switch to Strategy-Grouped view
6. Sort by Sharpe Ratio to find best performers

#### Finding Best Stocks for a Strategy
1. Select one strategy (e.g., RSI Mean Reversion)
2. Select large universe of symbols (50-100)
3. Choose default exit rule
4. Launch batch
5. Switch to Symbol-Grouped view
6. Sort by Win Rate or CAGR to find best stocks

#### Parameter Optimization
1. Select one strategy
2. Use multiple parameter sets (already included)
3. Select 10-20 symbols
4. Launch batch
5. Compare results across parameter sets
6. Identify optimal parameters

#### Exit Rule Comparison
1. Select one strategy with one param set
2. Select 10-20 symbols
3. Check all exit rules
4. Launch batch
5. Compare performance across exit strategies

### Best Practices

#### Performance Optimization
- **Start Small**: Test with 5-10 symbols first
- **Incremental Testing**: Add more symbols after validating setup
- **Use Group Sets**: Save successful configurations for reuse
- **Monitor Progress**: Watch status messages for errors

#### Result Interpretation
- **Statistical Significance**: More trades = more reliable metrics
- **Win Rate Context**: High win rate with few trades may not be robust
- **Sharpe Ratio**: Values >1.0 indicate good risk-adjusted returns
- **Drawdown Analysis**: Consider maximum drawdown tolerance

#### Data Management
- **Regular Exports**: Export results after each major batch
- **Group Set Organization**: Name group sets clearly
- **Result Archives**: Keep CSV exports for historical comparison

## API Usage

### Programmatic Access

```python
from backtest_engine import BacktestEngine
from strategy import StrategyConfig

# Initialize engine
engine = BacktestEngine("./data/backtests")

# Define strategies
configs = [
    StrategyConfig(
        name="rsi_meanrev",
        params={"rsi_period": 14, "oversold": 30, "overbought": 70}
    ),
    StrategyConfig(
        name="ma_crossover",
        params={"fast_period": 20, "slow_period": 50}
    )
]

# Run batch backtests
symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
exit_rules = ["default", "trailing_stop"]

results_df, job_stats = engine.run_batch_backtests(
    symbols=symbols,
    strategy_configs=configs,
    exit_rules=exit_rules,
    progress_callback=lambda curr, total, msg: print(f"{curr}/{total}: {msg}")
)

# Analyze results
print(f"Completed {job_stats['completed']} of {job_stats['total_jobs']} jobs")
print(f"Success rate: {job_stats['success_rate']*100:.1f}%")
print(f"\nTop 10 by Sharpe Ratio:")
print(results_df.nlargest(10, 'sharpe_ratio')[
    ['symbol', 'strategy', 'sharpe_ratio', 'win_rate', 'cagr']
])

# Export results
results_df.to_csv("batch_results.csv", index=False)
```

### Group Set Management

```python
from backtest_store import BacktestStore

# Initialize store
store = BacktestStore("./data/backtests/store.zarr")

# Save a group set
store.save_group_set(
    name="Tech Giants Momentum",
    symbols=["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
    strategies=["rsi_meanrev", "ma_crossover"],
    params_list=[
        {"rsi_period": 14, "oversold": 30, "overbought": 70},
        {"fast_period": 20, "slow_period": 50}
    ],
    exit_rules=["default", "trailing_stop"]
)

# Load a group set
group = store.load_group_set("Tech Giants Momentum")
print(f"Loaded group with {len(group['symbols'])} symbols")

# List all group sets
all_groups = store.list_group_sets()
print(f"Available group sets: {all_groups}")

# Delete a group set
store.delete_group_set("Old Configuration")
```

## Technical Details

### Storage Format
- **Zarr-based**: Efficient chunked storage
- **Metadata Arrays**: Fast filtering without loading full data
- **Group Sets**: Stored in separate Zarr group
- **Persistence**: All data persists across sessions

### Performance Characteristics
- **Batch Size**: Can handle 1000+ symbol/strategy combinations
- **Memory Usage**: ~100-500 MB for typical batch
- **Execution Time**: ~1-5 seconds per backtest
- **Storage**: ~10-50 MB per 100 backtests

### Scalability
- **Symbols**: Tested with 1000+ symbols
- **Strategies**: Unlimited strategy definitions
- **Parameter Sets**: Multiple variations per strategy
- **Exit Rules**: Multiple exit strategies supported
- **Results**: Efficiently stores and queries millions of backtest results

## Troubleshooting

### Common Issues

**No Symbols Available**
- Ensure indicators are computed: Click "Compute Indicators" in Scanner tab
- Check that price data exists in `data/prices/` directory
- Verify indicator files in `data/indicators/` directory

**Batch Execution Fails**
- Check that all selected symbols have indicator data
- Verify strategy parameters are valid
- Review error messages in status display
- Check console logs for detailed error traces

**Slow Performance**
- Reduce number of symbols in initial test
- Use fewer parameter variations
- Ensure sufficient system memory
- Close other resource-intensive applications

**Export Not Working**
- Ensure results exist (run a batch first)
- Check browser's download settings
- Try alternative export format (CSV vs XLSX)
- Check disk space availability

## Trade-by-Trade Analysis

### Overview

When you click on any row in the batch backtest results tables, a detailed modal opens displaying comprehensive trade-by-trade analysis for that specific backtest run.

### Features

#### 1. Summary Metrics Card
Displays key performance indicators:
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of trades executed
- **CAGR**: Compound Annual Growth Rate
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough decline
- **Total Return**: Overall percentage return
- **Expectancy**: Average return per trade

#### 2. Trade Statistics Card
Advanced trading metrics:
- **Winning Trades**: Count of profitable trades
- **Losing Trades**: Count of unprofitable trades
- **Average Win**: Mean return of winning trades
- **Average Loss**: Mean loss of losing trades
- **Profit Factor**: Ratio of average win to average loss
- **Average Holding Period**: Mean number of days per trade

#### 3. Equity Curve Visualization
Interactive Plotly chart showing:
- Portfolio equity over time
- Visual representation of strategy performance
- Hover details for specific dates

#### 4. Trade P&L Distribution
Histogram chart displaying:
- Distribution of trade returns
- Frequency of gains vs losses
- Visual representation of trade outcomes

#### 5. Drawdown Chart
Time-series plot showing:
- Drawdown percentage over time
- Peak-to-trough declines
- Recovery periods

#### 6. Trade-by-Trade Table
Comprehensive table with all trade details:

**Columns:**
- **Trade No.**: Sequential trade number
- **Entry Date**: Date position was opened
- **Entry Price**: Price at entry
- **Exit Date**: Date position was closed
- **Exit Price**: Price at exit
- **Position**: Type (Long/Short)
- **Size**: Number of shares/units
- **Holding Period**: Days in position
- **P&L %**: Percentage profit/loss
- **P&L $**: Dollar profit/loss
- **MAE**: Maximum Adverse Excursion (worst drawdown during trade)
- **MFE**: Maximum Favorable Excursion (best gain during trade)
- **Exit Reason**: Why trade was closed (Signal Exit, Signal Reversal, End of Period)
- **Comments**: Additional notes (customizable)

**Table Features:**
- **Sortable**: Click column headers to sort
- **Filterable**: Use filter inputs to find specific trades
- **Exportable**: Built-in CSV export functionality
- **Color-coded**: Profitable trades in green, losses in red
- **Paginated**: 20 trades per page for easy navigation

### Usage

1. **Access Trade Details**
   - Run a batch backtest as usual
   - View results in strategy-grouped or symbol-grouped view
   - Click on any row in the results table
   - Trade details modal opens automatically

2. **Analyze Trades**
   - Review summary metrics for overall performance
   - Check trade statistics for win/loss patterns
   - Examine equity curve for growth trajectory
   - Study P&L distribution for consistency
   - Review drawdown chart for risk assessment
   - Drill down into individual trades in the table

3. **Export Trade Data**
   - Use table's built-in export for filtered data
   - Save for further analysis in Excel or other tools

4. **Close Modal**
   - Click "Close" button to return to results
   - Click another row to view different backtest

### Best Practices

#### Trade Analysis
- **Focus on MAE/MFE**: Understand how much pain/pleasure each trade experienced
- **Review Exit Reasons**: Identify if exits are timely or premature
- **Check Holding Periods**: Ensure trades align with strategy timeframe
- **Study Outliers**: Examine best and worst trades for patterns

#### Performance Assessment
- **Win Rate Context**: High win rate with low profit factor may indicate cutting winners short
- **Expectancy**: Positive expectancy is crucial for long-term profitability
- **Drawdown Recovery**: Assess how quickly strategy recovers from drawdowns
- **Equity Curve Smoothness**: Smoother curves indicate more consistent performance

#### Risk Management
- **MAE Analysis**: Identify optimal stop-loss levels
- **Trade Size**: Ensure position sizing is appropriate for account
- **Drawdown Tolerance**: Verify max drawdown is acceptable
- **Holding Period Distribution**: Check if aligned with market conditions

## Future Enhancements

Planned features for future releases:

1. **Enhanced Trade Visualizations**
   - Price chart with entry/exit markers overlaid
   - Trade duration heatmap
   - Win/loss streak analysis

2. **Advanced Filtering**
   - Multi-criteria result filtering
   - Saved filter presets
   - Custom metric calculations

4. **Cancellation & Pause**
   - Stop batch execution mid-run
   - Pause and resume capabilities
   - Job queue management

5. **Scheduling**
   - Automated nightly backtest runs
   - Email notifications on completion
   - Result comparison over time

## Support

For issues, questions, or feature requests:
- Check existing documentation
- Review test files for usage examples
- Open GitHub issues for bugs
- Contribute improvements via pull requests
