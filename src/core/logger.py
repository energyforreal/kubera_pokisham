"""Enhanced logging configuration for Kubera Pokisham with component-level logging."""

import json
import logging
import logging.handlers
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
import gzip
import shutil

import structlog
from structlog.typing import FilteringBoundLogger, EventDict

from src.core.config import settings


class ComponentLogger:
    """Component-aware logger with dedicated log files, rotation, and cleanup."""
    
    _instances = {}
    _lock = threading.Lock()
    _session_id = None
    
    def __init__(self, component_name: str, log_level: str = "INFO"):
        self.component_name = component_name
        self.log_level = log_level
        self.log_dir = Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create component-specific logger
        self.logger = logging.getLogger(f"component.{component_name}")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create JSON file handler with rotation
        log_file = self.log_dir / f"{component_name}_{datetime.now().strftime('%Y%m%d')}.json"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8',
            utc=True
        )
        
        # Set formatter to JSON
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Add console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    @classmethod
    def get_logger(cls, component_name: str, log_level: str = "INFO") -> 'ComponentLogger':
        """Get or create component logger instance."""
        with cls._lock:
            if component_name not in cls._instances:
                cls._instances[component_name] = cls(component_name, log_level)
            return cls._instances[component_name]
    
    @classmethod
    def get_session_id(cls) -> str:
        """Get or create session ID for this run."""
        if cls._session_id is None:
            cls._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        return cls._session_id
    
    def log(self, level: str, operation: str, message: str, context: Optional[Dict] = None, 
            duration_ms: Optional[float] = None, error: Optional[Exception] = None):
        """Log structured message with component context."""
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()
        
        log_data = {
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_local": now_local.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "component": self.component_name,
            "level": level.upper(),
            "operation": operation,
            "message": message,
            "session_id": self.get_session_id(),
            "context": context or {},
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if error is not None:
            log_data["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": self._get_traceback(error)
            }
        
        # Log using appropriate level
        log_level = getattr(logging, level.upper())
        self.logger.log(log_level, json.dumps(log_data, ensure_ascii=False))
    
    def info(self, operation: str, message: str, context: Optional[Dict] = None, duration_ms: Optional[float] = None):
        """Log info level message."""
        self.log("INFO", operation, message, context, duration_ms)
    
    def warning(self, operation: str, message: str, context: Optional[Dict] = None, duration_ms: Optional[float] = None):
        """Log warning level message."""
        self.log("WARNING", operation, message, context, duration_ms)
    
    def error(self, operation: str, message: str, context: Optional[Dict] = None, 
              duration_ms: Optional[float] = None, error: Optional[Exception] = None):
        """Log error level message."""
        self.log("ERROR", operation, message, context, duration_ms, error)
    
    def debug(self, operation: str, message: str, context: Optional[Dict] = None, duration_ms: Optional[float] = None):
        """Log debug level message."""
        self.log("DEBUG", operation, message, context, duration_ms)
    
    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback for error."""
        import traceback
        return traceback.format_exc()
    
    def log_performance(self, operation: str, start_time: float, context: Optional[Dict] = None):
        """Log performance metrics."""
        duration_ms = (time.time() - start_time) * 1000
        self.info(operation, f"Operation completed in {duration_ms:.2f}ms", context, duration_ms)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        try:
            # If message is already JSON, return as is
            if isinstance(record.msg, str) and record.msg.startswith('{'):
                return record.msg
            else:
                # Convert to JSON
                log_data = {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "component": getattr(record, 'component', 'unknown')
                }
                return json.dumps(log_data, ensure_ascii=False)
        except Exception:
            return f"{record.levelname}: {record.getMessage()}"


class ConsoleFormatter(logging.Formatter):
    """Console formatter for human-readable output."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def cleanup_logs_on_startup() -> Dict[str, Any]:
    """Clean up old log files on startup and create startup log."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    cleanup_stats = {
        "files_deleted": 0,
        "space_freed_bytes": 0,
        "errors": []
    }
    
    try:
        # Delete all .log and .json files
        for file_path in log_dir.glob("*.log"):
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                cleanup_stats["files_deleted"] += 1
                cleanup_stats["space_freed_bytes"] += file_size
            except Exception as e:
                cleanup_stats["errors"].append(f"Failed to delete {file_path}: {e}")
        
        for file_path in log_dir.glob("*.json"):
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                cleanup_stats["files_deleted"] += 1
                cleanup_stats["space_freed_bytes"] += file_size
            except Exception as e:
                cleanup_stats["errors"].append(f"Failed to delete {file_path}: {e}")
        
        # Create startup log
        startup_logger = ComponentLogger.get_logger("startup")
        startup_logger.info(
            "system_startup",
            "Trading agent system started",
            {
                "cleanup_stats": cleanup_stats,
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "environment": os.environ.get("ENVIRONMENT", "development")
            }
        )
        
        return cleanup_stats
        
    except Exception as e:
        cleanup_stats["errors"].append(f"Startup cleanup failed: {e}")
        return cleanup_stats


def add_local_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add both UTC and local timestamps to log events.
    
    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary
        
    Returns:
        Updated event dictionary with timestamps
    """
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    
    # Format: YYYY-MM-DD HH:MM:SS TZ
    event_dict["timestamp_utc"] = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    event_dict["timestamp_local"] = now_local.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # Keep ISO format for compatibility
    event_dict["timestamp"] = now_utc.isoformat()
    
    return event_dict


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> FilteringBoundLogger:
    """Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        
    Returns:
        Configured logger instance
    """
    level = log_level or settings.log_level
    file_path = log_file or settings.log_file
    
    # Create logs directory if it doesn't exist
    log_dir = Path(file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Add file handler
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(getattr(logging, level.upper()))
    logging.root.addHandler(file_handler)
    
    # Configure structlog with enhanced timestamp
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            add_local_timestamp,  # Custom timestamp processor
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if level.upper() == "DEBUG" else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


# Create global logger instance
logger = setup_logging()

# Initialize component loggers
def get_component_logger(component_name: str, log_level: str = "INFO") -> ComponentLogger:
    """Get component-specific logger."""
    return ComponentLogger.get_logger(component_name, log_level)

