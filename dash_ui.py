"""
Dash UI Module
==============
Basic Dash application for scanner configuration and results visualization.
Light UI suitable for quick analysis, not optimized for heavy local use.
"""

import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import uuid
from typing import Optional

from scanner import Scanner
from indicator_engine import IndicatorEngine
from backtest_engine import BacktestEngine
from backtest_manager_ui import BacktestManagerUI
from session_manager import get_session_manager, SessionManager
from error_handler import (
    with_error_handling,
    safe_execute,
    handle_callback_error,
    ApplicationError
)

# Data path options to check for price data
DEFAULT_DATA_PATHS = ['./data/prices', './data/stock_data', '../data/prices']


class DashUI:
    """
    Dash-based web UI for scanning and results visualization.
    
    Design:
    - Simple interface for configuring scans
    - Table display of scan results with backtest stats
    - Strategy drilldown for detailed analysis
    - Advanced Backtest Manager portal
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
        # Initialize session manager
        self.session_manager = get_session_manager()
        self.session_id = str(uuid.uuid4())
        self.session_manager.create_session(
            self.session_id,
            metadata={'type': 'dash_ui', 'indicator_path': indicator_path}
        )
        
        # Initialize engines
        self.indicator_engine = IndicatorEngine(indicator_path)
        self.backtest_engine = BacktestEngine(backtest_path)
        self.scanner = Scanner(self.indicator_engine, self.backtest_engine)
        
        # Initialize Backtest Manager UI with session manager
        self.backtest_manager = BacktestManagerUI(
            self.indicator_engine, 
            self.backtest_engine,
            session_manager=self.session_manager
        )
        
        # Initialize Dash app with dark theme CSS
        external_stylesheets = [
            'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
            'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap'
        ]
        
        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder='assets'
        )
        
        # Set app title
        self.app.title = "Quant Dashboard - Stock Analysis & Trading"
        
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Setup the UI layout."""
        self.app.layout = dbc.Container([
            # Session status banner
            html.Div(id='session-status-banner', className="mb-3"),
            
            # Hidden interval for health checks
            dcc.Interval(
                id='health-check-interval',
                interval=30*1000,  # Check every 30 seconds
                n_intervals=0
            ),
            
            # Hidden store for session ID
            dcc.Store(id='session-id-store', data=self.session_id),
            
            # Header Section
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H1("📊 Quantitative Trading Dashboard", 
                                   className="text-center mb-2 main-title",
                                   style={'fontSize': '2.5rem'}),
                            html.P("Professional Stock Analysis & Backtesting Platform", 
                                  className="text-center mb-4",
                                  style={'fontSize': '1.1rem', 'fontWeight': '300', 'color': 'var(--text-secondary)'})
                        ])
                    ], width=12)
                ], className="mb-4")
            ], className="page-header"),
            
            # Navigation Tabs
            dbc.Tabs([
                # Indicators Tab
                dbc.Tab(
                    label="⚙️ Indicators",
                    tab_id="indicators-tab",
                    children=self._create_indicators_layout()
                ),
                
                # Backtest Tab
                dbc.Tab(
                    label="📊 Backtest",
                    tab_id="backtest-tab",
                    children=self.backtest_manager.create_layout()
                ),
                
                # Scanner Tab
                dbc.Tab(
                    label="📡 Scanner",
                    tab_id="scanner-tab",
                    children=self._create_scanner_layout()
                )
            ], id="main-tabs", active_tab="indicators-tab", className="mb-4")
        ], fluid=True, style={'paddingTop': '20px', 'paddingBottom': '40px'})
    
    def _create_indicators_layout(self):
        """Create indicators page layout."""
        return html.Div([
            # Summary Panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4("📊 Indicator Computation Status", className="mb-0")
                        ]),
                        dbc.CardBody([
                            html.Div(id='indicator-summary-panel', children=[
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.H6("Last Computation", className="text-muted mb-2"),
                                            html.H4(id='last-computation-date', children="Not computed yet", 
                                                   className="mb-0")
                                        ])
                                    ], width=4),
                                    dbc.Col([
                                        html.Div([
                                            html.H6("Symbols Processed", className="text-muted mb-2"),
                                            html.H4(id='symbols-count', children="0", 
                                                   className="mb-0")
                                        ])
                                    ], width=4),
                                    dbc.Col([
                                        html.Div([
                                            html.H6("Status", className="text-muted mb-2"),
                                            html.H4(id='indicator-status-text', children="⚠️ No Data", 
                                                   className="mb-0 text-warning")
                                        ])
                                    ], width=4)
                                ], className="mb-3"),
                                html.Hr(),
                                html.P([
                                    "Indicators must be computed from your price data before you can run backtests or scans. ",
                                    "This process analyzes historical OHLCV data and creates technical indicators stored in HDF5 format."
                                ], className="text-muted small mb-0")
                            ])
                        ])
                    ], className="mb-4", style={'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
                ], width=12)
            ]),
            
            # Compute Indicators Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⚙️ Compute Indicators"),
                        dbc.CardBody([
                            html.P([
                                "Compute technical indicators from Parquet files in ",
                                html.Code("data/prices/"),
                                ". This will analyze all available symbols and create indicators including SMA, RSI, EMA, candlestick patterns, and more."
                            ], className="mb-3"),
                            
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button(
                                        "🔧 Compute Indicators",
                                        id='compute-indicators-btn',
                                        color="primary",
                                        size="lg",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "🔄 Refresh Status",
                                        id='refresh-symbols-btn',
                                        color="secondary",
                                        size="lg",
                                        outline=True
                                    ),
                                ], width="auto")
                            ], className="mb-3"),
                            
                            html.Div(id='indicator-output', className="mt-3", 
                                    style={'fontSize': '0.9em', 'fontFamily': 'monospace'}),
                            
                            dbc.Alert(
                                id='indicator-computation-alert',
                                is_open=False,
                                dismissable=True,
                                className="mt-3"
                            )
                        ])
                    ], className="mb-4")
                ], width=12)
            ]),
            
            # Available Indicators Display
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📋 Available Indicators"),
                        dbc.CardBody([
                            html.Div(id='available-indicators-list', children=[
                                html.P("Compute indicators to see available indicators here.", 
                                      className="text-muted")
                            ])
                        ])
                    ])
                ], width=12)
            ])
        ])
    
    def _create_scanner_layout(self):
        """Create scanner tab layout."""
        return html.Div([
            # Scanner Configuration and Results
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
                                    {'label': 'Candlestick Patterns', 'value': 'candlestick'},
                                    {'label': 'Momentum Streaks', 'value': 'momentum_streak'},
                                    {'label': 'Custom Indicator Filter', 'value': 'custom_indicator'},
                                    {'label': 'Top Performers', 'value': 'top_performers'}
                                ],
                                value='rsi_oversold',
                                className="mb-3"
                            ),
                            
                            # RSI controls
                            html.Div(id='rsi-controls', children=[
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
                                )
                            ]),
                            
                            # MA controls
                            html.Div(id='ma-controls', children=[
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
                                )
                            ]),
                            
                            # Candlestick pattern controls
                            html.Div(id='candlestick-controls', children=[
                                dbc.Label("Pattern Type:"),
                                dcc.Dropdown(
                                    id='pattern-type',
                                    options=[
                                        {'label': 'Bullish Engulfing', 'value': 'engulfing_bull'},
                                        {'label': 'Bearish Engulfing', 'value': 'engulfing_bear'},
                                        {'label': 'Hammer', 'value': 'hammer'},
                                        {'label': 'Shooting Star', 'value': 'shooting_star'},
                                        {'label': 'Doji', 'value': 'doji'},
                                        {'label': 'Hanging Man', 'value': 'hanging_man'},
                                        {'label': 'Bullish Harami', 'value': 'harami_bull'},
                                        {'label': 'Bearish Harami', 'value': 'harami_bear'},
                                        {'label': 'Dark Cloud Cover', 'value': 'dark_cloud'},
                                        {'label': 'Piercing Pattern', 'value': 'piercing'},
                                        {'label': 'Three White Soldiers', 'value': 'three_white_soldiers'},
                                        {'label': 'Three Black Crows', 'value': 'three_black_crows'}
                                    ],
                                    value='engulfing_bull',
                                    className="mb-3"
                                )
                            ], style={'display': 'none'}),
                            
                            # Momentum streak controls
                            html.Div(id='streak-controls', children=[
                                dbc.Label("Streak Type:"),
                                dcc.Dropdown(
                                    id='streak-type',
                                    options=[
                                        {'label': 'Consecutive Higher Highs', 'value': 'consec_higher_high'},
                                        {'label': 'Consecutive Lower Lows', 'value': 'consec_lower_low'}
                                    ],
                                    value='consec_higher_high',
                                    className="mb-2"
                                ),
                                dbc.Label("Minimum Streak Days:"),
                                dcc.Input(
                                    id='streak-threshold',
                                    type='number',
                                    value=3,
                                    min=1,
                                    className="form-control mb-3"
                                )
                            ], style={'display': 'none'}),
                            
                            # Custom indicator controls
                            html.Div(id='custom-indicator-controls', children=[
                                dbc.Label("Select Indicator:"),
                                dcc.Dropdown(
                                    id='custom-indicator',
                                    options=[],  # Will be populated dynamically
                                    value=None,
                                    className="mb-2"
                                ),
                                dbc.Label("Operator:"),
                                dcc.Dropdown(
                                    id='custom-operator',
                                    options=[
                                        {'label': 'Greater than (>)', 'value': '>'},
                                        {'label': 'Less than (<)', 'value': '<'},
                                        {'label': 'Greater or equal (>=)', 'value': '>='},
                                        {'label': 'Less or equal (<=)', 'value': '<='},
                                        {'label': 'Equal (==)', 'value': '=='},
                                        {'label': 'Not equal (!=)', 'value': '!='}
                                    ],
                                    value='>',
                                    className="mb-2"
                                ),
                                dbc.Label("Threshold Value:"),
                                dcc.Input(
                                    id='custom-threshold',
                                    type='number',
                                    value=0,
                                    className="form-control mb-3"
                                )
                            ], style={'display': 'none'}),
                            
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
            
            # Backtest Summary Section  
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
        ])
    
    def _create_quick_backtest_layout(self):
        """Create quick backtest tab layout."""
        return html.Div([
            # Backtest Controls Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Quick Backtest"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Strategy:"),
                                    dcc.Dropdown(
                                        id='backtest-strategy',
                                        options=[
                                            {'label': 'RSI Mean Reversion', 'value': 'rsi_meanrev'},
                                            {'label': 'MA Crossover', 'value': 'ma_crossover'}
                                        ],
                                        value='rsi_meanrev',
                                        className="mb-2"
                                    ),
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Symbol:"),
                                    dcc.Input(
                                        id='backtest-symbol',
                                        type='text',
                                        placeholder='Enter symbol',
                                        className="form-control mb-2"
                                    ),
                                ], width=6)
                            ]),
                            html.Div(id='backtest-params-div', children=[
                                dbc.Label("Parameters (JSON):"),
                                dcc.Textarea(
                                    id='backtest-params',
                                    placeholder='{"rsi_period": 14, "oversold": 30, "overbought": 70}',
                                    className="form-control mb-2",
                                    style={'height': '80px'}
                                )
                            ]),
                            dbc.Button(
                                "🚀 Run Backtest",
                                id='run-backtest-btn',
                                color="success",
                                className="w-100 mt-2"
                            ),
                            html.Div(id='backtest-status', className="mt-2")
                        ])
                    ])
                ], width=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Backtest Details"),
                        dbc.CardBody([
                            html.Div(id='backtest-details-div')
                        ])
                    ])
                ], width=9)
            ])
        ])
    
    def _setup_callbacks(self):
        """Setup Dash callbacks."""
        
        # Setup Backtest Manager callbacks
        self.backtest_manager.setup_callbacks(self.app)
        
        # Health check callback
        @self.app.callback(
            Output('session-status-banner', 'children'),
            [Input('health-check-interval', 'n_intervals'),
             Input('session-id-store', 'data')]
        )
        def check_session_health(n_intervals, session_id):
            """Periodic health check of the session."""
            if not session_id:
                # No session - this is unusual, but can happen on first load
                # Don't show error on initial load (n_intervals == 0)
                if n_intervals == 0:
                    return None
                
                # Show prominent "Start New Session" banner
                return dbc.Alert([
                    html.Div([
                        html.H5("🔔 Session Not Found", className="alert-heading mb-3"),
                        html.P([
                            "Your session could not be found. This may happen if:",
                            html.Ul([
                                html.Li("The page was refreshed after a long period of inactivity"),
                                html.Li("The server was restarted"),
                                html.Li("There was a connection issue")
                            ], className="mb-3")
                        ]),
                        dbc.Button(
                            "🔄 Start New Session",
                            id='start-new-session-btn',
                            color="primary",
                            size="lg",
                            className="me-2"
                        ),
                        html.Span("Click to create a new session and continue", className="text-muted small")
                    ])
                ], color="warning", dismissable=False, className="mb-4", 
                   style={'border': '2px solid #ff9800', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
            
            # Check if session exists in manager
            try:
                session_state = self.session_manager.get_session(session_id)
                if session_state is None:
                    # Session doesn't exist in manager - create it silently
                    self.session_manager.create_session(
                        session_id,
                        metadata={'type': 'dash_ui_auto', 'indicator_path': self.indicator_engine.storage_path}
                    )
            except Exception as e:
                # Silently handle session creation errors
                pass
            
            # Update session activity
            self.session_manager.update_session_activity(session_id)
            
            # Check health
            health_status = self.session_manager.check_health(session_id)
            
            # Only show banner if there's an issue
            if not health_status.get('healthy', True):
                message = self.session_manager.get_user_friendly_message(health_status)
                recovery = self.session_manager.get_recovery_instructions(health_status)
                
                severity_map = {
                    'error': 'danger',
                    'warning': 'warning',
                    'expired': 'warning',
                    'disconnected': 'warning',
                    'failed': 'danger'
                }
                
                status_type = health_status.get('status', 'error')
                alert_color = severity_map.get(status_type, 'warning')
                
                banner = dbc.Alert([
                    html.H5([
                        "⚠️ Session Issue Detected" if alert_color == 'warning' else "❌ Session Error"
                    ], className="alert-heading"),
                    html.Div(message, className="mb-2"),
                    html.Hr() if recovery else None,
                    html.Div([
                        html.Strong("Recovery Steps:", className="d-block mb-2"),
                        html.Pre(recovery, style={'whiteSpace': 'pre-line', 'fontSize': '0.9em'})
                    ], className="mb-3") if recovery else None,
                    dbc.ButtonGroup([
                        dbc.Button(
                            "🔄 Refresh Page",
                            id='refresh-page-btn',
                            color="primary",
                            size="sm",
                            outline=True
                        ),
                        dbc.Button(
                            "🆕 Start New Session",
                            id='start-new-session-btn',
                            color="success",
                            size="sm"
                        )
                    ])
                ], color=alert_color, dismissable=True, className="mb-4",
                   style={
                       'border': f'2px solid {"#dc3545" if alert_color == "danger" else "#ff9800"}',
                       'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
                   })
                
                return banner
            
            return None
        
        @self.app.callback(
            Output('session-id-store', 'data'),
            [Input('start-new-session-btn', 'n_clicks'),
             Input('refresh-page-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_session_recovery(new_session_clicks, refresh_clicks):
            """Handle session recovery actions."""
            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'start-new-session-btn':
                # Create a new session
                new_session_id = str(uuid.uuid4())
                self.session_manager.create_session(
                    new_session_id,
                    metadata={'type': 'dash_ui_recovery', 'indicator_path': self.indicator_engine.storage_path}
                )
                return new_session_id
            elif button_id == 'refresh-page-btn':
                # Trigger a page refresh - handled by clientside callback
                return dash.no_update
            
            return dash.no_update
        
        @self.app.callback(
            [Output('rsi-controls', 'style'),
             Output('ma-controls', 'style'),
             Output('candlestick-controls', 'style'),
             Output('streak-controls', 'style'),
             Output('custom-indicator-controls', 'style')],
            Input('scan-type', 'value')
        )
        def toggle_controls(scan_type):
            """Show/hide controls based on scan type."""
            show = {'display': 'block'}
            hide = {'display': 'none'}
            
            # Default: hide all
            rsi_style = hide
            ma_style = hide
            candlestick_style = hide
            streak_style = hide
            custom_style = hide
            
            # Show relevant controls
            if scan_type in ['rsi_oversold', 'rsi_overbought']:
                rsi_style = show
            elif scan_type in ['ma_cross_bull', 'ma_cross_bear']:
                ma_style = show
            elif scan_type == 'candlestick':
                candlestick_style = show
            elif scan_type == 'momentum_streak':
                streak_style = show
            elif scan_type == 'custom_indicator':
                custom_style = show
            
            return rsi_style, ma_style, candlestick_style, streak_style, custom_style
        
        @self.app.callback(
            Output('custom-indicator', 'options'),
            Input('refresh-symbols-btn', 'n_clicks')
        )
        def populate_indicator_dropdown(n_clicks):
            """Populate the indicator dropdown with available indicators."""
            try:
                available_indicators = self.scanner.get_available_indicators()
                if not available_indicators:
                    return []
                
                # Create options with friendly labels
                options = []
                for indicator in available_indicators:
                    # Create a friendly label
                    label = indicator
                    if indicator.startswith('RSI_'):
                        label = f"RSI ({indicator.split('_')[1]} period)"
                    elif indicator.startswith('SMA_'):
                        label = f"SMA ({indicator.split('_')[1]} period)"
                    elif indicator.startswith('EMA_'):
                        label = f"EMA ({indicator.split('_')[1]} period)"
                    elif indicator == 'consec_higher_high':
                        label = "Consecutive Higher Highs"
                    elif indicator == 'consec_lower_low':
                        label = "Consecutive Lower Lows"
                    elif indicator == 'days_since_prev_high':
                        label = "Days Since Previous High"
                    elif indicator == 'days_since_prev_low':
                        label = "Days Since Previous Low"
                    elif indicator == 'engulfing_bull':
                        label = "Bullish Engulfing Pattern"
                    elif indicator == 'engulfing_bear':
                        label = "Bearish Engulfing Pattern"
                    elif '_' in indicator:
                        # Convert snake_case to Title Case
                        label = indicator.replace('_', ' ').title()
                    
                    options.append({'label': label, 'value': indicator})
                
                return options
            except Exception as e:
                print(f"Error populating indicators: {e}")
                return []
        
        @self.app.callback(
            [Output('scan-results-div', 'children'),
             Output('scan-status', 'children')],
            Input('run-scan-btn', 'n_clicks'),
            [State('scan-type', 'value'),
             State('rsi-period', 'value'),
             State('rsi-threshold', 'value'),
             State('fast-ma', 'value'),
             State('slow-ma', 'value'),
             State('pattern-type', 'value'),
             State('streak-type', 'value'),
             State('streak-threshold', 'value'),
             State('custom-indicator', 'value'),
             State('custom-operator', 'value'),
             State('custom-threshold', 'value'),
             State('session-id-store', 'data')]
        )
        def run_scan(n_clicks, scan_type, rsi_period, rsi_threshold, fast_ma, slow_ma,
                     pattern_type, streak_type, streak_threshold, 
                     custom_indicator, custom_operator, custom_threshold, session_id):
            """Run the selected scan."""
            if n_clicks is None:
                return html.P("Configure scan and click 'Run Scan'"), ""
            
            # Update session activity
            if session_id:
                self.session_manager.update_session_activity(session_id)
            
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
                
                elif scan_type == 'candlestick':
                    # Scan for candlestick pattern (pattern value == 1 indicates pattern detected)
                    PATTERN_PRESENT = 1
                    results = self.scanner.scan_by_indicator(symbols, pattern_type, '==', PATTERN_PRESENT)
                    pattern_name = pattern_type.replace('_', ' ').title()
                    status = f"Found {len(results)} stocks with {pattern_name} pattern"
                
                elif scan_type == 'momentum_streak':
                    # Scan for momentum streaks
                    results = self.scanner.scan_by_indicator(symbols, streak_type, '>=', float(streak_threshold))
                    streak_name = streak_type.replace('_', ' ').title()
                    status = f"Found {len(results)} stocks with {streak_name} >= {streak_threshold} days"
                
                elif scan_type == 'custom_indicator':
                    # Scan with custom indicator filter
                    if custom_indicator is None:
                        return html.P("Please select an indicator"), ""
                    results = self.scanner.scan_by_indicator(
                        symbols, custom_indicator, custom_operator, float(custom_threshold)
                    )
                    status = f"Found {len(results)} stocks where {custom_indicator} {custom_operator} {custom_threshold}"
                
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
                # Record error in session
                if session_id:
                    self.session_manager.record_session_error(
                        session_id,
                        f"Scanner error: {str(e)}"
                    )
                
                # Format user-friendly error message
                from error_handler import get_user_friendly_error
                error_msg = get_user_friendly_error(e)
                
                error_display = dbc.Alert([
                    html.H5("⚠️ Scan Error", className="alert-heading"),
                    html.P(error_msg),
                    html.Hr(),
                    html.P([
                        html.Strong("Suggestions:"),
                        html.Ul([
                            html.Li("Refresh the page to restart your session"),
                            html.Li("Ensure data is properly loaded for the selected symbols"),
                            html.Li("Try a different scan type or parameters"),
                            html.Li("Check the browser console for detailed error information")
                        ])
                    ], className="mb-0 small")
                ], color="danger")
                
                return error_display, html.P("Scan failed", className="text-danger")
        
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
        
        
        # New callbacks for Indicators page
        @self.app.callback(
            [Output('last-computation-date', 'children'),
             Output('symbols-count', 'children'),
             Output('indicator-status-text', 'children'),
             Output('indicator-status-text', 'className'),
             Output('available-indicators-list', 'children')],
            [Input('health-check-interval', 'n_intervals'),
             Input('compute-indicators-btn', 'n_clicks'),
             Input('refresh-symbols-btn', 'n_clicks')]
        )
        def update_indicator_summary(n_intervals, compute_clicks, refresh_clicks):
            """Update the indicator summary panel with current status."""
            from datetime import datetime
            
            try:
                metadata = self.indicator_engine.get_metadata()
                symbols = self.indicator_engine.list_available_symbols()
                symbols_count = len(symbols)
                
                # Format last computation date
                last_computed = metadata.get('last_computation_date')
                if last_computed:
                    try:
                        dt = datetime.fromisoformat(last_computed)
                        date_str = dt.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        date_str = last_computed
                else:
                    date_str = "Not computed yet"
                
                # Determine status
                if symbols_count > 0:
                    status_text = "✅ Ready"
                    status_class = "mb-0 text-success"
                else:
                    status_text = "⚠️ No Data"
                    status_class = "mb-0 text-warning"
                
                # Build available indicators list
                if symbols_count > 0:
                    config = self.indicator_engine.get_config()
                    
                    # Get a sample symbol to see what indicators are available
                    sample_symbol = symbols[0] if symbols else None
                    if sample_symbol and sample_symbol in config:
                        symbol_config = config[sample_symbol]
                        
                        indicators_list = []
                        
                        # SMA
                        if 'sma_periods' in symbol_config:
                            sma_periods = symbol_config['sma_periods']
                            indicators_list.append(
                                html.Li([html.Strong("SMA: "), f"{len(sma_periods)} periods ({', '.join(map(str, sma_periods))})"])
                            )
                        
                        # RSI
                        if 'rsi_periods' in symbol_config:
                            rsi_periods = symbol_config['rsi_periods']
                            indicators_list.append(
                                html.Li([html.Strong("RSI: "), f"{len(rsi_periods)} periods ({', '.join(map(str, rsi_periods))})"])
                            )
                        
                        # EMA
                        if 'ema_periods' in symbol_config:
                            ema_count = len(symbol_config['ema_periods'])
                            indicators_list.append(
                                html.Li([html.Strong("EMA: "), f"{ema_count} periods (2-200, 250-1000 by 50s)"])
                            )
                        
                        # Candlestick patterns
                        if symbol_config.get('candlestick_patterns', False):
                            indicators_list.append(
                                html.Li([html.Strong("Candlestick Patterns: "), "12 patterns (hammer, doji, engulfing, etc.)"])
                            )
                        
                        # Streak indicators
                        if symbol_config.get('streak_indicators', False):
                            indicators_list.append(
                                html.Li([html.Strong("Momentum Streaks: "), "Consecutive higher/lower highs and lows"])
                            )
                        
                        # High/Low days
                        if symbol_config.get('high_low_days', False):
                            indicators_list.append(
                                html.Li([html.Strong("Breakout Tracking: "), "Days since previous high/low"])
                            )
                        
                        indicators_display = html.Div([
                            html.H6("Computed Indicators:", className="mb-2"),
                            html.Ul(indicators_list, className="mb-0")
                        ])
                    else:
                        indicators_display = html.P("No indicator details available.", className="text-muted")
                else:
                    indicators_display = html.P("Compute indicators to see available indicators here.", 
                                               className="text-muted")
                
                return date_str, str(symbols_count), status_text, status_class, indicators_display
                
            except Exception as e:
                return "Error", "0", "❌ Error", "mb-0 text-danger", html.P(f"Error: {str(e)}", className="text-danger")
        
        @self.app.callback(
            [Output('indicator-output', 'children'),
             Output('indicator-computation-alert', 'children'),
             Output('indicator-computation-alert', 'color'),
             Output('indicator-computation-alert', 'is_open')],
            Input('compute-indicators-btn', 'n_clicks'),
            prevent_initial_call=True
        )
        def compute_indicators(n_clicks):
            """Compute indicators from price data."""
            if n_clicks is None:
                return "", "", "info", False
            
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
                    return (
                        html.Div([
                            html.P("❌ No price data directory found.", className="text-danger mb-1"),
                            html.P("Expected directories: data/prices/ or data/stock_data/", 
                                   className="text-muted small")
                        ]),
                        "Price data directory not found. Please ensure Parquet files exist in data/prices/ or data/stock_data/",
                        "danger",
                        True
                    )
                
                # Load data
                loader = DataLoader(data_path)
                symbols = loader.list_available_symbols()
                
                if not symbols:
                    return (
                        html.Div([
                            html.P("❌ No Parquet files found in data directory.", className="text-danger mb-1"),
                            html.P(f"Location: {data_path}", className="text-muted small")
                        ]),
                        f"No Parquet files found in {data_path}. Please add price data files.",
                        "danger",
                        True
                    )
                
                # Show progress
                output_msg = html.Div([
                    html.P(f"⏳ Processing {len(symbols)} symbols from {data_path}...", 
                           className="mb-1 text-info"),
                    html.P("Computing indicators: SMA, RSI, EMA, candlestick patterns, momentum streaks...", 
                           className="text-muted small")
                ])
                
                # Load data
                data_dict = loader.load_multiple_symbols(symbols)
                
                if not data_dict:
                    return (
                        html.Div([
                            html.P("❌ Failed to load any symbols.", className="text-danger mb-1"),
                            html.P("Check that Parquet files have correct OHLCV columns.", 
                                   className="text-muted small")
                        ]),
                        "Failed to load symbols. Check that Parquet files have correct OHLCV columns.",
                        "danger",
                        True
                    )
                
                # Compute indicators
                self.indicator_engine.process_multiple_symbols(
                    data_dict,
                    sma_periods=[20, 50, 200],
                    rsi_periods=[7, 14, 21, 28],
                    show_progress=False  # Disable progress bar in UI
                )
                
                # Verify results
                available = self.indicator_engine.list_available_symbols()
                
                return (
                    html.Div([
                        html.P("✅ Indicators computed successfully!", className="text-success fw-bold mb-2"),
                        html.Ul([
                            html.Li(f"Processed {len(available)} symbols"),
                            html.Li("Computed SMA (20, 50, 200 periods)"),
                            html.Li("Computed RSI (7, 14, 21, 28 periods)"),
                            html.Li("Computed 215 EMA periods (2-200, 250-1000 by 50s)"),
                            html.Li("Detected 12 candlestick patterns"),
                            html.Li("Computed momentum streak indicators"),
                            html.Li("Tracked breakout indicators (days since high/low)")
                        ], className="mb-2"),
                        html.P([
                            "✅ You can now use the ",
                            html.Strong("Backtest"),
                            " and ",
                            html.Strong("Scanner"),
                            " pages."
                        ], className="text-success small mb-0")
                    ]),
                    f"Successfully computed indicators for {len(available)} symbols!",
                    "success",
                    True
                )
            
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                return (
                    html.Div([
                        html.P(f"❌ Error: {str(e)}", className="text-danger mb-1"),
                        html.Details([
                            html.Summary("Show details", className="small text-muted"),
                            html.Pre(error_details, className="small bg-light p-2 mt-2")
                        ])
                    ]),
                    f"Error computing indicators: {str(e)}",
                    "danger",
                    True
                )
        
        @self.app.callback(
            [Output('backtest-details-div', 'children'),
             Output('backtest-status', 'children')],
            Input('run-backtest-btn', 'n_clicks'),
            [State('backtest-symbol', 'value'),
             State('backtest-strategy', 'value'),
             State('backtest-params', 'value')]
        )
        def run_manual_backtest(n_clicks, symbol, strategy, params_json):
            """Run a manual backtest for selected symbol/strategy/params."""
            if n_clicks is None or not symbol:
                return html.Div(), ""
            
            try:
                # Parse parameters
                import json
                if params_json:
                    try:
                        params = json.loads(params_json)
                    except json.JSONDecodeError:
                        return html.Div(), html.Div("Invalid JSON parameters", className="text-danger")
                else:
                    # Use default params based on strategy
                    if strategy == 'rsi_meanrev':
                        params = {'rsi_period': 14, 'oversold': 30, 'overbought': 70}
                    else:
                        params = {'fast_period': 20, 'slow_period': 50}
                
                # Run backtest
                result = self.backtest_engine.run_single_backtest(
                    symbol=symbol,
                    strategy_name=strategy,
                    params=params
                )
                
                # Create metrics display
                metrics = result['metrics']
                
                metrics_cards = dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Win Rate", className="text-muted"),
                                html.H4(f"{metrics['win_rate']*100:.1f}%")
                            ])
                        ], className="mb-2")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Num Trades", className="text-muted"),
                                html.H4(f"{metrics['num_trades']}")
                            ])
                        ], className="mb-2")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Sharpe Ratio", className="text-muted"),
                                html.H4(f"{metrics['sharpe_ratio']:.2f}")
                            ])
                        ], className="mb-2")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("CAGR", className="text-muted"),
                                html.H4(f"{metrics['cagr']*100:.1f}%")
                            ])
                        ], className="mb-2")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Max Drawdown", className="text-muted"),
                                html.H4(f"{metrics['max_drawdown']*100:.1f}%", className="text-danger")
                            ])
                        ], className="mb-2")
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Total Return", className="text-muted"),
                                html.H4(f"{metrics['total_return']*100:.1f}%")
                            ])
                        ], className="mb-2")
                    ], width=4)
                ])
                
                # Create equity curve chart
                equity_chart = go.Figure()
                equity_chart.add_trace(go.Scatter(
                    y=result['equity'],
                    mode='lines',
                    name='Equity',
                    line=dict(color='blue', width=2)
                ))
                equity_chart.update_layout(
                    title=f"Equity Curve - {symbol} ({strategy})",
                    xaxis_title="Days",
                    yaxis_title="Portfolio Value ($)",
                    height=400,
                    hovermode='x unified'
                )
                
                details = html.Div([
                    html.H5(f"Backtest Results: {symbol}"),
                    html.Hr(),
                    metrics_cards,
                    html.Hr(),
                    dcc.Graph(figure=equity_chart)
                ])
                
                status = html.Div(
                    f"✓ Backtest completed for {symbol} with {strategy}",
                    className="text-success"
                )
                
                return details, status
                
            except Exception as e:
                import traceback
                error_msg = html.Div([
                    html.P(f"Error running backtest: {str(e)}", className="text-danger"),
                    html.Pre(traceback.format_exc(), style={'fontSize': '0.8em'})
                ])
                return error_msg, html.Div(f"✗ Error: {str(e)}", className="text-danger")
    
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
