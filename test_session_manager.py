"""
Test Session Manager
====================
Tests for session management functionality.
"""

import pytest
import time
from datetime import datetime, timedelta

from session_manager import (
    SessionManager,
    SessionState,
    SessionStatus,
    get_session_manager,
    initialize_session_manager
)


def test_create_session():
    """Test session creation."""
    manager = SessionManager()
    session = manager.create_session('test-session-1', metadata={'user': 'test'})
    
    assert session.session_id == 'test-session-1'
    assert session.status == SessionStatus.ACTIVE
    assert session.metadata['user'] == 'test'
    assert session.error_count == 0


def test_get_session():
    """Test retrieving a session."""
    manager = SessionManager()
    manager.create_session('test-session-2')
    
    session = manager.get_session('test-session-2')
    assert session is not None
    assert session.session_id == 'test-session-2'
    
    # Non-existent session
    session = manager.get_session('non-existent')
    assert session is None


def test_update_activity():
    """Test session activity updates."""
    manager = SessionManager()
    session = manager.create_session('test-session-3')
    
    initial_time = session.last_activity
    time.sleep(0.1)
    
    manager.update_session_activity('test-session-3')
    updated_session = manager.get_session('test-session-3')
    
    assert updated_session.last_activity > initial_time


def test_session_expiry():
    """Test session expiry detection."""
    manager = SessionManager(session_timeout_minutes=0.01)  # 0.6 seconds
    session = manager.create_session('test-session-4')
    
    # Session should not be expired immediately
    assert not session.is_expired(0.01)
    
    # Wait for expiry
    time.sleep(1)
    
    # Session should now be expired
    assert session.is_expired(0.01)
    
    # Getting expired session should mark it as expired
    retrieved_session = manager.get_session('test-session-4')
    assert retrieved_session.status == SessionStatus.EXPIRED


def test_record_error():
    """Test error recording."""
    manager = SessionManager(max_error_threshold=3)
    session = manager.create_session('test-session-5')
    
    # Record first error
    manager.record_session_error('test-session-5', 'Error 1')
    session = manager.get_session('test-session-5')
    assert session.error_count == 1
    assert session.status == SessionStatus.ERROR
    assert session.last_error == 'Error 1'
    
    # Record more errors
    manager.record_session_error('test-session-5', 'Error 2')
    manager.record_session_error('test-session-5', 'Error 3')
    
    session = manager.get_session('test-session-5')
    assert session.error_count == 3
    assert session.status == SessionStatus.DISCONNECTED  # Exceeded threshold


def test_error_recovery():
    """Test error recovery mechanism."""
    manager = SessionManager(max_error_threshold=5)
    session = manager.create_session('test-session-6')
    
    recovery_called = {'count': 0}
    
    def recovery_action():
        recovery_called['count'] += 1
    
    # Record error with recovery
    success = manager.record_session_error(
        'test-session-6',
        'Recoverable error',
        recovery_action=recovery_action
    )
    
    assert success
    assert recovery_called['count'] == 1
    
    # Session errors should be reset after successful recovery
    session = manager.get_session('test-session-6')
    assert session.error_count == 0
    assert session.status == SessionStatus.ACTIVE


def test_health_check_healthy():
    """Test health check for healthy session."""
    manager = SessionManager()
    manager.create_session('test-session-7')
    
    health = manager.check_health('test-session-7')
    
    assert health['status'] == 'healthy'
    assert health['healthy'] is True
    assert 'idle_seconds' in health


def test_health_check_expired():
    """Test health check for expired session."""
    manager = SessionManager(session_timeout_minutes=0.01)
    manager.create_session('test-session-8')
    
    # Wait for expiry
    time.sleep(1)
    
    health = manager.check_health('test-session-8')
    
    assert health['status'] == 'expired'
    assert health['healthy'] is False
    assert health['can_recover'] is True
    assert health['recovery_action'] == 'restart'


def test_health_check_error():
    """Test health check for session in error state."""
    manager = SessionManager(max_error_threshold=5)
    manager.create_session('test-session-9')
    
    # Record error without recovery
    manager.record_session_error('test-session-9', 'Test error')
    
    health = manager.check_health('test-session-9')
    
    assert health['status'] == 'error'
    assert health['healthy'] is False
    assert health['can_recover'] is True
    assert health['recovery_action'] == 'retry'
    assert 'error_count' in health


def test_health_check_failed():
    """Test health check for failed session (too many errors)."""
    manager = SessionManager(max_error_threshold=2)
    manager.create_session('test-session-10')
    
    # Exceed error threshold
    manager.record_session_error('test-session-10', 'Error 1')
    manager.record_session_error('test-session-10', 'Error 2')
    
    health = manager.check_health('test-session-10')
    
    assert health['status'] == 'failed'
    assert health['healthy'] is False
    assert health['can_recover'] is True
    assert health['recovery_action'] == 'reconnect'


def test_cleanup_expired_sessions():
    """Test cleanup of expired sessions."""
    manager = SessionManager(session_timeout_minutes=0.01)
    
    # Create multiple sessions
    manager.create_session('session-1')
    manager.create_session('session-2')
    manager.create_session('session-3')
    
    # Wait for expiry
    time.sleep(1)
    
    # Cleanup
    cleaned = manager.cleanup_expired_sessions()
    
    assert cleaned == 3
    assert len(manager.sessions) == 0


def test_user_friendly_messages():
    """Test user-friendly message generation."""
    manager = SessionManager()
    manager.create_session('test-session-11')
    
    # Test different statuses
    statuses = ['not_found', 'expired', 'failed', 'error', 'disconnected', 'healthy']
    
    for status in statuses:
        health = {'status': status, 'message': 'Test message'}
        message = manager.get_user_friendly_message(health)
        
        assert isinstance(message, str)
        assert len(message) > 0


def test_recovery_instructions():
    """Test recovery instruction generation."""
    manager = SessionManager()
    manager.create_session('test-session-12')
    
    # Test with recovery actions
    recovery_actions = ['restart', 'reconnect', 'retry']
    
    for action in recovery_actions:
        health = {'healthy': False, 'recovery_action': action}
        instructions = manager.get_recovery_instructions(health)
        
        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0
    
    # Test healthy session (no instructions needed)
    health = {'healthy': True}
    instructions = manager.get_recovery_instructions(health)
    assert instructions is None


def test_global_session_manager():
    """Test global session manager singleton."""
    # Get global instance
    manager1 = get_session_manager()
    manager2 = get_session_manager()
    
    # Should be the same instance
    assert manager1 is manager2
    
    # Test initialization with custom settings
    manager3 = initialize_session_manager(
        session_timeout_minutes=60,
        max_error_threshold=10
    )
    
    assert manager3.session_timeout_minutes == 60
    assert manager3.max_error_threshold == 10
    
    # Getting after initialization should return the initialized instance
    manager4 = get_session_manager()
    assert manager4 is manager3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
