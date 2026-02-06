"""
Manual Validation of Session Management Features
=================================================
Validates session manager and error handler without pytest dependency.
"""

import sys
import time
from datetime import datetime

# Test imports
try:
    from session_manager import (
        SessionManager,
        SessionState,
        SessionStatus,
        get_session_manager,
        initialize_session_manager
    )
    print("✓ session_manager module imported successfully")
except Exception as e:
    print(f"✗ Failed to import session_manager: {e}")
    sys.exit(1)

try:
    from error_handler import (
        ApplicationError,
        SessionError,
        BackendProcessError,
        DataLoadError,
        ErrorSeverity,
        safe_execute,
        get_user_friendly_error,
        format_error_for_ui,
        RetryStrategy
    )
    print("✓ error_handler module imported successfully")
except Exception as e:
    print(f"✗ Failed to import error_handler: {e}")
    sys.exit(1)


def test_session_creation():
    """Test basic session creation and retrieval."""
    print("\n--- Testing Session Creation ---")
    manager = SessionManager()
    
    session = manager.create_session('test-1', metadata={'user': 'test_user'})
    assert session.session_id == 'test-1', "Session ID mismatch"
    assert session.status == SessionStatus.ACTIVE, "Session should be active"
    assert session.error_count == 0, "Error count should be 0"
    print("✓ Session creation works")
    
    retrieved = manager.get_session('test-1')
    assert retrieved is not None, "Should retrieve existing session"
    assert retrieved.session_id == 'test-1', "Retrieved session ID mismatch"
    print("✓ Session retrieval works")


def test_session_activity():
    """Test session activity tracking."""
    print("\n--- Testing Session Activity ---")
    manager = SessionManager()
    session = manager.create_session('test-2')
    
    initial_time = session.last_activity
    time.sleep(0.2)
    
    success = manager.update_session_activity('test-2')
    assert success, "Activity update should succeed"
    
    updated = manager.get_session('test-2')
    assert updated.last_activity > initial_time, "Activity time should be updated"
    print("✓ Session activity tracking works")


def test_error_recording():
    """Test error recording and threshold."""
    print("\n--- Testing Error Recording ---")
    manager = SessionManager(max_error_threshold=3)
    manager.create_session('test-3')
    
    # Record first error
    manager.record_session_error('test-3', 'Error 1')
    session = manager.get_session('test-3')
    assert session.error_count == 1, "Error count should be 1"
    assert session.status == SessionStatus.ERROR, "Status should be ERROR"
    print("✓ Error recording works")
    
    # Record more errors to exceed threshold
    manager.record_session_error('test-3', 'Error 2')
    manager.record_session_error('test-3', 'Error 3')
    
    session = manager.get_session('test-3')
    assert session.status == SessionStatus.DISCONNECTED, "Should be disconnected after threshold"
    print("✓ Error threshold works")


def test_health_checks():
    """Test health check functionality."""
    print("\n--- Testing Health Checks ---")
    manager = SessionManager()
    manager.create_session('test-4')
    
    # Healthy session
    health = manager.check_health('test-4')
    assert health['status'] == 'healthy', "Should be healthy"
    assert health['healthy'] is True, "Healthy flag should be True"
    print("✓ Healthy session check works")
    
    # Non-existent session
    health = manager.check_health('non-existent')
    assert health['status'] == 'not_found', "Should be not_found"
    assert health['healthy'] is False, "Should not be healthy"
    print("✓ Non-existent session check works")
    
    # Error session
    manager.record_session_error('test-4', 'Test error')
    health = manager.check_health('test-4')
    assert health['status'] == 'error', "Should be error"
    assert health['can_recover'] is True, "Should be recoverable"
    print("✓ Error session check works")


def test_user_friendly_messages():
    """Test user-friendly message generation."""
    print("\n--- Testing User-Friendly Messages ---")
    manager = SessionManager()
    
    test_statuses = [
        {'status': 'healthy', 'healthy': True},
        {'status': 'expired', 'healthy': False},
        {'status': 'failed', 'healthy': False},
        {'status': 'error', 'healthy': False, 'message': 'Test error'}
    ]
    
    for status in test_statuses:
        message = manager.get_user_friendly_message(status)
        assert isinstance(message, str), "Should return string"
        assert len(message) > 0, "Message should not be empty"
    
    print("✓ User-friendly messages work")


def test_error_handler_safe_execute():
    """Test safe_execute function."""
    print("\n--- Testing Safe Execute ---")
    
    def working_func(a, b):
        return a + b
    
    success, result, error = safe_execute(working_func, 2, 3)
    assert success is True, "Should succeed"
    assert result == 5, "Result should be 5"
    assert error is None, "Error should be None"
    print("✓ Safe execute with success works")
    
    def failing_func():
        raise ValueError("Test error")
    
    success, result, error = safe_execute(failing_func, default_value="default")
    assert success is False, "Should fail"
    assert result == "default", "Should return default value"
    assert error is not None, "Error message should be present"
    print("✓ Safe execute with failure works")


def test_error_handler_user_messages():
    """Test user-friendly error messages."""
    print("\n--- Testing Error Handler Messages ---")
    
    # Test different error types
    errors = [
        Exception("Connection timeout"),
        FileNotFoundError("file not found"),
        MemoryError("out of memory"),
        ValueError("invalid value")
    ]
    
    for error in errors:
        message = get_user_friendly_error(error)
        assert isinstance(message, str), "Should return string"
        assert len(message) > 0, "Message should not be empty"
    
    print("✓ User-friendly error messages work")


def test_retry_strategy():
    """Test retry strategy."""
    print("\n--- Testing Retry Strategy ---")
    
    attempt_count = {'value': 0}
    
    def succeeds_second_time():
        attempt_count['value'] += 1
        if attempt_count['value'] < 2:
            raise ValueError("First try fails")
        return "success"
    
    strategy = RetryStrategy(max_attempts=3, initial_delay=0.1)
    success, result, error = strategy.execute(succeeds_second_time)
    
    assert success is True, "Should succeed on retry"
    assert result == "success", "Should return success"
    assert attempt_count['value'] == 2, "Should have tried twice"
    print("✓ Retry strategy works")


def test_custom_exceptions():
    """Test custom exception classes."""
    print("\n--- Testing Custom Exceptions ---")
    
    session_error = SessionError("Session failed")
    assert isinstance(session_error, ApplicationError), "Should be ApplicationError"
    assert session_error.severity == ErrorSeverity.ERROR, "Should be ERROR severity"
    print("✓ SessionError works")
    
    backend_error = BackendProcessError("Backend failed")
    assert isinstance(backend_error, ApplicationError), "Should be ApplicationError"
    print("✓ BackendProcessError works")
    
    data_error = DataLoadError("Data not found")
    assert isinstance(data_error, ApplicationError), "Should be ApplicationError"
    assert data_error.severity == ErrorSeverity.WARNING, "Should be WARNING severity"
    print("✓ DataLoadError works")


def run_all_tests():
    """Run all validation tests."""
    print("="*60)
    print("Session Management and Error Handling Validation")
    print("="*60)
    
    tests = [
        test_session_creation,
        test_session_activity,
        test_error_recording,
        test_health_checks,
        test_user_friendly_messages,
        test_error_handler_safe_execute,
        test_error_handler_user_messages,
        test_retry_strategy,
        test_custom_exceptions
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
