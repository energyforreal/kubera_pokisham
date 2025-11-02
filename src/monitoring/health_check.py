"""Health check system for monitoring bot status."""

import json
import tempfile
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict

# Windows compatibility for fcntl
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    # Windows doesn't have fcntl, use alternative locking
    import msvcrt

from src.core.logger import logger, get_component_logger


class HealthCheck:
    """Monitor and report bot health status."""
    
    def __init__(self, health_file: str = "bot_health.json"):
        # Initialize component logger
        self.logger = get_component_logger("monitoring")
        
        self.health_file = Path(health_file)
        self.last_update = None
        self.last_signal_time = None
        self.signal_intervals = []
        self.status = {
            'is_alive': False,
            'last_heartbeat': None,
            'last_signal': None,
            'last_trade': None,
            'errors_count': 0,
            'signals_count': 0,
            'trades_count': 0,
            'uptime_seconds': 0,
            'models_loaded': 0,
            'circuit_breaker_active': False
        }
        self.logger.info("initialization", "Health check system initialized", {"health_file": str(self.health_file)})
    
    def heartbeat(self):
        """Record a heartbeat - bot is alive."""
        now = datetime.now(timezone.utc)
        self.status['is_alive'] = True
        self.status['last_heartbeat'] = now.isoformat()
        self.last_update = now
        self._save()
        
        # Log heartbeat every 10 minutes to avoid spam
        if not hasattr(self, '_last_heartbeat_log') or (now - self._last_heartbeat_log).total_seconds() > 600:
            self.logger.info("heartbeat", "Bot heartbeat recorded", {
                "timestamp": now.isoformat(),
                "uptime_seconds": self.status.get('uptime_seconds', 0)
            })
            self._last_heartbeat_log = now
    
    def record_signal(self, signal: Dict):
        """Record a trading signal generation."""
        now = datetime.now(timezone.utc)
        self.status['last_signal'] = now.isoformat()
        self.status['signals_count'] = self.status.get('signals_count', 0) + 1
        
        # Record signal generation timing for monitoring
        self.record_signal_generation(now)
        self._save()
        
        self.logger.info("signal_recorded", "Trading signal recorded", {
            "signal_type": signal.get('prediction', 'unknown'),
            "confidence": signal.get('confidence', 0),
            "symbol": signal.get('symbol', 'unknown'),
            "signals_count": self.status['signals_count']
        })
    
    def record_signal_generation(self, timestamp: datetime):
        """Record signal generation timing for monitoring."""
        if not hasattr(self, 'signal_intervals'):
            self.signal_intervals = []
        
        if self.last_signal_time:
            interval_seconds = (timestamp - self.last_signal_time).total_seconds()
            self.signal_intervals.append(interval_seconds)
            
            # Keep last 20 intervals
            if len(self.signal_intervals) > 20:
                self.signal_intervals.pop(0)
            
            # Check if running at expected 5-minute intervals
            if len(self.signal_intervals) >= 3:  # Need at least 3 samples
                avg_interval = sum(self.signal_intervals) / len(self.signal_intervals)
                if abs(avg_interval - 300) > 30:  # More than 30s deviation
                    logger.warning(f"Signal interval deviation: avg {avg_interval:.0f}s vs expected 300s")
        
        self.last_signal_time = timestamp
    
    def record_trade(self, trade: Dict):
        """Record a trade execution."""
        self.status['last_trade'] = datetime.now(timezone.utc).isoformat()
        self.status['trades_count'] = self.status.get('trades_count', 0) + 1
        self._save()
    
    def record_error(self, error: str):
        """Record an error occurrence."""
        self.status['errors_count'] = self.status.get('errors_count', 0) + 1
        self.status['last_error'] = {
            'message': str(error),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self._save()
    
    def update_circuit_breaker(self, is_active: bool):
        """Update circuit breaker status."""
        self.status['circuit_breaker_active'] = is_active
        self._save()
    
    def update_models_loaded(self, count: int):
        """Update count of loaded models."""
        self.status['models_loaded'] = count
        self._save()
        logger.info(f"Health check: Models loaded count updated to {count}")
    
    def get_status(self) -> Dict:
        """Get current health status.
        
        Returns:
            Health status dictionary
        """
        # Calculate uptime
        if self.last_update:
            uptime = (datetime.now(timezone.utc) - self.last_update).total_seconds()
            self.status['uptime_seconds'] = uptime
        
        return self.status.copy()
    
    def is_healthy(self, max_age_seconds: int = 120) -> bool:
        """Check if bot is healthy.
        
        Args:
            max_age_seconds: Maximum age of last heartbeat to consider healthy
            
        Returns:
            True if healthy, False otherwise
        """
        if not self.status.get('is_alive'):
            return False
        
        last_heartbeat = self.status.get('last_heartbeat')
        if not last_heartbeat:
            return False
        
        last_heartbeat_dt = datetime.fromisoformat(last_heartbeat)
        age = (datetime.now(timezone.utc) - last_heartbeat_dt).total_seconds()
        
        return age < max_age_seconds
    
    def _save(self):
        """Save health status to file with atomic write."""
        temp_file = None
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Write to temporary file first
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.health_file.parent, suffix='.tmp')
                
                with open(temp_file.name, 'w') as f:
                    if HAS_FCNTL:
                        # Unix/Linux file locking
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        json.dump(self.status, f, indent=2)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    else:
                        # Windows file locking
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                        json.dump(self.status, f, indent=2)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                
                # Atomic move
                temp_file.close()
                
                # Windows: os.rename fails if target exists, need to remove first
                # Unix: os.replace works as atomic replace
                if os.name == 'nt':  # Windows
                    # Try to remove existing file, ignore if it doesn't exist or is locked
                    try:
                        if self.health_file.exists():
                            os.remove(self.health_file)
                    except (OSError, PermissionError):
                        # File might be locked, wait and retry
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            if temp_file and os.path.exists(temp_file.name):
                                os.unlink(temp_file.name)
                            continue
                    
                    # Rename temp file to target
                    try:
                        os.rename(temp_file.name, self.health_file)
                    except OSError:
                        # If rename fails, use shutil.move as fallback
                        import shutil
                        shutil.move(temp_file.name, self.health_file)
                else:
                    # Unix/Linux: use os.replace for atomic operation
                    os.replace(temp_file.name, self.health_file)
                
                logger.debug(f"Health status saved to {self.health_file}")
                return  # Success
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Retry on error
                    if temp_file and os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed
                    logger.error(f"Failed to save health check to {self.health_file}", error=str(e), exc_info=True)
                    # Clean up temp file if it exists
                    if temp_file and os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
    
    def _load(self):
        """Load health status from file."""
        try:
            if self.health_file.exists():
                with open(self.health_file, 'r') as f:
                    self.status = json.load(f)
                logger.debug("Health check status loaded")
        except Exception as e:
            logger.warning(f"Failed to load health check", error=str(e))


# Global health check instance
_health_check = None

def get_health_check() -> HealthCheck:
    """Get global health check instance."""
    global _health_check
    if _health_check is None:
        _health_check = HealthCheck()
    return _health_check

