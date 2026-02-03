"""
Production Web Server Entry Point
==================================
Entry point for deploying the Dash UI as a web service on Railway or similar platforms.
Uses environment variables for configuration.
"""

import os
from dash_ui import create_app

# Get paths from environment variables with sensible defaults
INDICATOR_PATH = os.environ.get('INDICATOR_PATH', './data/indicators')
BACKTEST_PATH = os.environ.get('BACKTEST_PATH', './data/backtests')

# Create and configure the Dash app
app_instance = create_app(
    indicator_path=INDICATOR_PATH,
    backtest_path=BACKTEST_PATH
)

# The Dash app's Flask server (for gunicorn/uvicorn)
server = app_instance.app.server

if __name__ == '__main__':
    # For local development
    # In production, use gunicorn: gunicorn app:server
    port = int(os.environ.get('PORT', 8050))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app_instance.run(host=host, port=port, debug=debug)
