"""Initialize database tables."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import init_db
from src.core.logger import logger


def main():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    try:
        init_db()
        logger.info("✅ Database initialized successfully!")
        logger.info("Tables created: ohlcv_data, trades, positions, performance_metrics, model_predictions")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

