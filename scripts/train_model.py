"""Train XGBoost model on historical data."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.logger import logger
from src.ml.trainer import ModelTrainer


def main():
    """Train the model."""
    parser = argparse.ArgumentParser(description='Train XGBoost trading model')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe')
    parser.add_argument('--days', type=int, default=365, help='Number of days of historical data')
    parser.add_argument('--output', type=str, default=None, help='Output model path')
    parser.add_argument('--walk-forward', action='store_true', help='Run walk-forward validation')
    
    args = parser.parse_args()
    
    # Set output path
    output_path = args.output or settings.model_path
    
    logger.info(f"Training model for {args.symbol} ({args.timeframe})")
    logger.info(f"Using {args.days} days of historical data")
    
    try:
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Prepare training data
        logger.info("Preparing training data...")
        df = trainer.prepare_training_data(
            symbol=args.symbol,
            timeframe=args.timeframe,
            days=args.days
        )
        
        if df.empty:
            logger.error("No training data available")
            return
        
        logger.info(f"Training data prepared: {len(df)} samples")
        
        # Walk-forward validation
        if args.walk_forward:
            logger.info("Running walk-forward validation...")
            results = trainer.walk_forward_validation(df, n_splits=5)
            
            avg_accuracy = sum(r['accuracy'] for r in results) / len(results)
            logger.info(f"Walk-forward validation accuracy: {avg_accuracy:.4f}")
            
            for result in results:
                logger.info(f"Fold {result['fold']}: {result['accuracy']:.4f}")
        
        # Train final model
        logger.info("Training final model...")
        model = trainer.train_model(df, save_path=output_path)
        
        # Show feature importance
        importance = model.get_feature_importance(top_n=10)
        logger.info("Top 10 features:")
        for _, row in importance.iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        
        logger.info(f"✅ Model training complete!")
        logger.info(f"✅ Model saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Model training failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

