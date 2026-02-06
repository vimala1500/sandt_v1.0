# Session Management and Error Handling Guide

## Overview

This guide explains the new session management and error handling features added to the Stock Analysis & Trading System (sandt_v1.0) to provide robust error recovery, user-friendly error messages, and graceful handling of connection issues.

## Features

### 1. Session Management

The system now includes comprehensive session lifecycle management:

- **Session Status Tracking**: Active, Idle, Disconnected, Error, Expired
- **Health Monitoring**: Periodic health checks with automatic status updates
- **Activity Tracking**: Automatic timeout detection for inactive sessions
- **Error Recording**: Track errors per session with configurable thresholds

### 2. Error Handling

Enhanced error handling with user-friendly messages:

- **Custom Exception Classes**: SessionError, BackendProcessError, DataLoadError
- **Safe Execution**: Wrapper functions that gracefully handle errors
- **Retry Strategy**: Automatic retry with exponential backoff
- **User-Friendly Messages**: Convert technical errors to actionable user guidance

### 3. UI Integration

Visual indicators and user guidance in the Dash UI:

- **Session Status Banner**: Shows connection status and issues
- **Health Check Interval**: Automatic background health monitoring
- **Error Recovery Instructions**: Step-by-step recovery guidance
- **Dismissable Alerts**: Non-intrusive error notifications

## Architecture

### Session Manager

The `SessionManager` class provides centralized session state management:

```python
from session_manager import get_session_manager

# Get global session manager
manager = get_session_manager()

# Create a session
session = manager.create_session('my-session', metadata={'user': 'alice'})

# Update activity (prevents timeout)
manager.update_session_activity('my-session')

# Check health
health = manager.check_health('my-session')
if not health['healthy']:
    print(health['message'])
```

### Error Handler

The `error_handler` module provides utilities for safe execution and error formatting:

```python
from error_handler import safe_execute, get_user_friendly_error

# Safe execution with automatic error handling
success, result, error = safe_execute(
    risky_function,
    arg1, arg2,
    error_message="Operation failed",
    default_value=None
)

if not success:
    print(f"Error: {error}")

# Get user-friendly error message
try:
    dangerous_operation()
except Exception as e:
    user_msg = get_user_friendly_error(e)
    print(user_msg)  # Shows friendly message like "🔌 Connection issue detected..."
```

## Session States

### Active
- Session is running normally
- User is actively interacting with the application
- No errors or issues detected

### Idle
- Session exists but no recent activity
- Not yet expired
- Will transition to Active on next interaction

### Error
- Session encountered an error but is recoverable
- Error count below threshold
- Automatic retry may be attempted

### Disconnected
- Too many errors occurred (exceeded threshold)
- Connection may be lost
- User must reconnect or refresh

### Expired
- Session timed out due to inactivity
- Default timeout: 30 minutes
- User must refresh to create new session

## Configuration

### Session Timeout

Configure session timeout when initializing:

```python
from session_manager import initialize_session_manager

# Set 60-minute timeout
manager = initialize_session_manager(
    session_timeout_minutes=60,
    max_error_threshold=5
)
```

### Error Threshold

The system tracks errors per session. Default threshold is 5 errors before marking session as disconnected.

### Health Check Interval

The UI performs health checks every 30 seconds by default. This can be adjusted in `dash_ui.py`:

```python
dcc.Interval(
    id='health-check-interval',
    interval=30*1000,  # milliseconds
    n_intervals=0
)
```

## User Experience

### Normal Operation

When everything is working:
- No status banner displayed
- Operations complete successfully
- Session stays active

### Error Scenarios

When errors occur:

1. **Single Error**
   - Error recorded in session
   - User sees friendly error message
   - Automatic retry may be attempted
   - Session remains active

2. **Multiple Errors**
   - Error count increases
   - Session status changes to ERROR
   - User sees warning banner with recovery steps
   - Can continue but may need to refresh

3. **Too Many Errors**
   - Session marked as DISCONNECTED
   - Banner shows reconnection instructions
   - User must refresh page

4. **Session Timeout**
   - After 30 minutes of inactivity
   - Session marked as EXPIRED
   - Banner prompts user to refresh
   - Work preserved in storage

## Recovery Strategies

### Automatic Recovery

The system attempts automatic recovery for:
- Temporary network issues (with retry)
- Transient backend errors (with exponential backoff)
- Recoverable data loading errors

### Manual Recovery

Users are guided through manual recovery for:
- Session expiration → Refresh page
- Connection loss → Check network and refresh
- Backend failure → Refresh or contact support

### Recovery Instructions

The system provides context-specific recovery instructions:

```python
# Get recovery instructions for a health status
instructions = manager.get_recovery_instructions(health_status)
if instructions:
    print(instructions)
```

Example output:
```
To restart your session:
1. Refresh the page (F5 or Ctrl+R)
2. Your work will be preserved in storage
3. Re-run any active scans or backtests
```

## API Reference

### SessionManager

#### Methods

- `create_session(session_id, metadata=None)` - Create new session
- `get_session(session_id)` - Retrieve session by ID
- `update_session_activity(session_id)` - Update last activity timestamp
- `record_session_error(session_id, error_message, recovery_action=None)` - Record error
- `check_health(session_id)` - Check session health status
- `cleanup_expired_sessions()` - Remove expired sessions
- `get_user_friendly_message(health_status)` - Get user-friendly status message
- `get_recovery_instructions(health_status)` - Get recovery instructions

#### Properties

- `session_timeout_minutes` - Inactivity timeout
- `max_error_threshold` - Maximum errors before disconnect
- `health_check_interval` - Seconds between health checks

### Error Handler

#### Functions

- `safe_execute(func, *args, error_message, default_value, **kwargs)` - Safely execute function
- `get_user_friendly_error(error)` - Convert exception to user message
- `format_error_for_ui(error, context, include_recovery)` - Format error for UI display
- `create_error_banner(message, severity, recovery_hint)` - Create HTML error banner
- `handle_callback_error(error, callback_name, session_manager, session_id)` - Handle callback errors

#### Classes

- `ApplicationError` - Base application exception
- `SessionError` - Session-related errors
- `BackendProcessError` - Backend process errors
- `DataLoadError` - Data loading errors
- `RetryStrategy` - Retry logic with exponential backoff

## Testing

### Unit Tests

Run validation tests:

```bash
python validate_session_features.py
```

### Integration Testing

Test with actual UI:

1. Start the application:
   ```bash
   python app.py
   ```

2. Test scenarios:
   - Normal operation
   - Network disconnection
   - Session timeout (wait 30 minutes)
   - Multiple rapid operations (trigger errors)
   - Backend unavailability

### Expected Behavior

- Session status banner appears only when issues occur
- Error messages are user-friendly and actionable
- Recovery instructions are clear and helpful
- Sessions automatically recover from transient errors
- Users can always refresh to restart

## Best Practices

### For Developers

1. **Always update session activity** in callbacks that perform operations
2. **Use safe_execute** for risky operations
3. **Provide context** in error messages
4. **Include recovery hints** in custom exceptions
5. **Log errors** for debugging while showing friendly messages to users

### For Users

1. **Refresh regularly** for long-running sessions
2. **Follow recovery instructions** when errors occur
3. **Check network connection** if seeing connection errors
4. **Contact support** if errors persist after refresh
5. **Save work frequently** (system preserves most state automatically)

## Troubleshooting

### Session keeps expiring
- Increase `session_timeout_minutes` in configuration
- Check if user is actually inactive
- Verify health check interval is reasonable

### Too many error alerts
- Review `max_error_threshold` setting
- Investigate root cause of errors
- Check backend stability

### Health checks impacting performance
- Increase health check interval
- Optimize health check logic
- Consider async health checks

### Recovery not working
- Verify recovery actions are implemented
- Check error threshold hasn't been exceeded
- Review error logs for underlying issues

## Future Enhancements

Potential improvements:

1. **WebSocket Integration**: Real-time session status updates
2. **Session Persistence**: Store sessions in database for recovery across restarts
3. **Advanced Analytics**: Track error patterns and user recovery success
4. **Automatic Reconnection**: Seamless reconnection without page refresh
5. **Session Migration**: Transfer sessions between servers/instances

## Support

For issues or questions:
- Check this documentation
- Review error logs
- Consult code comments in `session_manager.py` and `error_handler.py`
- Open GitHub issue with error details

## Version

- **Version**: 1.1.0
- **Date**: 2026-02-06
- **Status**: Production Ready ✅
