# Session Management - Visual UI Examples

## UI Components Added

### 1. Session Status Banner

The session status banner appears at the top of the page when issues are detected:

```
┌─────────────────────────────────────────────────────────────────┐
│ ⏱️ Your session has expired due to inactivity.                  │
│ Please refresh the page to continue.                            │
│ ─────────────────────────────────────────────────────────────── │
│ To restart your session:                                        │
│ 1. Refresh the page (F5 or Ctrl+R)                            │
│ 2. Your work will be preserved in storage                      │
│ 3. Re-run any active scans or backtests                        │
│                                                      [Dismiss ×] │
└─────────────────────────────────────────────────────────────────┘
```

**Color Coding**:
- 🔵 Blue (Info): Informational messages
- 🟡 Yellow (Warning): Session issues, expiration
- 🔴 Red (Danger): Critical errors, disconnection

### 2. Enhanced Error Messages

#### Scanner Error Example

**Before**:
```
Error: list index out of range
```

**After**:
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ Scan Error                                                    │
│                                                                  │
│ 📁 Required data file not found. Please ensure data is properly │
│ loaded or refresh the page.                                     │
│ ─────────────────────────────────────────────────────────────── │
│ Suggestions:                                                     │
│ • Refresh the page to restart your session                      │
│ • Ensure data is properly loaded for the selected symbols       │
│ • Try a different scan type or parameters                       │
│ • Check the browser console for detailed error information      │
│                                                                  │
│                                                      [Dismiss ×] │
└─────────────────────────────────────────────────────────────────┘
```

#### Backtest Error Example

**Before**:
```
Error occurred
```

**After**:
```
┌─────────────────────────────────────────────────────────────────┐
│ ❌ Batch backtest failed!                                        │
│                                                                  │
│ 🔌 Connection issue detected. Please check your internet        │
│ connection and try again.                                       │
│ ─────────────────────────────────────────────────────────────── │
│ Recovery steps:                                                  │
│ • Verify data is loaded for selected symbols                    │
│ • Try with fewer symbols or strategies                          │
│ • Check system resources and refresh if needed                  │
│ • Review browser console for detailed errors                    │
│                                                                  │
│                                                      [Dismiss ×] │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Connection Status States

Visual representation of session states:

#### Active (Healthy)
```
Status: ✅ Session is active and running normally
Hidden banner - no alerts needed
```

#### Idle
```
Status: 💤 Session is idle but valid
Hidden banner - will activate on interaction
```

#### Error (Recoverable)
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ Session error: Operation failed. Retrying automatically...   │
│ If this persists, please refresh the page.                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Disconnected
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔌 Connection lost. Please check your internet connection and   │
│ refresh the page.                                               │
│ ─────────────────────────────────────────────────────────────── │
│ To reconnect:                                                    │
│ 1. Check your internet connection                              │
│ 2. Refresh the page                                            │
│ 3. If problem persists, clear browser cache and try again      │
└─────────────────────────────────────────────────────────────────┘
```

#### Expired
```
┌─────────────────────────────────────────────────────────────────┐
│ ⏱️ Your session has expired after 30 minutes of inactivity      │
│ ─────────────────────────────────────────────────────────────── │
│ To restart your session:                                        │
│ 1. Refresh the page (F5 or Ctrl+R)                            │
│ 2. Your work will be preserved in storage                      │
│ 3. Re-run any active scans or backtests                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Page Layout with Session Management

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   [Session Status Banner - Appears here when issues detected]          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                  Stock Scanner & Backtest Analyzer                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [📡 Scanner]  [🚀 Backtest Manager]  [📊 Quick Backtest]             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  Scanner Configuration                                           │  │
│  │                                                                  │  │
│  │  Scan Type: [RSI Oversold ▼]                                    │  │
│  │  RSI Period: [14]                                               │  │
│  │  Threshold: [30]                                                │  │
│  │                                                                  │  │
│  │  [Run Scan]                                                     │  │
│  │                                                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Scan Results:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Symbol │ RSI   │ Close  │ Sharpe │ Win Rate │                   │  │
│  ├────────┼───────┼────────┼────────┼──────────┤                   │  │
│  │ AAPL   │ 28.5  │ 150.25 │ 1.8    │ 65%      │                   │  │
│  │ MSFT   │ 27.3  │ 380.50 │ 2.1    │ 68%      │                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

                    [Hidden: Health check runs every 30s]
```

## Error Message Icons

The system uses clear icons to convey error severity:

- ✅ Success / Healthy
- ℹ️ Information
- ⚠️ Warning / Caution
- ❌ Error / Failed
- 🚨 Critical / Urgent
- 🔌 Connection Issue
- ⏱️ Timeout / Expiration
- 📁 File / Data Issue
- 💾 Memory / Resource Issue
- 🔒 Permission / Access Issue

## User Experience Flow

### Scenario 1: Normal Operation
```
User opens page
  ↓
Session created (Active)
  ↓
Health checks run (every 30s)
  ↓
User performs scans/backtests
  ↓
Session remains active
  ↓
No banners shown (all good)
```

### Scenario 2: Transient Error
```
User runs scan
  ↓
Network hiccup occurs
  ↓
Error recorded in session
  ↓
Automatic retry (3 attempts)
  ↓
Success on retry #2
  ↓
Error count reset
  ↓
Brief warning shown (dismissable)
  ↓
User continues normally
```

### Scenario 3: Session Timeout
```
User leaves page idle
  ↓
30 minutes pass
  ↓
Health check detects expiry
  ↓
Yellow warning banner appears:
  "⏱️ Session expired. Refresh to continue."
  ↓
User refreshes page
  ↓
New session created
  ↓
Work preserved in storage
  ↓
User resumes work
```

### Scenario 4: Multiple Errors
```
User runs operation
  ↓
Error occurs
  ↓
User retries
  ↓
Error occurs again (count: 2)
  ↓
User retries
  ↓
Error occurs again (count: 3)
  ↓
...continues...
  ↓
Error count reaches threshold (5)
  ↓
Session marked as Disconnected
  ↓
Red error banner appears:
  "❌ Too many errors. Please refresh."
  ↓
User refreshes
  ↓
Fresh session starts
```

## Mobile Responsive Design

Banners adapt to screen size:

**Desktop** (Full instructions):
```
┌───────────────────────────────────────────────────────────┐
│ ⚠️ Session error occurred                                 │
│ Detailed instructions here...                             │
│ 1. Step one                                              │
│ 2. Step two                                              │
│ 3. Step three                                            │
└───────────────────────────────────────────────────────────┘
```

**Mobile** (Condensed):
```
┌─────────────────────────────────┐
│ ⚠️ Session error                │
│ Tap to view recovery steps      │
└─────────────────────────────────┘
```

## Technical Implementation

### Health Check Callback
```python
@app.callback(
    Output('session-status-banner', 'children'),
    [Input('health-check-interval', 'n_intervals'),
     Input('session-id-store', 'data')]
)
def check_session_health(n_intervals, session_id):
    # Check health every 30 seconds
    # Show banner only if issues detected
    # Return None if healthy (no banner)
```

### Error Handling in Callbacks
```python
try:
    # Perform operation
    results = scanner.scan(...)
    return results, "Success"
except Exception as e:
    # Record error in session
    session_manager.record_session_error(session_id, str(e))
    
    # Show user-friendly error
    error_msg = get_user_friendly_error(e)
    error_banner = create_error_alert(error_msg, recovery_steps)
    
    return error_banner, "Failed"
```

## Accessibility Features

- **Screen Reader Compatible**: All alerts have ARIA labels
- **Keyboard Navigation**: Dismissable with Escape key
- **High Contrast**: Clear color differentiation
- **Focus Management**: Automatic focus to banner when shown

## Browser Console Integration

When errors occur, detailed technical information is logged to the console:

```
Console Output:
─────────────────────────────────────────────────────
ERROR [session_manager]: Session test-123 error: Connection timeout
WARNING [error_handler]: Attempt 1/3 failed: Connection timeout
INFO [error_handler]: Retrying in 1.0 seconds...
INFO [error_handler]: Retry succeeded on attempt 2
─────────────────────────────────────────────────────

User sees: "⚠️ Temporary connection issue. Retry successful."
```

## Summary

The new session management UI provides:

✅ **Non-intrusive**: Banners only appear when needed
✅ **Informative**: Clear, actionable error messages
✅ **Helpful**: Step-by-step recovery instructions
✅ **Professional**: Clean, modern design
✅ **Accessible**: Screen reader and keyboard friendly
✅ **Responsive**: Works on all device sizes

Users now have a clear understanding of system state and know exactly what to do when issues occur.
