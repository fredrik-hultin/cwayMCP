"""Comprehensive logging configuration for the Cway MCP server."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from config.settings import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class RequestTrackingFilter(logging.Filter):
    """Filter to add request tracking information to log records."""
    
    def __init__(self) -> None:
        super().__init__()
        self.current_request_id: Optional[str] = None
        self.current_operation: Optional[str] = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add tracking information to log record."""
        record.request_id = getattr(self, 'current_request_id', 'N/A')
        record.operation = getattr(self, 'current_operation', 'Unknown')
        return True
    
    def set_request_context(self, request_id: str, operation: str) -> None:
        """Set context for current request."""
        self.current_request_id = request_id
        self.current_operation = operation
        
    def clear_request_context(self) -> None:
        """Clear request context."""
        self.current_request_id = None
        self.current_operation = None


def setup_logging() -> RequestTrackingFilter:
    """
    Set up comprehensive logging configuration.
    
    Returns:
        RequestTrackingFilter: Filter instance for request tracking
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create request tracking filter
    request_filter = RequestTrackingFilter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(request_id)s | %(operation)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(request_filter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "cway_mcp_server.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(request_id)s | %(operation)s | %(name)s | %(levelname)s | %(message)s | %(pathname)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(request_filter)
    root_logger.addHandler(file_handler)
    
    # Separate error log file
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    error_handler.addFilter(request_filter)
    root_logger.addHandler(error_handler)
    
    # API calls log (for tracking all GraphQL calls)
    api_logger = logging.getLogger("cway.api")
    api_handler = logging.handlers.RotatingFileHandler(
        log_dir / "api_calls.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10
    )
    api_formatter = logging.Formatter(
        fmt='%(asctime)s | %(request_id)s | %(operation)s | API_CALL | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    api_handler.setFormatter(api_formatter)
    api_handler.addFilter(request_filter)
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.DEBUG)
    api_logger.propagate = False  # Don't propagate to root logger
    
    # Performance log (for tracking timing)
    perf_logger = logging.getLogger("cway.performance")
    perf_handler = logging.handlers.RotatingFileHandler(
        log_dir / "performance.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    perf_formatter = logging.Formatter(
        fmt='%(asctime)s | %(request_id)s | %(operation)s | PERFORMANCE | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    perf_handler.setFormatter(perf_formatter)
    perf_handler.addFilter(request_filter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.DEBUG)
    perf_logger.propagate = False
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 Cway MCP Server Starting Up")
    logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔧 Log Level: {settings.log_level.upper()}")
    logger.info(f"🌐 API URL: {settings.cway_api_url}")
    logger.info(f"🏠 Server: {settings.mcp_server_host}:{settings.mcp_server_port}")
    logger.info("=" * 80)
    
    return request_filter


def log_api_call(operation: str, query: str, variables: dict = None, response_size: int = 0, duration_ms: float = 0) -> None:
    """Log API call details."""
    api_logger = logging.getLogger("cway.api")
    
    # Clean up the query for logging (remove excessive whitespace)
    clean_query = ' '.join(query.split())
    
    api_logger.info(
        f"GraphQL {operation} | Query: {clean_query[:200]}{'...' if len(clean_query) > 200 else ''} | "
        f"Variables: {variables} | Response Size: {response_size} bytes | Duration: {duration_ms:.2f}ms"
    )


def log_performance(operation: str, duration_ms: float, details: str = "") -> None:
    """Log performance metrics."""
    perf_logger = logging.getLogger("cway.performance")
    perf_logger.info(f"{operation} | Duration: {duration_ms:.2f}ms | {details}")


def log_request_flow(step: str, details: str = "") -> None:
    """Log request flow through the system."""
    logger = logging.getLogger("cway.flow")
    logger.info(f"📍 {step} | {details}")


# Global request filter instance
_request_filter: Optional[RequestTrackingFilter] = None


def get_request_filter() -> Optional[RequestTrackingFilter]:
    """Get the global request filter instance."""
    return _request_filter


def initialize_logging() -> None:
    """Initialize logging system."""
    global _request_filter
    _request_filter = setup_logging()