"""
Test Error Handler
==================
Tests for error handling utilities.
"""

import pytest
from error_handler import (
    ApplicationError,
    SessionError,
    BackendProcessError,
    DataLoadError,
    ErrorSeverity,
    with_error_handling,
    safe_execute,
    get_user_friendly_error,
    format_error_for_ui,
    create_error_banner,
    RetryStrategy,
    handle_callback_error
)


def test_application_error():
    """Test ApplicationError exception."""
    error = ApplicationError(
        message="Test error",
        severity=ErrorSeverity.WARNING,
        user_message="User-friendly message",
        recovery_hint="Try again"
    )
    
    assert str(error) == "Test error"
    assert error.severity == ErrorSeverity.WARNING
    assert error.user_message == "User-friendly message"
    assert error.recovery_hint == "Try again"


def test_session_error():
    """Test SessionError exception."""
    error = SessionError("Session expired")
    
    assert isinstance(error, ApplicationError)
    assert error.severity == ErrorSeverity.ERROR


def test_backend_process_error():
    """Test BackendProcessError exception."""
    error = BackendProcessError("Process failed")
    
    assert isinstance(error, ApplicationError)
    assert error.severity == ErrorSeverity.ERROR


def test_data_load_error():
    """Test DataLoadError exception."""
    error = DataLoadError("Data not found")
    
    assert isinstance(error, ApplicationError)
    assert error.severity == ErrorSeverity.WARNING


def test_with_error_handling_decorator_success():
    """Test error handling decorator on successful function."""
    @with_error_handling(user_friendly_message="Operation failed")
    def successful_function(x, y):
        return x + y
    
    result = successful_function(2, 3)
    assert result == 5


def test_with_error_handling_decorator_error():
    """Test error handling decorator on failing function."""
    @with_error_handling(
        user_friendly_message="Operation failed",
        default_return="error"
    )
    def failing_function():
        raise ValueError("Test error")
    
    result = failing_function()
    assert result == "error"


def test_with_error_handling_decorator_reraise():
    """Test error handling decorator with raise_on_error."""
    @with_error_handling(
        user_friendly_message="Operation failed",
        raise_on_error=True
    )
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()


def test_safe_execute_success():
    """Test safe_execute with successful function."""
    def successful_function(x, y):
        return x * y
    
    success, result, error = safe_execute(
        successful_function,
        2, 3,
        error_message="Multiplication failed"
    )
    
    assert success is True
    assert result == 6
    assert error is None


def test_safe_execute_failure():
    """Test safe_execute with failing function."""
    def failing_function():
        raise ValueError("Test error")
    
    success, result, error = safe_execute(
        failing_function,
        error_message="Operation failed",
        default_value=None
    )
    
    assert success is False
    assert result is None
    assert error is not None
    assert isinstance(error, str)


def test_get_user_friendly_error_connection():
    """Test user-friendly error for connection issues."""
    error = Exception("Connection timeout occurred")
    message = get_user_friendly_error(error)
    
    assert "Connection" in message or "connection" in message


def test_get_user_friendly_error_file_not_found():
    """Test user-friendly error for file not found."""
    error = FileNotFoundError("file not found")
    message = get_user_friendly_error(error)
    
    assert "file" in message.lower() or "data" in message.lower()


def test_get_user_friendly_error_memory():
    """Test user-friendly error for memory issues."""
    error = MemoryError("Out of memory")
    message = get_user_friendly_error(error)
    
    assert "memory" in message.lower()


def test_get_user_friendly_error_application_error():
    """Test user-friendly error for ApplicationError."""
    error = ApplicationError(
        message="Internal error",
        user_message="Something went wrong"
    )
    message = get_user_friendly_error(error)
    
    assert message == "Something went wrong"


def test_format_error_for_ui():
    """Test formatting error for UI display."""
    error = ValueError("Invalid value")
    result = format_error_for_ui(error, context="Testing")
    
    assert result['type'] == 'ValueError'
    assert 'message' in result
    assert result['context'] == "Testing"
    assert result['severity'] == 'error'


def test_format_error_for_ui_application_error():
    """Test formatting ApplicationError for UI."""
    error = ApplicationError(
        message="Test error",
        severity=ErrorSeverity.WARNING,
        user_message="User message",
        recovery_hint="Try recovery"
    )
    
    result = format_error_for_ui(error, include_recovery=True)
    
    assert result['severity'] == 'warning'
    assert result['message'] == "User message"
    assert result['recovery_hint'] == "Try recovery"


def test_create_error_banner():
    """Test creating HTML error banner."""
    banner = create_error_banner(
        message="Test error",
        severity="error",
        recovery_hint="Try again"
    )
    
    assert isinstance(banner, str)
    assert "alert" in banner
    assert "Test error" in banner
    assert "Try again" in banner


def test_create_error_banner_severity_levels():
    """Test error banner with different severity levels."""
    severities = ['info', 'warning', 'error', 'critical']
    
    for severity in severities:
        banner = create_error_banner("Test", severity=severity)
        assert isinstance(banner, str)
        assert len(banner) > 0


def test_retry_strategy_success():
    """Test retry strategy with successful function."""
    attempt_count = {'value': 0}
    
    def function_succeeds_on_second_try():
        attempt_count['value'] += 1
        if attempt_count['value'] < 2:
            raise ValueError("First attempt fails")
        return "success"
    
    strategy = RetryStrategy(max_attempts=3, initial_delay=0.1)
    success, result, error = strategy.execute(function_succeeds_on_second_try)
    
    assert success is True
    assert result == "success"
    assert error is None
    assert attempt_count['value'] == 2


def test_retry_strategy_all_failures():
    """Test retry strategy with all attempts failing."""
    attempt_count = {'value': 0}
    
    def function_always_fails():
        attempt_count['value'] += 1
        raise ValueError("Always fails")
    
    strategy = RetryStrategy(max_attempts=3, initial_delay=0.1)
    success, result, error = strategy.execute(function_always_fails)
    
    assert success is False
    assert result is None
    assert error is not None
    assert attempt_count['value'] == 3


def test_retry_strategy_backoff():
    """Test retry strategy exponential backoff."""
    strategy = RetryStrategy(
        max_attempts=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=10.0
    )
    
    assert strategy.initial_delay == 1.0
    assert strategy.backoff_factor == 2.0
    assert strategy.max_delay == 10.0


def test_handle_callback_error():
    """Test callback error handler."""
    error = ValueError("Callback failed")
    
    result = handle_callback_error(
        error,
        callback_name="test_callback",
        session_manager=None,
        session_id=None
    )
    
    assert 'type' in result
    assert 'message' in result
    assert result['context'] == "test_callback"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
