"""Performance metrics tracking for the trading bot."""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import contextmanager

from src.core.logger import logger


class PerformanceMetrics:
    """Track and report performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'api_calls': [],
            'predictions': [],
            'feature_engineering': [],
            'total_iterations': 0,
            'errors': 0
        }
        self.start_time = time.time()
    
    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure operation duration.
        
        Usage:
            with metrics.measure('api_call'):
                # do something
        """
        start = time.time()
        operation_info = {'operation': operation, 'start': start}
        
        try:
            yield operation_info
            duration = time.time() - start
            operation_info['duration'] = duration
            operation_info['success'] = True
            
            # Store metric
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(duration)
            
            # Log if slow
            if duration > 5.0:  # More than 5 seconds
                logger.warning(
                    f"Slow operation detected",
                    operation=operation,
                    duration_seconds=f"{duration:.2f}",
                    threshold="5s"
                )
            else:
                logger.debug(
                    f"Operation completed",
                    operation=operation,
                    duration_ms=f"{duration*1000:.0f}"
                )
                
        except Exception as e:
            duration = time.time() - start
            operation_info['duration'] = duration
            operation_info['success'] = False
            operation_info['error'] = str(e)
            
            logger.error(
                f"Operation failed",
                operation=operation,
                duration_seconds=f"{duration:.2f}",
                error=str(e)
            )
            raise
    
    def record_api_call(self, duration: float, endpoint: str, success: bool = True):
        """Record an API call."""
        self.metrics['api_calls'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration': duration,
            'endpoint': endpoint,
            'success': success
        })
        
        # Keep only last 100 records
        if len(self.metrics['api_calls']) > 100:
            self.metrics['api_calls'] = self.metrics['api_calls'][-100:]
    
    def record_prediction(self, duration: float, model: str = 'single'):
        """Record a prediction operation."""
        self.metrics['predictions'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration': duration,
            'model': model
        })
        
        # Keep only last 100 records
        if len(self.metrics['predictions']) > 100:
            self.metrics['predictions'] = self.metrics['predictions'][-100:]
    
    def get_summary(self) -> Dict:
        """Get performance summary.
        
        Returns:
            Dictionary with performance statistics
        """
        summary = {
            'uptime_seconds': time.time() - self.start_time,
            'total_iterations': self.metrics['total_iterations'],
            'total_errors': self.metrics['errors']
        }
        
        # API call stats
        if self.metrics['api_calls']:
            api_durations = [call['duration'] for call in self.metrics['api_calls']]
            summary['api_calls'] = {
                'count': len(api_durations),
                'avg_duration_ms': sum(api_durations) / len(api_durations) * 1000,
                'max_duration_ms': max(api_durations) * 1000,
                'min_duration_ms': min(api_durations) * 1000
            }
        
        # Prediction stats
        if self.metrics['predictions']:
            pred_durations = [p['duration'] for p in self.metrics['predictions']]
            summary['predictions'] = {
                'count': len(pred_durations),
                'avg_duration_ms': sum(pred_durations) / len(pred_durations) * 1000,
                'max_duration_ms': max(pred_durations) * 1000,
                'min_duration_ms': min(pred_durations) * 1000
            }
        
        return summary
    
    def log_summary(self):
        """Log performance summary."""
        summary = self.get_summary()
        logger.info(
            "Performance summary",
            uptime_hours=summary['uptime_seconds'] / 3600,
            iterations=summary['total_iterations'],
            errors=summary['total_errors'],
            api_avg_ms=summary.get('api_calls', {}).get('avg_duration_ms', 0),
            pred_avg_ms=summary.get('predictions', {}).get('avg_duration_ms', 0)
        )


# Global metrics instance
_metrics = None

def get_metrics() -> PerformanceMetrics:
    """Get global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics

