"""
Dash UI Module
==============
Basic Dash application for scanner configuration and results visualization.
Light UI suitable for quick analysis, not optimized for heavy local use.
"""

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import Optional

from scanner import Scanner
from indicator_engine import IndicatorEngine
from backtest_engine import BacktestEngine

# Data path options to check for price data
DEFAULT_DATA_PATHS = ['./data/prices', './data/stock_data', '../data/prices']


class DashUI:
    """
    Dash-based web UI for scanning and results visualization.
    
    Design:
    - Simple interface for configuring scans
    - Table display of scan results with backtest stats
    - Strategy drilldown for detailed analysis
    - Lightweight, optimized for Colab environment
    """
    
    def __init__(
        self,
        indicator_path: str = "./data/indicators",
        backtest_path: str = "./data/backtests"
    ):
        """
        Initialize Dash UI.
        
        Args:
            indicator_path: Path to indicator storage
            backtest_path: Path to backtest results
        """
        # Initialize engines
        self.indicator_engine = IndicatorEngine(indicator_path)
        self.backtest_engine = BacktestEngine(backtest_path)
        self.scanner = Scanner(self.indicator_engine, self.backtest_engine)
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Setup the UI layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Stock Scanner & Backtest Analyzer", className="text-center mb-4"),
                ], width=12)
            ]),
            
            # Indicator computation section
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H5("⚙️ Indicator Management", className="alert-heading"),
                        html.P([
                            "Before scanning, ensure indicators are computed from your price data. ",
                            "Click below to compute/refresh indicators from Parquet files in ",
                            html.Code("data/prices/"), "."
                        ]),
                        html.Hr(),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "🔧 Compute Indicators",
                                    id='compute-indicators-btn',
                                    color="warning",
                                    className="me-2",
                                    outline=True
                                ),
                                dbc.Button(
                                    "🔄 Refresh Symbol List",
                                    id='refresh-symbols-btn',
                                    color="secondary",
                                    outline=True
                                ),
                            ], width="auto"),
                            dbc.Col([
                                html.Div(id='indicator-status', className="text-end")
                            ])
                        ], align="center", className="g-2"),
                        html.Div(id='indicator-output', className="mt-2", style={'fontSize': '0.9em'})
                    ], color="info", className="mb-3")
                ], width=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Scanner Configuration"),
                        dbc.CardBody([
                            dbc.Label("Scan Type:"),
                            dcc.Dropdown(
                                id='scan-type',
                                options=[
                                    {'label': 'RSI Oversold', 'value': 'rsi_oversold'},
                                    {'label': 'RSI Overbought', 'value': 'rsi_overbought'},
                                    {'label': 'MA Crossover (Bullish)', 'value': 'ma_cross_bull'},
                                    {'label': 'MA Crossover (Bearish)', 'value': 'ma_cross_bear'},
                                    {'label': 'Top Performers', 'value': 'top_performers'}
                                ],
                                value='rsi_oversold',
                                className="mb-3"
                            ),
                            
                            dbc.Label("RSI Period:"),
                            dcc.Input(
                                id='rsi-period',
                                type='number',
                                value=14,
                                className="form-control mb-3"
                            ),
                            
                            dbc.Label("RSI Threshold:"),
                            dcc.Input(
                                id='rsi-threshold',
                                type='number',
                                value=30,
                                className="form-control mb-3"
                            ),
                            
                            dbc.Label("Fast MA Period:"),
                            dcc.Input(
                                id='fast-ma',
                                type='number',
                                value=20,
                                className="form-control mb-3"
                            ),
                            
                            dbc.Label("Slow MA Period:"),
                            dcc.Input(
                                id='slow-ma',
                                type='number',
                                value=50,
                                className="form-control mb-3"
                            ),
                            
                            dbc.Button(
                                "Run Scan",
                                id='run-scan-btn',
                                color="primary",
                                className="w-100"
                            )
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Scan Results"),
                        dbc.CardBody([
                            html.Div(id='scan-results-div'),
                            html.Div(id='scan-status', className="mt-2")
                        ])
                    ])
                ], width=9)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Backtest Summary"),
                        dbc.CardBody([
                            html.Div(id='backtest-summary-div')
                        ])
                    ])
                ], width=12)
            ])
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Setup Dash callbacks."""
        
        @self.app.callback(
            [Output('scan-results-div', 'children'),
             Output('scan-status', 'children')],
            Input('run-scan-btn', 'n_clicks'),
            [State('scan-type', 'value'),
             State('rsi-period', 'value'),
             State('rsi-threshold', 'value'),
             State('fast-ma', 'value'),
             State('slow-ma', 'value')]
        )
        def run_scan(n_clicks, scan_type, rsi_period, rsi_threshold, fast_ma, slow_ma):
            """Run the selected scan."""
            if n_clicks is None:
                return html.P("Configure scan and click 'Run Scan'"), ""
            
            try:
                # Get available symbols
                symbols = self.indicator_engine.list_available_symbols()
                
                if not symbols:
                    return html.P("No symbols with indicators found. Please run indicator computation first."), ""
                
                # Run appropriate scan
                if scan_type == 'rsi_oversold':
                    results = self.scanner.scan_rsi_oversold(symbols, rsi_period, rsi_threshold)
                    status = f"Found {len(results)} oversold stocks (RSI < {rsi_threshold})"
                
                elif scan_type == 'rsi_overbought':
                    results = self.scanner.scan_rsi_overbought(symbols, rsi_period, rsi_threshold)
                    status = f"Found {len(results)} overbought stocks (RSI > {rsi_threshold})"
                
                elif scan_type == 'ma_cross_bull':
                    results = self.scanner.scan_ma_crossover(symbols, fast_ma, slow_ma, 'bullish')
                    status = f"Found {len(results)} bullish MA crossovers"
                
                elif scan_type == 'ma_cross_bear':
                    results = self.scanner.scan_ma_crossover(symbols, fast_ma, slow_ma, 'bearish')
                    status = f"Found {len(results)} bearish MA crossovers"
                
                elif scan_type == 'top_performers':
                    results = self.scanner.get_top_performers('rsi_meanrev', metric='sharpe_ratio', top_n=20)
                    status = f"Top 20 performers by Sharpe ratio"
                
                else:
                    return html.P("Unknown scan type"), ""
                
                # Display results
                if results is None or len(results) == 0:
                    return html.P("No results found"), status
                
                # Create table
                table = dash_table.DataTable(
                    data=results.to_dict('records'),
                    columns=[{'name': col, 'id': col} for col in results.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=20
                )
                
                return table, html.P(status, className="text-success")
            
            except Exception as e:
                return html.P(f"Error: {str(e)}"), html.P(str(e), className="text-danger")
        
        @self.app.callback(
            Output('backtest-summary-div', 'children'),
            Input('run-scan-btn', 'n_clicks')
        )
        def update_backtest_summary(n_clicks):
            """Update backtest summary statistics."""
            try:
                summary = self.backtest_engine.load_summary()
                
                if summary is None or len(summary) == 0:
                    return html.P("No backtest results available. Please run backtests first.")
                
                # Calculate aggregate statistics
                avg_metrics = summary.groupby('strategy').agg({
                    'cagr': 'mean',
                    'sharpe_ratio': 'mean',
                    'win_rate': 'mean',
                    'max_drawdown': 'mean',
                    'num_trades': 'mean'
                }).round(4)
                
                # Create summary table
                table = dash_table.DataTable(
                    data=avg_metrics.reset_index().to_dict('records'),
                    columns=[{'name': col, 'id': col} for col in avg_metrics.reset_index().columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }
                )
                
                return [
                    html.H5(f"Average Performance Across {len(summary)} Backtests", className="mb-3"),
                    table
                ]
            
            except Exception as e:
                return html.P(f"Error loading backtest summary: {str(e)}")
        
        @self.app.callback(
            [Output('indicator-output', 'children'),
             Output('indicator-status', 'children')],
            Input('compute-indicators-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def compute_indicators(n_clicks):
            """Compute indicators from price data."""
            if n_clicks is None:
                return "", ""
            
            try:
                from data_loader import DataLoader
                import os
                
                # Determine data path - try common locations
                data_path = None
                for path in DEFAULT_DATA_PATHS:
                    if os.path.exists(path):
                        data_path = path
                        break
                
                if data_path is None:
                    return html.Div([
                        html.P("❌ No price data directory found.", className="text-danger mb-1"),
                        html.P("Expected directories: data/prices/ or data/stock_data/", 
                               className="text-muted small")
                    ]), html.Span("❌ Failed", className="badge bg-danger")
                
                # Load data
                loader = DataLoader(data_path)
                symbols = loader.list_available_symbols()
                
                if not symbols:
                    return html.Div([
                        html.P("❌ No Parquet files found in data directory.", className="text-danger mb-1"),
                        html.P(f"Location: {data_path}", className="text-muted small")
                    ]), html.Span("❌ Failed", className="badge bg-danger")
                
                # Show progress
                output_msg = html.Div([
                    html.P(f"⏳ Processing {len(symbols)} symbols from {data_path}...", 
                           className="mb-1"),
                    html.P("This may take a minute. Please wait...", 
                           className="text-muted small")
                ])
                
                # Load data
                data_dict = loader.load_multiple_symbols(symbols)
                
                if not data_dict:
                    return html.Div([
                        html.P("❌ Failed to load any symbols.", className="text-danger mb-1"),
                        html.P("Check that Parquet files have correct OHLCV columns.", 
                               className="text-muted small")
                    ]), html.Span("❌ Failed", className="badge bg-danger")
                
                # Compute indicators
                # Compute multiple RSI periods to support user selection in UI
                self.indicator_engine.process_multiple_symbols(
                    data_dict,
                    sma_periods=[20, 50, 200],
                    rsi_periods=[7, 14, 21, 28],
                    show_progress=False  # Disable progress bar in UI
                )
                
                # Verify results
                available = self.indicator_engine.list_available_symbols()
                
                return html.Div([
                    html.P("✅ Indicators computed successfully!", className="text-success mb-1"),
                    html.P([
                        f"{len(available)} symbols now available. ",
                        html.Strong("Click 'Run Scan' to use them.")
                    ], className="small")
                ]), html.Span(f"✅ {len(available)} symbols", className="badge bg-success")
            
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                return html.Div([
                    html.P(f"❌ Error: {str(e)}", className="text-danger mb-1"),
                    html.Details([
                        html.Summary("Show details", className="small text-muted"),
                        html.Pre(error_details, className="small bg-light p-2")
                    ])
                ]), html.Span("❌ Error", className="badge bg-danger")
        
        @self.app.callback(
            Output('indicator-status', 'children', allow_duplicate=True),
            Input('refresh-symbols-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def refresh_symbols(n_clicks):
            """Refresh the count of available symbols."""
            if n_clicks is None:
                return ""
            
            try:
                available = self.indicator_engine.list_available_symbols()
                if not available:
                    return html.Span("⚠️ No symbols", className="badge bg-warning")
                return html.Span(f"✅ {len(available)} symbols", className="badge bg-success")
            except Exception as e:
                return html.Span(f"❌ Error: {str(e)}", className="badge bg-danger")
    
    def run(self, host: str = '0.0.0.0', port: int = 8050, debug: bool = False):
        """
        Run the Dash server.
        
        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        self.app.run(host=host, port=port, debug=debug)


def create_app(indicator_path: str = "./data/indicators",
               backtest_path: str = "./data/backtests"):
    """
    Factory function to create and return Dash app instance.
    
    Args:
        indicator_path: Path to indicator storage
        backtest_path: Path to backtest results
        
    Returns:
        DashUI instance
    """
    return DashUI(indicator_path, backtest_path)


if __name__ == '__main__':
    # For running standalone
    ui = create_app()
    ui.run(debug=True)
