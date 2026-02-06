# Session Troubleshooting Guide

## Overview

This guide helps you understand and resolve session-related issues in the Stock Scanner & Backtest Analyzer platform.

---

## Table of Contents

1. [Understanding Sessions](#understanding-sessions)
2. [Common Session Errors](#common-session-errors)
3. [Recovery Procedures](#recovery-procedures)
4. [Prevention Tips](#prevention-tips)
5. [Technical Details](#technical-details)

---

## Understanding Sessions

### What is a Session?

A session is a temporary connection between your browser and the application server. It stores:
- Your current state (selected symbols, strategies, etc.)
- Activity history
- Error logs
- User preferences

### Session Lifecycle

1. **Creation**: A new session is created when you first load the application
2. **Active**: Session remains active while you interact with the application
3. **Idle**: After 30 minutes of inactivity, session becomes idle
4. **Expired**: After extended idle time, session expires and must be recreated

### Why Sessions Matter

Sessions enable:
- Maintaining your work across page interactions
- Tracking application health
- Providing context for error recovery
- Ensuring data consistency

---

## Common Session Errors

### 1. "Session Not Found"

**Symptoms:**
- Large warning banner appears at the top of the page
- Message: "🔔 Session Not Found"
- Can't perform any actions

**Causes:**
- Page refreshed after long period of inactivity (>30 minutes)
- Server was restarted
- Browser cleared cache or cookies
- Network connection was interrupted

**Solution:**
Click the **"🔄 Start New Session"** button in the warning banner to create a fresh session.

---

### 2. "Session Expired"

**Symptoms:**
- Warning banner with "⚠️ Session Issue Detected"
- Operations fail with timeout errors
- Data doesn't load or update

**Causes:**
- No interaction with the application for 30+ minutes
- Session reached maximum age
- Server-side cleanup of old sessions

**Solution:**
1. Click **"🆕 Start New Session"** to create a new session
2. Or click **"🔄 Refresh Page"** to reload the application

---

### 3. "Connection Error"

**Symptoms:**
- "❌ Session Error" banner
- Cannot load data or perform operations
- Frequent timeouts

**Causes:**
- Network connectivity issues
- Server is down or unreachable
- Firewall or proxy blocking connection
- Heavy server load

**Solution:**
1. Check your internet connection
2. Try refreshing the page
3. Wait a few minutes and try again
4. Contact support if issue persists

---

### 4. "Too Many Errors"

**Symptoms:**
- Session marked as failed after multiple errors
- Operations consistently fail
- Error count visible in logs

**Causes:**
- Repeated failed operations
- Data corruption
- Server-side issues
- Invalid configurations

**Solution:**
1. Click **"🆕 Start New Session"** to start fresh
2. Review and validate your configurations
3. Try with smaller data sets
4. Check system resources (memory, CPU)

---

## Recovery Procedures

### Quick Recovery (Recommended)

1. **Locate the session banner** at the top of the page (if visible)
2. **Read the error message** to understand what happened
3. **Click recovery button**:
   - **"🔄 Start New Session"**: Creates new session immediately
   - **"🔄 Refresh Page"**: Reloads entire application
4. **Resume your work**: Your application is ready to use

### Manual Recovery

If quick recovery doesn't work:

1. **Clear browser cache**:
   - Chrome: Ctrl+Shift+Delete → Clear cached data
   - Firefox: Ctrl+Shift+Delete → Cookies and Cache
   - Safari: Preferences → Privacy → Remove All Website Data

2. **Hard refresh the page**:
   - Windows: Ctrl+F5 or Ctrl+Shift+R
   - Mac: Cmd+Shift+R

3. **Try incognito/private mode**:
   - Eliminates cached data issues
   - Tests if browser extensions are interfering

4. **Restart your browser**:
   - Completely close all browser windows
   - Reopen and navigate to the application

### Advanced Recovery

For persistent issues:

1. **Check browser console** for errors:
   - Press F12 to open Developer Tools
   - Look at Console tab for red error messages
   - Share these with support if needed

2. **Try a different browser**:
   - Isolates browser-specific issues
   - Recommended browsers: Chrome, Firefox, Safari, Edge

3. **Check server status**:
   - If self-hosted, verify server is running
   - Check server logs for errors
   - Verify network connectivity to server

4. **Contact administrator**:
   - For deployment issues
   - If error persists across browsers
   - If other users report same issue

---

## Prevention Tips

### Best Practices

1. **Stay Active**:
   - Interact with the application at least once every 20 minutes
   - Run health checks automatically happen every 30 seconds

2. **Save Your Work**:
   - Use "Save Group Set" feature for batch backtests
   - Export results before long periods of inactivity
   - Bookmark frequently used configurations

3. **Stable Connection**:
   - Use reliable internet connection
   - Avoid switching networks mid-session
   - Close unnecessary browser tabs to reduce resource usage

4. **Regular Updates**:
   - Keep your browser up to date
   - Clear cache periodically
   - Don't accumulate too many open tabs

### Configuration Recommendations

**For Administrators:**

Adjust session timeout in `session_manager.py`:
```python
SessionManager(
    session_timeout_minutes=30,  # Increase for longer sessions
    max_error_threshold=5,       # Errors before marking failed
    health_check_interval=60     # Seconds between checks
)
```

**For Users:**

- Refresh the page before starting long operations
- Use "Export" features to save work frequently
- Don't leave application idle for extended periods

---

## Technical Details

### Session Architecture

**Components:**
- **SessionManager**: Server-side session lifecycle management
- **SessionState**: Tracks status, activity, errors
- **Health Check**: Periodic monitoring (every 30 seconds)
- **Error Handler**: Graceful error recovery

**Session Status States:**
- `ACTIVE`: Normal operation
- `IDLE`: No activity, but still valid
- `DISCONNECTED`: Connection lost
- `ERROR`: Recoverable error occurred
- `EXPIRED`: Session too old, must recreate
- `FAILED`: Too many errors

### Health Check Process

```python
# Runs every 30 seconds
1. Check if session exists
2. Calculate time since last activity
3. Check error count
4. Determine session health
5. Display banner if unhealthy
6. Provide recovery options
```

### Session Storage

**Stored in Memory:**
- Session ID (UUID)
- Creation timestamp
- Last activity timestamp
- Error count and messages
- Metadata (paths, configuration)

**Not Stored:**
- User credentials (not needed)
- Sensitive data
- Large datasets (stored separately)

### Error Thresholds

| Threshold | Value | Action |
|-----------|-------|--------|
| Idle timeout | 30 minutes | Mark as idle |
| Session expiry | 60 minutes idle | Mark as expired |
| Max errors | 5 errors | Mark as failed |
| Health check interval | 30 seconds | Check session health |

### Recovery Actions

**"Start New Session":**
```python
1. Generate new UUID
2. Create fresh SessionState
3. Initialize with default metadata
4. Update UI with new session ID
5. Resume operations
```

**"Refresh Page":**
```python
1. Trigger browser reload
2. Application reinitializes
3. Creates new session automatically
4. Loads fresh state
```

---

## Debugging Guide

### For Developers

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Monitor Session State:**
```python
# Check current session
session_id = app.session_id
status = session_manager.check_health(session_id)
print(f"Session status: {status}")
```

**Simulate Session Expiry:**
```python
# Force expiry for testing
session_state.last_activity = datetime.now() - timedelta(minutes=31)
```

### Common Debug Steps

1. **Check session exists**:
   ```python
   session_exists = session_id in session_manager.sessions
   ```

2. **Check session health**:
   ```python
   health = session_manager.check_health(session_id)
   print(f"Healthy: {health.get('healthy')}")
   ```

3. **View session metadata**:
   ```python
   session = session_manager.sessions.get(session_id)
   print(f"Created: {session.created_at}")
   print(f"Last activity: {session.last_activity}")
   print(f"Errors: {session.error_count}")
   ```

4. **Reset session errors**:
   ```python
   session_manager.sessions[session_id].reset_errors()
   ```

---

## FAQ

### Q: How long can I stay idle?

**A:** Sessions remain valid for 30 minutes of inactivity. After that, you'll need to start a new session.

### Q: Will I lose my work if session expires?

**A:** Some work is saved:
- ✅ Computed indicators (stored on disk)
- ✅ Saved group sets (stored on disk)
- ✅ Exported results (in downloads)
- ❌ Selected but not saved configurations
- ❌ Filters and search terms
- ❌ Unsaved backtest selections

### Q: Why do I keep getting session errors?

**A:** Common reasons:
- Unstable internet connection
- Server resource issues
- Too many concurrent operations
- Browser cache corruption

Try: Clear cache, restart browser, use different network.

### Q: Can I extend session timeout?

**A:** Yes, if you have admin access. Modify `session_timeout_minutes` in `session_manager.py` initialization.

### Q: What happens to my data when session expires?

**A:** Session expiry only affects connection state. Your:
- Indicator data remains on disk
- Backtest results remain on disk
- Configuration files remain on disk
Only temporary UI state is lost.

### Q: Is my data secure?

**A:** Yes. Sessions:
- Don't store sensitive credentials
- Use UUID for identification
- Expire automatically
- Are server-side managed
- Don't expose data to other sessions

---

## Contact Support

If you continue to experience session issues:

1. **Collect information**:
   - Browser type and version
   - Error message text
   - Steps to reproduce
   - Browser console errors (F12)

2. **Check documentation**:
   - README.md
   - SESSION_MANAGEMENT_GUIDE.md
   - This troubleshooting guide

3. **Report issue**:
   - GitHub Issues: Include collected information
   - Provide screenshots if helpful
   - Mention if issue is reproducible

---

**Last Updated**: 2026-02-06  
**Version**: 1.1.0
