"""Database connection and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger
from backend.database.models import Base

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./kubera_pokisham.db"  # Fallback to SQLite
)

# Determine if PostgreSQL or SQLite
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")

# Create engine with appropriate settings
if IS_POSTGRESQL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
    logger.info("Using PostgreSQL database", url=DATABASE_URL.split('@')[-1])  # Log without credentials
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool
    )
    logger.info("Using SQLite database", path=DATABASE_URL)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # If PostgreSQL, create TimescaleDB hypertable
    if IS_POSTGRESQL:
        create_hypertables()


def create_hypertables():
    """Create TimescaleDB hypertables for time-series data."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        try:
            # Enable TimescaleDB extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.commit()
            logger.info("TimescaleDB extension enabled")
            
            # Create hypertable for OHLCV data
            conn.execute(text("""
                SELECT create_hypertable(
                    'ohlcv_data',
                    'time',
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """))
            conn.commit()
            logger.info("OHLCV hypertable created")
            
            # Add retention policy (keep 1 year of data)
            conn.execute(text("""
                SELECT add_retention_policy(
                    'ohlcv_data',
                    INTERVAL '1 year',
                    if_not_exists => TRUE
                );
            """))
            conn.commit()
            logger.info("Retention policy added")
            
            # Create continuous aggregate for 1h data from 15m
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1h
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 hour', time) AS bucket,
                    symbol,
                    first(open, time) as open,
                    max(high) as high,
                    min(low) as low,
                    last(close, time) as close,
                    sum(volume) as volume
                FROM ohlcv_data
                WHERE timeframe = '15m'
                GROUP BY bucket, symbol;
            """))
            conn.commit()
            logger.info("Continuous aggregate for 1h created")
            
            # Add refresh policy
            conn.execute(text("""
                SELECT add_continuous_aggregate_policy(
                    'ohlcv_1h',
                    start_offset => INTERVAL '3 hours',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour',
                    if_not_exists => TRUE
                );
            """))
            conn.commit()
            logger.info("Refresh policy added for 1h aggregate")
            
        except Exception as e:
            logger.warning(f"TimescaleDB setup failed (might not be installed)", error=str(e))


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_db():
    """Close database connection."""
    engine.dispose()
    logger.info("Database connection closed")


