"""
Session Manager Module
======================
Manages session state, health checks, and connection monitoring for the application.
Provides graceful error handling and recovery mechanisms.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status states."""
    ACTIVE = "active"
    IDLE = "idle"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class SessionState:
    """Represents the state of a session."""
    session_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired due to inactivity."""
        timeout_delta = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout_delta
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE
    
    def record_error(self, error_message: str):
        """Record an error occurrence."""
        self.error_count += 1
        self.last_error = error_message
        self.status = SessionStatus.ERROR
        logger.error(f"Session {self.session_id} error: {error_message}")
    
    def reset_errors(self):
        """Reset error state."""
        self.error_count = 0
        self.last_error = None
        if self.status == SessionStatus.ERROR:
            self.status = SessionStatus.ACTIVE


class SessionManager:
    """
    Manages application sessions with health monitoring and error recovery.
    
    Features:
    - Session lifecycle management
    - Health checks and heartbeats
    - Error tracking and recovery
    - Session timeout handling
    - Connection state monitoring
    """
    
    def __init__(
        self,
        session_timeout_minutes: int = 30,
        max_error_threshold: int = 5,
        health_check_interval: int = 60
    ):
        """
        Initialize Session Manager.
        
        Args:
            session_timeout_minutes: Minutes of inactivity before session expires
            max_error_threshold: Maximum errors before marking session as failed
            health_check_interval: Seconds between health checks
        """
        self.sessions: Dict[str, SessionState] = {}
        self.session_timeout_minutes = session_timeout_minutes
        self.max_error_threshold = max_error_threshold
        self.health_check_interval = health_check_interval
        self._last_health_check = datetime.now()
        
        logger.info(f"SessionManager initialized with {session_timeout_minutes}min timeout")
    
    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> SessionState:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata
            
        Returns:
            New SessionState object
        """
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists, returning existing")
            return self.sessions[session_id]
        
        session = SessionState(
            session_id=session_id,
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionState if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session and session.is_expired(self.session_timeout_minutes):
            session.status = SessionStatus.EXPIRED
            logger.warning(f"Session {session_id} has expired")
        return session
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session activity timestamp.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if updated, False if session not found or expired
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Cannot update activity: session {session_id} not found")
            return False
        
        if session.status == SessionStatus.EXPIRED:
            logger.warning(f"Cannot update activity: session {session_id} expired")
            return False
        
        session.update_activity()
        return True
    
    def record_session_error(
        self,
        session_id: str,
        error_message: str,
        recovery_action: Optional[Callable] = None
    ) -> bool:
        """
        Record an error for a session and attempt recovery.
        
        Args:
            session_id: Session identifier
            error_message: Error description
            recovery_action: Optional recovery callback
            
        Returns:
            True if recovery successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Cannot record error: session {session_id} not found")
            return False
        
        session.record_error(error_message)
        
        # Attempt recovery if not exceeded threshold
        if session.error_count < self.max_error_threshold:
            if recovery_action:
                try:
                    logger.info(f"Attempting recovery for session {session_id}")
                    recovery_action()
                    session.reset_errors()
                    return True
                except Exception as e:
                    logger.error(f"Recovery failed for session {session_id}: {e}")
                    return False
        else:
            logger.error(
                f"Session {session_id} exceeded error threshold ({self.max_error_threshold})"
            )
            session.status = SessionStatus.DISCONNECTED
        
        return False
    
    def check_health(self, session_id: str) -> Dict[str, Any]:
        """
        Check health status of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with health status information
        """
        session = self.get_session(session_id)
        
        if not session:
            return {
                'status': 'not_found',
                'healthy': False,
                'message': 'Session does not exist',
                'can_recover': False
            }
        
        # Check if expired
        if session.is_expired(self.session_timeout_minutes):
            return {
                'status': 'expired',
                'healthy': False,
                'message': f'Session expired after {self.session_timeout_minutes} minutes of inactivity',
                'can_recover': True,
                'recovery_action': 'restart'
            }
        
        # Check error threshold
        if session.error_count >= self.max_error_threshold:
            return {
                'status': 'failed',
                'healthy': False,
                'message': f'Too many errors ({session.error_count})',
                'can_recover': True,
                'recovery_action': 'reconnect'
            }
        
        # Check if in error state but recoverable
        if session.status == SessionStatus.ERROR:
            return {
                'status': 'error',
                'healthy': False,
                'message': session.last_error or 'Unknown error',
                'can_recover': True,
                'recovery_action': 'retry',
                'error_count': session.error_count
            }
        
        # Check if disconnected
        if session.status == SessionStatus.DISCONNECTED:
            return {
                'status': 'disconnected',
                'healthy': False,
                'message': 'Session is disconnected',
                'can_recover': True,
                'recovery_action': 'reconnect'
            }
        
        # Session is healthy
        idle_time = (datetime.now() - session.last_activity).total_seconds()
        return {
            'status': 'healthy',
            'healthy': True,
            'message': 'Session is active and healthy',
            'idle_seconds': idle_time,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat()
        }
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from memory.
        
        Returns:
            Number of sessions cleaned up
        """
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout_minutes)
        ]
        
        for session_id in expired:
            logger.info(f"Cleaning up expired session: {session_id}")
            del self.sessions[session_id]
        
        return len(expired)
    
    def get_user_friendly_message(self, health_status: Dict[str, Any]) -> str:
        """
        Convert health status to user-friendly message.
        
        Args:
            health_status: Health status dictionary from check_health()
            
        Returns:
            User-friendly status message
        """
        status = health_status.get('status')
        
        messages = {
            'not_found': (
                "⚠️ Session not found. Please refresh the page to start a new session."
            ),
            'expired': (
                "⏱️ Your session has expired due to inactivity. "
                "Please refresh the page to continue."
            ),
            'failed': (
                "❌ Session encountered too many errors and needs to be restarted. "
                "Please refresh the page or contact support if the problem persists."
            ),
            'error': (
                f"⚠️ Session error: {health_status.get('message')}. "
                "Retrying automatically... If this persists, please refresh the page."
            ),
            'disconnected': (
                "🔌 Connection lost. Please check your internet connection and refresh the page."
            ),
            'healthy': (
                "✅ Session is active and running normally."
            )
        }
        
        return messages.get(status, "Unknown session status")
    
    def get_recovery_instructions(self, health_status: Dict[str, Any]) -> Optional[str]:
        """
        Get recovery instructions based on health status.
        
        Args:
            health_status: Health status dictionary from check_health()
            
        Returns:
            Recovery instructions or None if not applicable
        """
        if health_status.get('healthy', False):
            return None
        
        recovery_action = health_status.get('recovery_action')
        
        instructions = {
            'restart': (
                "To restart your session:\n"
                "1. Refresh the page (F5 or Ctrl+R)\n"
                "2. Your work will be preserved in storage\n"
                "3. Re-run any active scans or backtests"
            ),
            'reconnect': (
                "To reconnect:\n"
                "1. Check your internet connection\n"
                "2. Refresh the page\n"
                "3. If problem persists, clear browser cache and try again"
            ),
            'retry': (
                "The system will automatically retry the operation. "
                "If the error persists after several attempts, try refreshing the page."
            )
        }
        
        return instructions.get(recovery_action)


# Global session manager instance
_global_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get or create global session manager instance.
    
    Returns:
        Global SessionManager instance
    """
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


def initialize_session_manager(
    session_timeout_minutes: int = 30,
    max_error_threshold: int = 5
) -> SessionManager:
    """
    Initialize global session manager with custom settings.
    
    Args:
        session_timeout_minutes: Session timeout in minutes
        max_error_threshold: Maximum errors before session failure
        
    Returns:
        Initialized SessionManager instance
    """
    global _global_session_manager
    _global_session_manager = SessionManager(
        session_timeout_minutes=session_timeout_minutes,
        max_error_threshold=max_error_threshold
    )
    return _global_session_manager
