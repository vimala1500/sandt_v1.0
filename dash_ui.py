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
        indicator_path: str = "/content/drive/MyDrive/indicators",
        backtest_path: str = "/content/drive/MyDrive/backtests"
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
    
    def run(self, host: str = '0.0.0.0', port: int = 8050, debug: bool = False):
        """
        Run the Dash server.
        
        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        self.app.run_server(host=host, port=port, debug=debug)


def create_app(indicator_path: str = "/content/drive/MyDrive/indicators",
               backtest_path: str = "/content/drive/MyDrive/backtests"):
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
