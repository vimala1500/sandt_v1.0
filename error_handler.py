"""
Error Handler Module
====================
Provides robust error handling, user-friendly error messages, and recovery strategies.
"""

import logging
import traceback
from typing import Callable, Any, Optional, Tuple, Dict
from functools import wraps
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ApplicationError(Exception):
    """Base class for application-specific errors."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None
    ):
        super().__init__(message)
        self.severity = severity
        self.user_message = user_message or message
        self.recovery_hint = recovery_hint


class SessionError(ApplicationError):
    """Session-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            **kwargs
        )


class BackendProcessError(ApplicationError):
    """Backend process errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            **kwargs
        )


class DataLoadError(ApplicationError):
    """Data loading errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.WARNING,
            **kwargs
        )


def with_error_handling(
    user_friendly_message: str = "An error occurred",
    recovery_action: Optional[Callable] = None,
    raise_on_error: bool = False,
    default_return: Any = None
):
    """
    Decorator for adding error handling to functions.
    
    Args:
        user_friendly_message: Message to show users
        recovery_action: Optional recovery callback
        raise_on_error: Whether to re-raise exceptions
        default_return: Default return value on error
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApplicationError as e:
                # Handle our custom errors
                logger.error(
                    f"ApplicationError in {func.__name__}: {e}",
                    exc_info=True
                )
                
                # Attempt recovery
                if recovery_action:
                    try:
                        recovery_action()
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}")
                
                if raise_on_error:
                    raise
                
                return default_return
                
            except Exception as e:
                # Handle unexpected errors
                logger.error(
                    f"Unexpected error in {func.__name__}: {e}",
                    exc_info=True
                )
                
                if raise_on_error:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    error_message: str = "Operation failed",
    default_value: Any = None,
    **kwargs
) -> Tuple[bool, Any, Optional[str]]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        error_message: Base error message
        default_value: Value to return on error
        **kwargs: Function keyword arguments
        
    Returns:
        Tuple of (success, result, error_message)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except ApplicationError as e:
        logger.error(f"{error_message}: {e}")
        return False, default_value, e.user_message
    except Exception as e:
        logger.error(f"{error_message}: {e}", exc_info=True)
        user_msg = f"{error_message}. Please try again or contact support if the issue persists."
        return False, default_value, user_msg


def get_user_friendly_error(error: Exception) -> str:
    """
    Convert exception to user-friendly error message.
    
    Args:
        error: Exception object
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, ApplicationError):
        return error.user_message
    
    # Map common errors to user-friendly messages
    error_type = type(error).__name__
    error_str = str(error).lower()
    
    if 'connection' in error_str or 'timeout' in error_str:
        return (
            "🔌 Connection issue detected. "
            "Please check your internet connection and try again."
        )
    
    if 'file not found' in error_str or 'no such file' in error_str:
        return (
            "📁 Required data file not found. "
            "Please ensure data is properly loaded or refresh the page."
        )
    
    if 'permission' in error_str or 'access denied' in error_str:
        return (
            "🔒 Permission denied. "
            "Please check file permissions or contact your administrator."
        )
    
    if 'memory' in error_str or 'out of memory' in error_str:
        return (
            "💾 Insufficient memory. "
            "Try processing fewer items at once or restart the application."
        )
    
    if 'value' in error_str and 'error' in error_str:
        return (
            "⚠️ Invalid input value. "
            "Please check your inputs and try again."
        )
    
    # Generic fallback
    return (
        f"❌ An unexpected error occurred ({error_type}). "
        "Please refresh the page or contact support if the issue persists."
    )


def format_error_for_ui(
    error: Exception,
    context: Optional[str] = None,
    include_recovery: bool = True
) -> Dict[str, Any]:
    """
    Format error for UI display.
    
    Args:
        error: Exception object
        context: Additional context information
        include_recovery: Whether to include recovery instructions
        
    Returns:
        Dictionary with formatted error information
    """
    user_message = get_user_friendly_error(error)
    
    result = {
        'type': type(error).__name__,
        'message': user_message,
        'severity': 'error',
        'timestamp': None  # Can be set by caller
    }
    
    if context:
        result['context'] = context
    
    if isinstance(error, ApplicationError):
        result['severity'] = error.severity.value
        if include_recovery and error.recovery_hint:
            result['recovery_hint'] = error.recovery_hint
    
    return result


def create_error_banner(
    message: str,
    severity: str = "error",
    recovery_hint: Optional[str] = None
) -> str:
    """
    Create HTML error banner for Dash UI.
    
    Args:
        message: Error message to display
        severity: Severity level (info, warning, error, critical)
        recovery_hint: Optional recovery instructions
        
    Returns:
        HTML string for error banner
    """
    color_map = {
        'info': 'info',
        'warning': 'warning',
        'error': 'danger',
        'critical': 'danger'
    }
    
    icon_map = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'critical': '🚨'
    }
    
    color = color_map.get(severity, 'danger')
    icon = icon_map.get(severity, '❌')
    
    html = f'<div class="alert alert-{color}" role="alert">'
    html += f'  <strong>{icon} {message}</strong>'
    
    if recovery_hint:
        html += f'<br><small>{recovery_hint}</small>'
    
    html += '</div>'
    
    return html


class RetryStrategy:
    """Implements retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for delay after each attempt
            max_delay: Maximum delay between attempts
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (success, result, error_message)
        """
        import time
        
        delay = self.initial_delay
        last_error = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 1:
                    logger.info(f"Retry succeeded on attempt {attempt}")
                return True, result, None
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt}/{self.max_attempts} failed: {e}"
                )
                
                if attempt < self.max_attempts:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
        
        # All attempts failed
        error_msg = get_user_friendly_error(last_error)
        return False, None, error_msg


def handle_callback_error(
    error: Exception,
    callback_name: str,
    session_manager=None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle errors in Dash callbacks.
    
    Args:
        error: Exception that occurred
        callback_name: Name of the callback
        session_manager: Optional session manager instance
        session_id: Optional session ID
        
    Returns:
        Dictionary with error information for UI
    """
    logger.error(f"Error in callback {callback_name}: {error}", exc_info=True)
    
    # Record error in session if available
    if session_manager and session_id:
        session_manager.record_session_error(
            session_id=session_id,
            error_message=f"{callback_name}: {str(error)}"
        )
    
    # Format error for UI
    error_info = format_error_for_ui(error, context=callback_name)
    
    return error_info
