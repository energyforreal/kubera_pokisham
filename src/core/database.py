"""Database models and connection management - Enhanced unified schema."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Index,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from contextlib import asynccontextmanager

from src.core.config import settings

# Create base class for models
Base = declarative_base()


class OHLCVData(Base):
    """OHLCV candle data - supports TimescaleDB."""
    
    __tablename__ = "ohlcv_data"
    
    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_symbol_time', 'symbol', 'time'),
        Index('idx_timeframe_time', 'timeframe', 'time'),
    )
    
    # Alias for compatibility
    @property
    def timestamp(self):
        return self.time


class Trade(Base):
    """Trade execution records - enhanced with ML metadata."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    size = Column(Float, nullable=False)
    pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    close_reason = Column(String(50), nullable=True)  # 'stop_loss', 'take_profit', 'signal', 'manual'
    is_closed = Column(Boolean, default=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    holding_period = Column(Integer, nullable=True)  # seconds
    
    # ML metadata
    signal_confidence = Column(Float, nullable=True)
    model_predictions = Column(Text, nullable=True)  # JSON string
    market_conditions = Column(Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_is_closed_timestamp', 'is_closed', 'timestamp'),
    )
    
    # Alias for backward compatibility
    @property
    def exit_timestamp(self):
        return self.closed_at


class Position(Base):
    """Active trading position."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    side = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relation to trade
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=True)
    trade = relationship("Trade", backref="position")


class PerformanceMetrics(Base):
    """Daily performance metrics."""
    
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    balance = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    daily_pnl_percent = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    num_trades = Column(Integer, default=0)
    num_wins = Column(Integer, default=0)
    num_losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    sortino_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    consecutive_losses = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_date', 'date'),
    )


class ModelPrediction(Base):
    """ML model predictions log - for tracking model performance."""
    
    __tablename__ = "model_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    model_name = Column(String(50), nullable=False)
    prediction = Column(String(10), nullable=False)  # 'BUY', 'SELL', 'HOLD'
    confidence = Column(Float, nullable=False)
    features_used = Column(Text, nullable=True)  # JSON string
    actual_outcome = Column(String(10), nullable=True)  # Set after trade closes
    is_correct = Column(Boolean, nullable=True)
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_model_timestamp', 'model_name', 'timestamp'),
    )


class CircuitBreakerEvent(Base):
    """Circuit breaker trigger events - for risk management tracking."""
    
    __tablename__ = "circuit_breaker_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    breaker_type = Column(String(50), nullable=False)  # 'daily_loss', 'drawdown', etc.
    reason = Column(Text, nullable=False)
    portfolio_balance = Column(Float, nullable=False)
    metrics = Column(Text, nullable=True)  # JSON string
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
    )


# ---------------------------------------------------------------------------
# Equity snapshots - lightweight time series for real risk metrics
# ---------------------------------------------------------------------------
class EquitySnapshot(Base):
    """Timestamped equity snapshots for risk metric calculations.

    This provides a reliable data source for Sharpe/Sortino/Drawdown even
    when there are few or no closed trades. Snapshots are small and fast.
    """

    __tablename__ = "equity_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    equity = Column(Float, nullable=False)
    balance = Column(Float, nullable=True)
    note = Column(String, nullable=True)

    __table_args__ = (
        Index('idx_equity_timestamp', 'timestamp'),
    )


# Database engine and session
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_db_session():
    """Async context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Export for easy imports
__all__ = [
    'Base',
    'OHLCVData',
    'Trade',
    'Position',
    'PerformanceMetrics',
    'ModelPrediction',
    'CircuitBreakerEvent',
    'engine',
    'SessionLocal',
    'init_db',
    'get_db',
    'get_db_session',
]

