"""
Backtest Manager Portal
========================
Advanced batch backtesting UI with multi-select, grouped results, and exports.

Features:
- Multi-select strategies and symbols
- Batch execution with progress tracking
- Grouped results (by strategy/symbol)
- Professional trade breakdowns
- CSV/XLSX export
- Group set management
- Session management and error handling
"""

import json
import io
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

from backtest_engine import BacktestEngine
from strategy import StrategyConfig, StrategyRegistry
from indicator_engine import IndicatorEngine
from error_handler import safe_execute, get_user_friendly_error


class BacktestManagerUI:
    """
    Advanced Backtest Manager UI component for Dash application.
    """
    
    def __init__(
        self,
        indicator_engine: IndicatorEngine,
        backtest_engine: BacktestEngine,
        session_manager=None
    ):
        """
        Initialize the Backtest Manager UI.
        
        Args:
            indicator_engine: IndicatorEngine instance
            backtest_engine: BacktestEngine instance
            session_manager: Optional SessionManager instance
        """
        self.indicator_engine = indicator_engine
        self.backtest_engine = backtest_engine
        self.session_manager = session_manager
        self.strategy_registry = StrategyRegistry()
        
        # Available strategies with default configurations
        self.available_strategies = {
            'rsi_meanrev': {
                'name': 'RSI Mean Reversion',
                'params': [
                    {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
                    {'rsi_period': 14, 'oversold': 20, 'overbought': 80},
                    {'rsi_period': 21, 'oversold': 30, 'overbought': 70}
                ]
            },
            'ma_crossover': {
                'name': 'MA Crossover',
                'params': [
                    {'fast_period': 20, 'slow_period': 50},
                    {'fast_period': 50, 'slow_period': 200},
                    {'fast_period': 10, 'slow_period': 30}
                ]
            }
        }
    
    def create_layout(self) -> dbc.Container:
        """
        Create the Backtest Manager UI layout.
        
        Returns:
            Dash layout component
        """
        return dbc.Container([
            html.H2("🚀 Backtest Manager Portal", className="mb-4"),
            
            # Configuration Section
            dbc.Row([
                # Strategy Selection
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Strategy Selection"),
                        dbc.CardBody([
                            html.Label("Select Strategies:", className="fw-bold"),
                            dcc.Checklist(
                                id='batch-strategy-checklist',
                                options=[
                                    {'label': self.available_strategies[k]['name'], 'value': k}
                                    for k in self.available_strategies.keys()
                                ],
                                value=[],
                                className="mb-3"
                            ),
                            dbc.ButtonGroup([
                                dbc.Button("Select All", id='select-all-strategies-btn', 
                                         size="sm", color="secondary", outline=True),
                                dbc.Button("Clear", id='clear-strategies-btn', 
                                         size="sm", color="secondary", outline=True)
                            ], className="mb-3"),
                            html.Hr(),
                            html.Label("Parameter Sets:", className="fw-bold"),
                            html.Div(id='strategy-params-display', className="small text-muted")
                        ])
                    ])
                ], width=4),
                
                # Symbol Selection
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 Symbol Selection"),
                        dbc.CardBody([
                            html.Label("Search & Select Symbols:", className="fw-bold"),
                            dcc.Input(
                                id='symbol-search-input',
                                type='text',
                                placeholder='Search symbols...',
                                className="form-control mb-2"
                            ),
                            html.Div(
                                id='symbol-checklist-container',
                                style={'maxHeight': '300px', 'overflowY': 'auto'},
                                className="mb-3"
                            ),
                            dbc.ButtonGroup([
                                dbc.Button("Select All", id='select-all-symbols-btn', 
                                         size="sm", color="secondary", outline=True),
                                dbc.Button("Clear", id='clear-symbols-btn', 
                                         size="sm", color="secondary", outline=True)
                            ], className="mb-2"),
                            html.Hr(),
                            html.Label("Bulk Import:", className="fw-bold"),
                            dcc.Textarea(
                                id='bulk-symbol-input',
                                placeholder='Paste symbols (comma or newline separated)',
                                style={'height': '80px'},
                                className="form-control mb-2"
                            ),
                            dbc.Button("Import Symbols", id='import-symbols-btn',
                                     size="sm", color="info", outline=True)
                        ])
                    ])
                ], width=4),
                
                # Execution Controls
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⚙️ Execution Controls"),
                        dbc.CardBody([
                            html.Label("Exit Rules:", className="fw-bold"),
                            dcc.Checklist(
                                id='exit-rules-checklist',
                                options=[
                                    {'label': 'Default', 'value': 'default'},
                                    {'label': 'Trailing Stop', 'value': 'trailing_stop'},
                                    {'label': 'Profit Target', 'value': 'profit_target'}
                                ],
                                value=['default'],
                                className="mb-3"
                            ),
                            html.Hr(),
                            html.Label("Job Summary:", className="fw-bold"),
                            html.Div(id='job-summary-display', className="mb-3 p-2 bg-light rounded"),
                            html.Hr(),
                            dbc.Button(
                                "🚀 Launch Batch Backtest",
                                id='launch-batch-btn',
                                color="success",
                                size="lg",
                                className="w-100 mb-2"
                            ),
                            dbc.Progress(
                                id='batch-progress-bar',
                                value=0,
                                className="mb-2",
                                style={'display': 'none'}
                            ),
                            html.Div(id='batch-status-display', className="small")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Group Set Management
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💾 Group Set Management"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Input(
                                        id='group-set-name-input',
                                        type='text',
                                        placeholder='Group set name (e.g., My S&P500 Momentum)',
                                        className="form-control"
                                    )
                                ], width=8),
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button("Save", id='save-group-set-btn', 
                                                 color="primary", size="sm"),
                                        dbc.Button("Load", id='load-group-set-btn', 
                                                 color="secondary", size="sm")
                                    ], className="w-100")
                                ], width=4)
                            ]),
                            html.Div(id='group-set-status', className="mt-2 small")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Results Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            dbc.Row([
                                dbc.Col([
                                    html.H5("📊 Backtest Results", className="mb-0")
                                ], width=6),
                                dbc.Col([
                                    dbc.ButtonGroup([
                                        dbc.Button("By Strategy", id='view-by-strategy-btn',
                                                 color="primary", size="sm", outline=True),
                                        dbc.Button("By Symbol", id='view-by-symbol-btn',
                                                 color="primary", size="sm", outline=True),
                                        dbc.Button("Export CSV", id='export-csv-btn',
                                                 color="success", size="sm", outline=True),
                                        dbc.Button("Export XLSX", id='export-xlsx-btn',
                                                 color="success", size="sm", outline=True)
                                    ], className="float-end")
                                ], width=6)
                            ], align="center")
                        ]),
                        dbc.CardBody([
                            dcc.Loading(
                                id='results-loading',
                                children=html.Div(id='results-display'),
                                type='default'
                            )
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Trade Details Modal
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(id='trade-modal-title')),
                dbc.ModalBody(id='trade-modal-body'),
                dbc.ModalFooter(
                    dbc.Button("Close", id='close-trade-modal-btn', className="ml-auto")
                )
            ], id='trade-details-modal', size='xl', scrollable=True),
            
            # Hidden stores for state management
            dcc.Store(id='batch-results-store'),
            dcc.Store(id='current-view-mode', data='strategy'),
            dcc.Store(id='selected-backtest-data'),
            dcc.Download(id='download-results'),
            dcc.Download(id='download-trades')
        ], fluid=True)
    
    def setup_callbacks(self, app):
        """
        Setup all callbacks for the Backtest Manager UI.
        
        Args:
            app: Dash app instance
        """
        
        @app.callback(
            Output('symbol-checklist-container', 'children'),
            [Input('symbol-search-input', 'value'),
             Input('import-symbols-btn', 'n_clicks')],
            [State('bulk-symbol-input', 'value')]
        )
        def update_symbol_checklist(search_term, import_clicks, bulk_input):
            """Update symbol checklist based on search and bulk import."""
            ctx = callback_context
            
            # Get available symbols
            all_symbols = self.indicator_engine.list_available_symbols()
            
            if not all_symbols:
                return html.P("No symbols available. Please compute indicators first.",
                            className="text-warning")
            
            # Handle bulk import
            if ctx.triggered and ctx.triggered[0]['prop_id'] == 'import-symbols-btn.n_clicks':
                if bulk_input:
                    # Parse bulk input
                    imported_symbols = []
                    for line in bulk_input.replace(',', '\n').split('\n'):
                        symbol = line.strip().upper()
                        if symbol and symbol in all_symbols:
                            imported_symbols.append(symbol)
                    
                    # Filter to imported symbols
                    all_symbols = imported_symbols
            
            # Apply search filter
            if search_term:
                search_term = search_term.upper()
                all_symbols = [s for s in all_symbols if search_term in s]
            
            # Create checklist
            return dcc.Checklist(
                id='batch-symbol-checklist',
                options=[{'label': s, 'value': s} for s in sorted(all_symbols)],
                value=[],
                className="small"
            )
        
        @app.callback(
            Output('batch-symbol-checklist', 'value'),
            [Input('select-all-symbols-btn', 'n_clicks'),
             Input('clear-symbols-btn', 'n_clicks')],
            [State('batch-symbol-checklist', 'options')]
        )
        def toggle_symbol_selection(select_all, clear, options):
            """Toggle symbol selection."""
            ctx = callback_context
            if not ctx.triggered or not options:
                return []
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'select-all-symbols-btn':
                return [opt['value'] for opt in options]
            elif button_id == 'clear-symbols-btn':
                return []
            
            return []
        
        @app.callback(
            Output('batch-strategy-checklist', 'value'),
            [Input('select-all-strategies-btn', 'n_clicks'),
             Input('clear-strategies-btn', 'n_clicks')],
            [State('batch-strategy-checklist', 'options')]
        )
        def toggle_strategy_selection(select_all, clear, options):
            """Toggle strategy selection."""
            ctx = callback_context
            if not ctx.triggered or not options:
                return []
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'select-all-strategies-btn':
                return [opt['value'] for opt in options]
            elif button_id == 'clear-strategies-btn':
                return []
            
            return []
        
        @app.callback(
            Output('strategy-params-display', 'children'),
            Input('batch-strategy-checklist', 'value')
        )
        def display_strategy_params(selected_strategies):
            """Display parameter sets for selected strategies."""
            if not selected_strategies:
                return html.P("No strategies selected", className="text-muted small")
            
            params_display = []
            for strategy_id in selected_strategies:
                strategy_info = self.available_strategies.get(strategy_id, {})
                params_list = strategy_info.get('params', [])
                
                params_display.append(
                    html.Div([
                        html.Strong(f"{strategy_info.get('name', strategy_id)}:"),
                        html.Ul([
                            html.Li(str(params)) for params in params_list
                        ], className="mb-2")
                    ])
                )
            
            return params_display
        
        @app.callback(
            Output('job-summary-display', 'children'),
            [Input('batch-strategy-checklist', 'value'),
             Input('batch-symbol-checklist', 'value'),
             Input('exit-rules-checklist', 'value')]
        )
        def update_job_summary(strategies, symbols, exit_rules):
            """Update job summary statistics."""
            if not strategies or not symbols or not exit_rules:
                return html.P("Configure selections to see job summary", 
                            className="text-muted small")
            
            # Calculate total jobs
            total_param_sets = sum(
                len(self.available_strategies.get(s, {}).get('params', []))
                for s in strategies
            )
            total_jobs = len(symbols) * total_param_sets * len(exit_rules)
            
            return html.Div([
                html.P([html.Strong("Strategies: "), f"{len(strategies)} ({total_param_sets} param sets)"], 
                      className="mb-1 small"),
                html.P([html.Strong("Symbols: "), f"{len(symbols)}"], 
                      className="mb-1 small"),
                html.P([html.Strong("Exit Rules: "), f"{len(exit_rules)}"], 
                      className="mb-1 small"),
                html.Hr(className="my-2"),
                html.P([html.Strong("Total Jobs: "), html.Span(f"{total_jobs}", 
                      className="badge bg-primary")], className="mb-0")
            ])
        
        @app.callback(
            [Output('batch-results-store', 'data'),
             Output('batch-progress-bar', 'value'),
             Output('batch-progress-bar', 'style'),
             Output('batch-status-display', 'children')],
            Input('launch-batch-btn', 'n_clicks'),
            [State('batch-strategy-checklist', 'value'),
             State('batch-symbol-checklist', 'value'),
             State('exit-rules-checklist', 'value'),
             State('session-id-store', 'data')],
            prevent_initial_call=True
        )
        def launch_batch_backtest(n_clicks, strategies, symbols, exit_rules, session_id):
            """Launch batch backtest execution."""
            if not n_clicks or not strategies or not symbols:
                return None, 0, {'display': 'none'}, ""
            
            # Update session activity
            if self.session_manager and session_id:
                self.session_manager.update_session_activity(session_id)
            
            try:
                # Prepare strategy configurations
                strategy_configs = []
                for strategy_id in strategies:
                    strategy_info = self.available_strategies.get(strategy_id, {})
                    params_list = strategy_info.get('params', [])
                    
                    for params in params_list:
                        strategy_configs.append(
                            StrategyConfig(name=strategy_id, params=params)
                        )
                
                # Progress tracking
                progress_messages = []
                
                def progress_callback(current, total, message):
                    progress_messages.append(message)
                
                # Run batch backtests with error handling
                success, result, error_msg = safe_execute(
                    self.backtest_engine.run_batch_backtests,
                    symbols=symbols,
                    strategy_configs=strategy_configs,
                    exit_rules=exit_rules if exit_rules else ['default'],
                    progress_callback=progress_callback,
                    error_message="Batch backtest execution failed"
                )
                
                if not success:
                    # Record error in session
                    if self.session_manager and session_id:
                        self.session_manager.record_session_error(
                            session_id,
                            f"Batch backtest error: {error_msg}"
                        )
                    
                    # Return error status
                    status_msg = dbc.Alert([
                        html.P("❌ Batch backtest failed!", className="text-danger fw-bold"),
                        html.P(error_msg or "Unknown error occurred"),
                        html.Hr(),
                        html.Small([
                            html.Strong("Recovery steps:"),
                            html.Ul([
                                html.Li("Verify data is loaded for selected symbols"),
                                html.Li("Try with fewer symbols or strategies"),
                                html.Li("Check system resources and refresh if needed"),
                                html.Li("Review browser console for detailed errors")
                            ])
                        ])
                    ], color="danger")
                    
                    return None, 0, {'display': 'none'}, status_msg
                
                # Success - unpack results
                results_df, job_stats = result
                
                # Add view trades action column to results
                if len(results_df) > 0:
                    results_df['view_trades_action'] = '**[📊 View Details]**'
                
                # Store results
                results_data = results_df.to_dict('records') if len(results_df) > 0 else []
                
                # Create status message
                status_msg = html.Div([
                    html.P(f"✅ Batch backtest completed!", className="text-success fw-bold"),
                    html.P(f"Total: {job_stats['total_jobs']} | "
                          f"Completed: {job_stats['completed']} | "
                          f"Errors: {job_stats['errors']}", className="small mb-0")
                ])
                
                return results_data, 100, {'display': 'block'}, status_msg
                
            except Exception as e:
                # Fallback error handling
                error_msg = get_user_friendly_error(e)
                
                if self.session_manager and session_id:
                    self.session_manager.record_session_error(
                        session_id,
                        f"Batch backtest exception: {str(e)}"
                    )
                
                status_msg = dbc.Alert([
                    html.P("❌ Unexpected error occurred!", className="fw-bold"),
                    html.P(error_msg)
                ], color="danger")
                
                return None, 0, {'display': 'none'}, status_msg
        
        @app.callback(
            Output('current-view-mode', 'data'),
            [Input('view-by-strategy-btn', 'n_clicks'),
             Input('view-by-symbol-btn', 'n_clicks')]
        )
        def toggle_view_mode(by_strategy_clicks, by_symbol_clicks):
            """Toggle between strategy and symbol view modes."""
            ctx = callback_context
            if not ctx.triggered:
                return 'strategy'
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'view-by-strategy-btn':
                return 'strategy'
            elif button_id == 'view-by-symbol-btn':
                return 'symbol'
            
            return 'strategy'
        
        @app.callback(
            Output('results-display', 'children'),
            [Input('batch-results-store', 'data'),
             Input('current-view-mode', 'data')]
        )
        def display_results(results_data, view_mode):
            """Display backtest results in grouped tables."""
            if not results_data:
                return html.P("No results yet. Configure and launch a batch backtest.", 
                            className="text-muted")
            
            results_df = pd.DataFrame(results_data)
            
            if len(results_df) == 0:
                return html.P("No successful backtests in this batch.", 
                            className="text-warning")
            
            # Group by strategy or symbol
            if view_mode == 'strategy':
                return self._create_strategy_grouped_view(results_df)
            else:
                return self._create_symbol_grouped_view(results_df)
        
        @app.callback(
            [Output('download-results', 'data'),
             Output('download-results', 'filename')],
            [Input('export-csv-btn', 'n_clicks'),
             Input('export-xlsx-btn', 'n_clicks')],
            [State('batch-results-store', 'data')],
            prevent_initial_call=True
        )
        def export_results(csv_clicks, xlsx_clicks, results_data):
            """Export results to CSV or XLSX."""
            ctx = callback_context
            if not ctx.triggered or not results_data:
                return None, None
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            results_df = pd.DataFrame(results_data)
            
            if button_id == 'export-csv-btn':
                return dcc.send_data_frame(results_df.to_csv, "backtest_results.csv", index=False)
            elif button_id == 'export-xlsx-btn':
                return dcc.send_data_frame(results_df.to_excel, "backtest_results.xlsx", index=False)
            
            return None, None
        
        @app.callback(
            Output('group-set-status', 'children'),
            [Input('save-group-set-btn', 'n_clicks'),
             Input('load-group-set-btn', 'n_clicks')],
            [State('group-set-name-input', 'value'),
             State('batch-strategy-checklist', 'value'),
             State('batch-symbol-checklist', 'value'),
             State('exit-rules-checklist', 'value')],
            prevent_initial_call=True
        )
        def manage_group_sets(save_clicks, load_clicks, group_name, strategies, symbols, exit_rules):
            """Save or load group sets."""
            ctx = callback_context
            if not ctx.triggered or not group_name:
                return html.P("Enter a group set name", className="text-muted")
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if button_id == 'save-group-set-btn':
                if not strategies or not symbols:
                    return html.P("⚠️ Select strategies and symbols to save", 
                                className="text-warning")
                
                # Prepare params list
                params_list = []
                for strategy_id in strategies:
                    strategy_info = self.available_strategies.get(strategy_id, {})
                    params_list.extend(strategy_info.get('params', []))
                
                # Save to store
                self.backtest_engine.store.save_group_set(
                    name=group_name,
                    symbols=symbols,
                    strategies=strategies,
                    params_list=params_list,
                    exit_rules=exit_rules if exit_rules else ['default']
                )
                
                return html.P(f"✅ Group set '{group_name}' saved successfully", 
                            className="text-success")
            
            elif button_id == 'load-group-set-btn':
                group_data = self.backtest_engine.store.load_group_set(group_name)
                
                if not group_data:
                    return html.P(f"⚠️ Group set '{group_name}' not found", 
                                className="text-warning")
                
                return html.P(f"✅ Group set '{group_name}' loaded successfully", 
                            className="text-success")
            
            return ""
        
        @app.callback(
            [Output('trade-details-modal', 'is_open'),
             Output('trade-modal-title', 'children'),
             Output('trade-modal-body', 'children')],
            [Input({'type': 'results-table', 'strategy': dash.ALL}, 'active_cell'),
             Input({'type': 'results-table', 'symbol': dash.ALL}, 'active_cell'),
             Input('close-trade-modal-btn', 'n_clicks')],
            [State({'type': 'results-table', 'strategy': dash.ALL}, 'data'),
             State({'type': 'results-table', 'symbol': dash.ALL}, 'data'),
             State('trade-details-modal', 'is_open')]
        )
        def show_trade_details(strategy_active_cells, symbol_active_cells, close_clicks, 
                              strategy_data_list, symbol_data_list, is_open):
            """Display trade-by-trade details when a row is clicked."""
            ctx = callback_context
            
            if not ctx.triggered:
                return False, "", ""
            
            trigger_id = ctx.triggered[0]['prop_id']
            
            # Close button clicked
            if 'close-trade-modal-btn' in trigger_id:
                return False, "", ""
            
            # Find which table was clicked
            clicked_row_data = None
            
            # Check strategy tables
            for i, active_cell in enumerate(strategy_active_cells or []):
                if active_cell and strategy_data_list and i < len(strategy_data_list):
                    data = strategy_data_list[i]
                    if data and active_cell['row'] < len(data):
                        clicked_row_data = data[active_cell['row']]
                        break
            
            # Check symbol tables if not found
            if not clicked_row_data:
                for i, active_cell in enumerate(symbol_active_cells or []):
                    if active_cell and symbol_data_list and i < len(symbol_data_list):
                        data = symbol_data_list[i]
                        if data and active_cell['row'] < len(data):
                            clicked_row_data = data[active_cell['row']]
                            break
            
            if not clicked_row_data:
                return False, "", ""
            
            # Extract backtest identifiers
            symbol = clicked_row_data.get('symbol', '')
            strategy = clicked_row_data.get('strategy', '')
            params = clicked_row_data.get('params', {})
            exit_rule = clicked_row_data.get('exit_rule', 'default')
            
            # Get detailed results from store
            detailed_results = self.backtest_engine.store.get_detailed_results(
                symbol=symbol,
                strategy=strategy,
                params=params,
                exit_rule=exit_rule
            )
            
            if not detailed_results:
                return True, "⚠️ Trade Details Not Available", html.P(
                    "Unable to load trade details for this backtest.",
                    className="text-warning"
                )
            
            # Create modal content
            modal_title = f"📊 Trade Details: {symbol} - {strategy} ({exit_rule})"
            modal_body = self._create_trade_details_view(detailed_results)
            
            return True, modal_title, modal_body
        
        @app.callback(
            Output('download-trades', 'data'),
            Input({'type': 'export-trades-btn', 'index': dash.ALL}, 'n_clicks'),
            State('selected-backtest-data', 'data'),
            prevent_initial_call=True
        )
        def export_trades(n_clicks, backtest_data):
            """Export trade details to CSV."""
            if not any(n_clicks) or not backtest_data:
                return None
            
            trades_df = pd.DataFrame(backtest_data.get('trades', []))
            
            if trades_df.empty:
                return None
            
            return dcc.send_data_frame(
                trades_df.to_csv,
                f"trades_{backtest_data['symbol']}_{backtest_data['strategy']}.csv",
                index=False
            )
    
    def _create_strategy_grouped_view(self, results_df: pd.DataFrame) -> html.Div:
        """Create strategy-grouped results view."""
        grouped_tables = []
        
        for strategy in results_df['strategy'].unique():
            strategy_df = results_df[results_df['strategy'] == strategy]
            
            # Calculate summary stats
            avg_win_rate = strategy_df['win_rate'].mean()
            avg_sharpe = strategy_df['sharpe_ratio'].mean()
            avg_cagr = strategy_df['cagr'].mean()
            total_trades = strategy_df['num_trades'].sum()
            
            grouped_tables.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5(f"📊 {strategy}", className="mb-0 d-inline"),
                        html.Span([
                            f" | Avg Win Rate: {avg_win_rate*100:.1f}% | ",
                            f"Avg Sharpe: {avg_sharpe:.2f} | ",
                            f"Avg CAGR: {avg_cagr*100:.1f}% | ",
                            f"Total Trades: {total_trades}"
                        ], className="small text-muted ms-3")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.P("💡 Click any row or use the '👁️ View Trades' button to see detailed trade-by-trade results", 
                                   className="text-muted small mb-2"),
                            dash_table.DataTable(
                                id={'type': 'results-table', 'strategy': strategy},
                                data=strategy_df.to_dict('records'),
                                columns=[
                                    {'name': 'Symbol', 'id': 'symbol'},
                                    {'name': 'Params', 'id': 'params_str'},
                                    {'name': 'Exit', 'id': 'exit_rule'},
                                    {'name': 'Win Rate', 'id': 'win_rate', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Trades', 'id': 'num_trades'},
                                    {'name': 'CAGR', 'id': 'cagr', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Sharpe', 'id': 'sharpe_ratio', 'type': 'numeric',
                                     'format': {'specifier': '.2f'}},
                                    {'name': 'Max DD', 'id': 'max_drawdown', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Total Ret', 'id': 'total_return', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': '👁️ View Trades', 'id': 'view_trades_action', 
                                     'presentation': 'markdown'}
                                ],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px',
                                    'fontSize': '14px',
                                    'minWidth': '80px',
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'view_trades_action'},
                                        'textAlign': 'center',
                                        'width': '120px',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#e8f4f8',
                                        'fontWeight': 'bold',
                                        'color': '#0066cc'
                                    }
                                ],
                                style_header={
                                    'backgroundColor': '#2c3e50',
                                    'color': 'white',
                                    'fontWeight': 'bold',
                                    'fontSize': '13px',
                                    'textAlign': 'center',
                                    'border': '1px solid #34495e'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    },
                                    {
                                        'if': {'row_index': 'even'},
                                        'backgroundColor': '#ffffff'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{sharpe_ratio} > 1',
                                            'column_id': 'sharpe_ratio'
                                        },
                                        'backgroundColor': '#d4edda',
                                        'color': '#155724',
                                        'fontWeight': '600'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{win_rate} > 0.6',
                                            'column_id': 'win_rate'
                                        },
                                        'backgroundColor': '#d4edda',
                                        'color': '#155724',
                                        'fontWeight': '600'
                                    },
                                    {
                                        'if': {'state': 'active'},
                                        'backgroundColor': '#d1ecf1',
                                        'border': '2px solid #0066cc'
                                    }
                                ],
                                sort_action='native',
                                filter_action='native',
                                page_size=20,
                                tooltip_data=[
                                    {
                                        'view_trades_action': {'value': 'Click to view detailed trade-by-trade results', 'type': 'text'}
                                    } for _ in range(len(strategy_df))
                                ],
                                tooltip_duration=None,
                                css=[{
                                    'selector': '.dash-table-tooltip',
                                    'rule': 'background-color: #2c3e50; color: white; font-size: 12px; padding: 8px; border-radius: 4px;'
                                }]
                            )
                        ])
                    ])
                ], className="mb-3")
            )
        
        return html.Div(grouped_tables)
    
    def _create_symbol_grouped_view(self, results_df: pd.DataFrame) -> html.Div:
        """Create symbol-grouped results view."""
        grouped_tables = []
        
        for symbol in results_df['symbol'].unique():
            symbol_df = results_df[results_df['symbol'] == symbol]
            
            # Calculate summary stats
            avg_win_rate = symbol_df['win_rate'].mean()
            avg_sharpe = symbol_df['sharpe_ratio'].mean()
            avg_cagr = symbol_df['cagr'].mean()
            total_trades = symbol_df['num_trades'].sum()
            
            grouped_tables.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5(f"📈 {symbol}", className="mb-0 d-inline"),
                        html.Span([
                            f" | Avg Win Rate: {avg_win_rate*100:.1f}% | ",
                            f"Avg Sharpe: {avg_sharpe:.2f} | ",
                            f"Avg CAGR: {avg_cagr*100:.1f}% | ",
                            f"Total Trades: {total_trades}"
                        ], className="small text-muted ms-3")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.P("💡 Click any row or use the '👁️ View Trades' button to see detailed trade-by-trade results", 
                                   className="text-muted small mb-2"),
                            dash_table.DataTable(
                                id={'type': 'results-table', 'symbol': symbol},
                                data=symbol_df.to_dict('records'),
                                columns=[
                                    {'name': 'Strategy', 'id': 'strategy'},
                                    {'name': 'Params', 'id': 'params_str'},
                                    {'name': 'Exit', 'id': 'exit_rule'},
                                    {'name': 'Win Rate', 'id': 'win_rate', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Trades', 'id': 'num_trades'},
                                    {'name': 'CAGR', 'id': 'cagr', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Sharpe', 'id': 'sharpe_ratio', 'type': 'numeric',
                                     'format': {'specifier': '.2f'}},
                                    {'name': 'Max DD', 'id': 'max_drawdown', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': 'Total Ret', 'id': 'total_return', 'type': 'numeric',
                                     'format': {'specifier': '.1%'}},
                                    {'name': '👁️ View Trades', 'id': 'view_trades_action', 
                                     'presentation': 'markdown'}
                                ],
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'padding': '10px',
                                    'fontSize': '14px',
                                    'minWidth': '80px',
                                },
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'view_trades_action'},
                                        'textAlign': 'center',
                                        'width': '120px',
                                        'cursor': 'pointer',
                                        'backgroundColor': '#e8f4f8',
                                        'fontWeight': 'bold',
                                        'color': '#0066cc'
                                    }
                                ],
                                style_header={
                                    'backgroundColor': '#2c3e50',
                                    'color': 'white',
                                    'fontWeight': 'bold',
                                    'fontSize': '13px',
                                    'textAlign': 'center',
                                    'border': '1px solid #34495e'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': '#f8f9fa'
                                    },
                                    {
                                        'if': {'row_index': 'even'},
                                        'backgroundColor': '#ffffff'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{sharpe_ratio} > 1',
                                            'column_id': 'sharpe_ratio'
                                        },
                                        'backgroundColor': '#d4edda',
                                        'color': '#155724',
                                        'fontWeight': '600'
                                    },
                                    {
                                        'if': {
                                            'filter_query': '{win_rate} > 0.6',
                                            'column_id': 'win_rate'
                                        },
                                        'backgroundColor': '#d4edda',
                                        'color': '#155724',
                                        'fontWeight': '600'
                                    },
                                    {
                                        'if': {'state': 'active'},
                                        'backgroundColor': '#d1ecf1',
                                        'border': '2px solid #0066cc'
                                    }
                                ],
                                sort_action='native',
                                filter_action='native',
                                page_size=20,
                                tooltip_data=[
                                    {
                                        'view_trades_action': {'value': 'Click to view detailed trade-by-trade results', 'type': 'text'}
                                    } for _ in range(len(symbol_df))
                                ],
                                tooltip_duration=None,
                                css=[{
                                    'selector': '.dash-table-tooltip',
                                    'rule': 'background-color: #2c3e50; color: white; font-size: 12px; padding: 8px; border-radius: 4px;'
                                }]
                            )
                        ])
                    ])
                ], className="mb-3")
            )
        
        return html.Div(grouped_tables)
    
    def _create_trade_details_view(self, detailed_results: Dict) -> html.Div:
        """Create comprehensive trade-by-trade details view with summary metrics and visualizations."""
        metrics = detailed_results.get('metrics', {})
        trades = detailed_results.get('trades')
        equity_curve = detailed_results.get('equity_curve')
        dates = detailed_results.get('dates', [])
        
        # Convert trades to DataFrame if it isn't already
        if trades is not None and not isinstance(trades, pd.DataFrame):
            trades_df = pd.DataFrame(trades)
        else:
            trades_df = trades
        
        # Summary metrics section
        summary_section = dbc.Card([
            dbc.CardHeader(html.H5("📈 Summary Metrics", className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.P([
                            html.Strong("Win Rate: "),
                            f"{metrics.get('win_rate', 0)*100:.2f}%"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Total Trades: "),
                            f"{metrics.get('num_trades', 0)}"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("CAGR: "),
                            f"{metrics.get('cagr', 0)*100:.2f}%"
                        ], className="mb-2")
                    ], md=3),
                    dbc.Col([
                        html.P([
                            html.Strong("Sharpe Ratio: "),
                            f"{metrics.get('sharpe_ratio', 0):.2f}"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Max Drawdown: "),
                            f"{metrics.get('max_drawdown', 0)*100:.2f}%"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Total Return: "),
                            f"{metrics.get('total_return', 0)*100:.2f}%"
                        ], className="mb-2")
                    ], md=3),
                    dbc.Col([
                        html.P([
                            html.Strong("Expectancy: "),
                            f"{metrics.get('expectancy', 0)*100:.2f}%"
                        ], className="mb-2")
                    ], md=3)
                ])
            ])
        ], className="mb-3")
        
        # Calculate additional trade statistics if trades exist
        trade_stats_section = None
        if trades_df is not None and len(trades_df) > 0:
            winning_trades = trades_df[trades_df['P&L %'] > 0]
            losing_trades = trades_df[trades_df['P&L %'] <= 0]
            
            avg_win = winning_trades['P&L %'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['P&L %'].mean() if len(losing_trades) > 0 else 0
            avg_holding = trades_df['Holding Period'].mean()
            
            trade_stats_section = dbc.Card([
                dbc.CardHeader(html.H5("📊 Trade Statistics", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                html.Strong("Winning Trades: "),
                                f"{len(winning_trades)}"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Losing Trades: "),
                                f"{len(losing_trades)}"
                            ], className="mb-2")
                        ], md=3),
                        dbc.Col([
                            html.P([
                                html.Strong("Avg Win: "),
                                f"{avg_win*100:.2f}%"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Avg Loss: "),
                                f"{avg_loss*100:.2f}%"
                            ], className="mb-2")
                        ], md=3),
                        dbc.Col([
                            html.P([
                                html.Strong("Profit Factor: "),
                                f"{abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "N/A"
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Avg Holding Period: "),
                                f"{avg_holding:.1f} days"
                            ], className="mb-2")
                        ], md=3)
                    ])
                ])
            ], className="mb-3")
        
        # Equity curve visualization
        equity_chart = None
        if equity_curve is not None and len(equity_curve) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates if dates else list(range(len(equity_curve))),
                y=equity_curve,
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title='Equity Curve',
                xaxis_title='Date',
                yaxis_title='Equity ($)',
                hovermode='x unified',
                height=400
            )
            
            equity_chart = dbc.Card([
                dbc.CardHeader(html.H5("📈 Equity Curve", className="mb-0")),
                dbc.CardBody([dcc.Graph(figure=fig)])
            ], className="mb-3")
        
        # Trade distribution chart
        distribution_chart = None
        if trades_df is not None and len(trades_df) > 0:
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=trades_df['P&L %'] * 100,
                nbinsx=20,
                name='P&L Distribution',
                marker_color='steelblue'
            ))
            
            fig_dist.update_layout(
                title='Trade P&L Distribution',
                xaxis_title='P&L (%)',
                yaxis_title='Frequency',
                height=300
            )
            
            distribution_chart = dbc.Card([
                dbc.CardHeader(html.H5("📊 Trade P&L Distribution", className="mb-0")),
                dbc.CardBody([dcc.Graph(figure=fig_dist)])
            ], className="mb-3")
        
        # Drawdown plot
        drawdown_chart = None
        if equity_curve is not None and len(equity_curve) > 0:
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - peak) / peak * 100
            
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dates if dates else list(range(len(drawdown))),
                y=drawdown,
                fill='tozeroy',
                name='Drawdown',
                line=dict(color='red')
            ))
            
            fig_dd.update_layout(
                title='Drawdown Over Time',
                xaxis_title='Date',
                yaxis_title='Drawdown (%)',
                height=300
            )
            
            drawdown_chart = dbc.Card([
                dbc.CardHeader(html.H5("📉 Drawdown", className="mb-0")),
                dbc.CardBody([dcc.Graph(figure=fig_dd)])
            ], className="mb-3")
        
        # Trade-by-trade table
        trades_table = None
        if trades_df is not None and len(trades_df) > 0:
            trades_display = trades_df.copy()
            if 'Entry Date' in trades_display.columns:
                trades_display['Entry Date'] = pd.to_datetime(trades_display['Entry Date']).dt.strftime('%Y-%m-%d')
            if 'Exit Date' in trades_display.columns:
                trades_display['Exit Date'] = pd.to_datetime(trades_display['Exit Date']).dt.strftime('%Y-%m-%d')
            
            trades_table = dbc.Card([
                dbc.CardHeader(html.H5("📋 Trade-by-Trade Details", className="mb-0")),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=trades_display.to_dict('records'),
                        columns=[
                            {'name': 'Trade No.', 'id': 'Trade No.'},
                            {'name': 'Entry Date', 'id': 'Entry Date'},
                            {'name': 'Entry Price', 'id': 'Entry Price', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': 'Exit Date', 'id': 'Exit Date'},
                            {'name': 'Exit Price', 'id': 'Exit Price', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                            {'name': 'Position', 'id': 'Position'},
                            {'name': 'Size', 'id': 'Size'},
                            {'name': 'Holding Period', 'id': 'Holding Period'},
                            {'name': 'P&L %', 'id': 'P&L %', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                            {'name': 'P&L $', 'id': 'P&L $', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                            {'name': 'MAE', 'id': 'MAE', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                            {'name': 'MFE', 'id': 'MFE', 'type': 'numeric', 'format': {'specifier': '.2%'}},
                            {'name': 'Exit Reason', 'id': 'Exit Reason'},
                            {'name': 'Comments', 'id': 'Comments'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px', 'minWidth': '80px'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold', 'fontSize': '11px'},
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'},
                            {'if': {'filter_query': '{P&L %} > 0', 'column_id': 'P&L %'}, 'backgroundColor': '#d4edda', 'color': '#155724'},
                            {'if': {'filter_query': '{P&L %} <= 0', 'column_id': 'P&L %'}, 'backgroundColor': '#f8d7da', 'color': '#721c24'}
                        ],
                        sort_action='native',
                        filter_action='native',
                        page_size=20,
                        export_format='csv'
                    )
                ])
            ], className="mb-3")
        else:
            trades_table = dbc.Alert("No trade data available for this backtest.", color="warning")
        
        # Assemble all sections
        sections = [summary_section]
        if trade_stats_section:
            sections.append(trade_stats_section)
        if equity_chart:
            sections.append(equity_chart)
        if distribution_chart:
            sections.append(distribution_chart)
        if drawdown_chart:
            sections.append(drawdown_chart)
        sections.append(trades_table)
        
        return html.Div(sections)
