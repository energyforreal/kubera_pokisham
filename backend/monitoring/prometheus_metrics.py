"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
from functools import wraps
from typing import Callable
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Trading Metrics
trades_total = Counter(
    'trades_total',
    'Total number of trades executed',
    ['symbol', 'side', 'status']
)

pnl_total = Gauge(
    'pnl_total',
    'Total profit/loss in USD'
)

portfolio_balance = Gauge(
    'portfolio_balance',
    'Current portfolio balance in USD'
)

portfolio_equity = Gauge(
    'portfolio_equity',
    'Current portfolio equity (balance + unrealized P&L) in USD'
)

open_positions = Gauge(
    'open_positions',
    'Number of currently open positions'
)

portfolio_drawdown_percent = Gauge(
    'portfolio_drawdown_percent',
    'Current drawdown percentage'
)

win_rate = Gauge(
    'trading_win_rate',
    'Trading win rate (percentage of winning trades)'
)

# Model Performance Metrics
model_inference_duration = Histogram(
    'model_inference_duration_seconds',
    'Model inference time in seconds',
    ['model_name'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

model_predictions_total = Counter(
    'model_predictions_total',
    'Total number of model predictions',
    ['model_name', 'prediction']
)

model_accuracy = Gauge(
    'model_accuracy',
    'Model prediction accuracy',
    ['model_name']
)

ensemble_agreement = Gauge(
    'ensemble_agreement',
    'Agreement level among ensemble models (0-1)'
)

# API Performance Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

api_errors_total = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['endpoint', 'error_type']
)

# Circuit Breaker Metrics
circuit_breaker_active = Gauge(
    'circuit_breaker_active',
    'Whether circuit breaker is currently active (1) or not (0)',
    ['breaker_type']
)

circuit_breaker_triggers = Counter(
    'circuit_breaker_triggers_total',
    'Total number of circuit breaker triggers',
    ['breaker_type']
)

# Risk Metrics
var_95 = Gauge(
    'var_95',
    'Value at Risk at 95% confidence level'
)

cvar_95 = Gauge(
    'cvar_95',
    'Conditional Value at Risk at 95% confidence level'
)

sharpe_ratio = Gauge(
    'sharpe_ratio',
    'Sharpe ratio of trading strategy'
)

sortino_ratio = Gauge(
    'sortino_ratio',
    'Sortino ratio of trading strategy'
)

max_drawdown = Gauge(
    'max_drawdown',
    'Maximum drawdown in USD'
)

# Data Quality Metrics
data_fetch_errors = Counter(
    'data_fetch_errors_total',
    'Total number of data fetching errors',
    ['source', 'symbol']
)

data_quality_score = Gauge(
    'data_quality_score',
    'Data quality score (0-1)',
    ['symbol', 'timeframe']
)

# System Health Metrics
system_uptime_seconds = Gauge(
    'system_uptime_seconds',
    'System uptime in seconds'
)

last_heartbeat_timestamp = Gauge(
    'last_heartbeat_timestamp',
    'Timestamp of last system heartbeat'
)

# Database Metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_in_use = Gauge(
    'db_connection_pool_in_use',
    'Number of database connections currently in use'
)

db_connection_pool_exhausted = Gauge(
    'db_connection_pool_exhausted',
    'Whether database connection pool is exhausted (1) or not (0)'
)

# Cache Metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_level']  # L1, L2
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_level']
)

cache_size = Gauge(
    'cache_size',
    'Current cache size',
    ['cache_level']
)

# WebSocket Metrics
websocket_connections = Gauge(
    'websocket_connections',
    'Number of active WebSocket connections'
)

websocket_messages_sent = Counter(
    'websocket_messages_sent_total',
    'Total number of WebSocket messages sent',
    ['message_type']
)

# Application Info
app_info = Info(
    'app_info',
    'Application version and configuration'
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

class MetricsCollector:
    """Helper class to collect and update metrics."""
    
    @staticmethod
    def record_trade(trade_data: dict):
        """Record a trade execution."""
        symbol = trade_data.get('symbol', 'unknown')
        side = trade_data.get('side', 'unknown')
        status = trade_data.get('status', 'unknown')
        
        trades_total.labels(symbol=symbol, side=side, status=status).inc()
        
        if status == 'filled':
            logger.debug("Trade metric recorded", symbol=symbol, side=side)
    
    @staticmethod
    def update_portfolio(portfolio_data: dict):
        """Update portfolio metrics."""
        portfolio_balance.set(portfolio_data.get('balance', 0))
        portfolio_equity.set(portfolio_data.get('equity', 0))
        open_positions.set(portfolio_data.get('num_positions', 0))
        pnl_total.set(portfolio_data.get('total_pnl', 0))
        
        # Calculate drawdown percentage
        total_pnl_pct = portfolio_data.get('total_pnl_percent', 0)
        if total_pnl_pct < 0:
            portfolio_drawdown_percent.set(abs(total_pnl_pct))
        else:
            portfolio_drawdown_percent.set(0)
    
    @staticmethod
    def record_model_prediction(model_name: str, prediction: str, inference_time: float):
        """Record model prediction."""
        model_predictions_total.labels(model_name=model_name, prediction=prediction).inc()
        model_inference_duration.labels(model_name=model_name).observe(inference_time)
    
    @staticmethod
    def update_ensemble_metrics(agreement_level: float):
        """Update ensemble model metrics."""
        ensemble_agreement.set(agreement_level)
    
    @staticmethod
    def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
        """Record API request."""
        api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_api_error(endpoint: str, error_type: str):
        """Record API error."""
        api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()
    
    @staticmethod
    def update_circuit_breaker(breaker_type: str, is_active: bool):
        """Update circuit breaker status."""
        circuit_breaker_active.labels(breaker_type=breaker_type).set(1 if is_active else 0)
        
        if is_active:
            circuit_breaker_triggers.labels(breaker_type=breaker_type).inc()
    
    @staticmethod
    def update_risk_metrics(risk_data: dict):
        """Update risk metrics."""
        var_95.set(risk_data.get('var_95', 0))
        cvar_95.set(risk_data.get('cvar_95', 0))
        sharpe_ratio.set(risk_data.get('sharpe_ratio', 0))
        sortino_ratio.set(risk_data.get('sortino_ratio', 0))
        max_drawdown.set(risk_data.get('max_drawdown', 0))
    
    @staticmethod
    def record_data_fetch_error(source: str, symbol: str):
        """Record data fetching error."""
        data_fetch_errors.labels(source=source, symbol=symbol).inc()
    
    @staticmethod
    def update_data_quality(symbol: str, timeframe: str, quality_score: float):
        """Update data quality score."""
        data_quality_score.labels(symbol=symbol, timeframe=timeframe).set(quality_score)
    
    @staticmethod
    def update_system_health(uptime: float, heartbeat: float):
        """Update system health metrics."""
        system_uptime_seconds.set(uptime)
        last_heartbeat_timestamp.set(heartbeat)
    
    @staticmethod
    def update_cache_metrics(cache_stats: dict):
        """Update cache metrics."""
        if 'l1_size' in cache_stats:
            cache_size.labels(cache_level='L1').set(cache_stats['l1_size'])
        if 'l2_size' in cache_stats:
            cache_size.labels(cache_level='L2').set(cache_stats.get('l2_size', 0))
    
    @staticmethod
    def record_cache_hit(cache_level: str):
        """Record cache hit."""
        cache_hits.labels(cache_level=cache_level).inc()
    
    @staticmethod
    def record_cache_miss(cache_level: str):
        """Record cache miss."""
        cache_misses.labels(cache_level=cache_level).inc()
    
    @staticmethod
    def update_websocket_connections(count: int):
        """Update WebSocket connection count."""
        websocket_connections.set(count)
    
    @staticmethod
    def record_websocket_message(message_type: str):
        """Record WebSocket message sent."""
        websocket_messages_sent.labels(message_type=message_type).inc()
    
    @staticmethod
    def set_app_info(version: str, environment: str, models_loaded: int):
        """Set application info."""
        app_info.info({
            'version': version,
            'environment': environment,
            'models_loaded': str(models_loaded)
        })


# Decorator for timing functions
def time_metric(metric: Histogram, labels: dict = None):
    """Decorator to time function execution and record to histogram."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_response() -> Response:
    """Get Prometheus metrics in exposition format."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


