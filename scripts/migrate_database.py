"""Database migration script to upgrade to unified schema.

This script migrates from the old schema to the enhanced unified schema.
It preserves existing data while adding new fields and indexes.
"""

import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.database import Base, Trade, Position, PerformanceMetrics
from src.core.logger import logger


def backup_database():
    """Create a backup of the current database."""
    db_path = settings.database_url.replace('sqlite:///', '')
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise


def check_existing_schema(engine):
    """Check what tables and columns exist."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    logger.info("Existing tables:", tables=existing_tables)
    
    for table in existing_tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        logger.info(f"Table '{table}' columns:", columns=columns)
    
    return existing_tables


def migrate_trades_table(engine):
    """Migrate trades table to new schema."""
    inspector = inspect(engine)
    
    if 'trades' not in inspector.get_table_names():
        logger.info("Trades table doesn't exist, will be created fresh")
        return
    
    existing_columns = {col['name'] for col in inspector.get_columns('trades')}
    logger.info("Existing trades columns:", columns=list(existing_columns))
    
    # Add new columns if they don't exist
    new_columns = {
        'model_predictions': 'TEXT',
        'market_conditions': 'TEXT',
    }
    
    with engine.connect() as conn:
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE trades ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    logger.info(f"Added column: {col_name}")
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
        
        # Rename columns if needed (SQLite doesn't support direct rename in old versions)
        # We'll handle this through the property aliases in the model
        
        logger.info("Trades table migration complete")


def migrate_performance_metrics_table(engine):
    """Migrate performance_metrics table to new schema."""
    inspector = inspect(engine)
    
    if 'performance_metrics' not in inspector.get_table_names():
        logger.info("Performance metrics table doesn't exist, will be created fresh")
        return
    
    existing_columns = {col['name'] for col in inspector.get_columns('performance_metrics')}
    logger.info("Existing performance_metrics columns:", columns=list(existing_columns))
    
    # Add new columns
    new_columns = {
        'sortino_ratio': 'FLOAT DEFAULT 0.0',
    }
    
    with engine.connect() as conn:
        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE performance_metrics ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    logger.info(f"Added column: {col_name}")
                except Exception as e:
                    logger.warning(f"Could not add column {col_name}: {e}")
        
        # Rename total_trades to num_trades if needed
        if 'total_trades' in existing_columns and 'num_trades' not in existing_columns:
            try:
                # SQLite doesn't support column rename in older versions
                # We'll create new column and copy data
                conn.execute(text("ALTER TABLE performance_metrics ADD COLUMN num_trades INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE performance_metrics SET num_trades = total_trades"))
                conn.commit()
                logger.info("Migrated total_trades to num_trades")
            except Exception as e:
                logger.warning(f"Could not rename total_trades: {e}")
        
        # Similarly for winning_trades -> num_wins and losing_trades -> num_losses
        if 'winning_trades' in existing_columns and 'num_wins' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE performance_metrics ADD COLUMN num_wins INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE performance_metrics SET num_wins = winning_trades"))
                conn.commit()
                logger.info("Migrated winning_trades to num_wins")
            except Exception as e:
                logger.warning(f"Could not rename winning_trades: {e}")
        
        if 'losing_trades' in existing_columns and 'num_losses' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE performance_metrics ADD COLUMN num_losses INTEGER DEFAULT 0"))
                conn.execute(text("UPDATE performance_metrics SET num_losses = losing_trades"))
                conn.commit()
                logger.info("Migrated losing_trades to num_losses")
            except Exception as e:
                logger.warning(f"Could not rename losing_trades: {e}")
        
        logger.info("Performance metrics table migration complete")


def migrate_positions_table(engine):
    """Migrate positions table to new schema."""
    inspector = inspect(engine)
    
    if 'positions' not in inspector.get_table_names():
        logger.info("Positions table doesn't exist, will be created fresh")
        return
    
    existing_columns = {col['name'] for col in inspector.get_columns('positions')}
    logger.info("Existing positions columns:", columns=list(existing_columns))
    
    # Add trade_id foreign key if it doesn't exist
    if 'trade_id' not in existing_columns:
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE positions ADD COLUMN trade_id INTEGER"))
                conn.commit()
                logger.info("Added trade_id column to positions")
            except Exception as e:
                logger.warning(f"Could not add trade_id: {e}")
    
    # Rename entry_timestamp to timestamp if needed
    if 'entry_timestamp' in existing_columns and 'timestamp' not in existing_columns:
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE positions ADD COLUMN timestamp DATETIME"))
                conn.execute(text("UPDATE positions SET timestamp = entry_timestamp"))
                conn.commit()
                logger.info("Migrated entry_timestamp to timestamp")
            except Exception as e:
                logger.warning(f"Could not rename entry_timestamp: {e}")
    
    logger.info("Positions table migration complete")


def create_new_tables(engine):
    """Create any new tables that don't exist."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    # Create all tables defined in Base
    Base.metadata.create_all(bind=engine)
    
    new_tables = set(inspector.get_table_names()) - existing_tables
    if new_tables:
        logger.info("Created new tables:", tables=list(new_tables))
    else:
        logger.info("No new tables needed")


def main():
    """Run the migration."""
    logger.info("=" * 60)
    logger.info("Starting Database Migration")
    logger.info("=" * 60)
    
    try:
        # Create engine
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
        )
        
        # Check existing schema
        logger.info("\n--- Checking Existing Schema ---")
        existing_tables = check_existing_schema(engine)
        
        # Backup database
        logger.info("\n--- Creating Backup ---")
        backup_path = backup_database()
        
        # Migrate existing tables
        logger.info("\n--- Migrating Existing Tables ---")
        migrate_trades_table(engine)
        migrate_performance_metrics_table(engine)
        migrate_positions_table(engine)
        
        # Create new tables
        logger.info("\n--- Creating New Tables ---")
        create_new_tables(engine)
        
        # Verify migration
        logger.info("\n--- Verifying Migration ---")
        check_existing_schema(engine)
        
        logger.info("=" * 60)
        logger.info("Migration Complete!")
        logger.info(f"Backup saved at: {backup_path}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Migration failed!", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

