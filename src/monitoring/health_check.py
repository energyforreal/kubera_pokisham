"""Health check system for monitoring bot status."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict

from src.core.logger import logger


class HealthCheck:
    """Monitor and report bot health status."""
    
    def __init__(self, health_file: str = "bot_health.json"):
        self.health_file = Path(health_file)
        self.last_update = None
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
    
    def heartbeat(self):
        """Record a heartbeat - bot is alive."""
        now = datetime.now(timezone.utc)
        self.status['is_alive'] = True
        self.status['last_heartbeat'] = now.isoformat()
        self.last_update = now
        self._save()
        logger.debug("Health check heartbeat recorded")
    
    def record_signal(self, signal: Dict):
        """Record a trading signal generation."""
        self.status['last_signal'] = datetime.now(timezone.utc).isoformat()
        self.status['signals_count'] = self.status.get('signals_count', 0) + 1
        self._save()
    
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
        """Save health status to file."""
        try:
            with open(self.health_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health check", error=str(e))
    
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

