#!/bin/bash
# Script to train all ML models

set -e

echo "🤖 Training All ML Models"
echo "========================="

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create models directory
mkdir -p models

# 1. Train XGBoost (existing)
echo "📊 Training XGBoost models..."
python scripts/train_model.py --symbol BTCUSD --timeframe 15m --days 365
python scripts/train_model.py --symbol BTCUSD --timeframe 1h --days 365

# 2. Train LightGBM
echo "📊 Training LightGBM..."
python -c "
from ml_pipeline.models.ensemble.lightgbm_model import LightGBMTrader
from scripts.download_data import download_and_prepare_data
import numpy as np

X_train, y_train, X_val, y_val, X_test, y_test = download_and_prepare_data('BTCUSD', '15m', 365)
model = LightGBMTrader()
model.train(X_train, y_train, X_val, y_val)
model.save('models/lightgbm_BTCUSD_15m.txt')
print('✓ LightGBM model saved')
"

# 3. Train CatBoost
echo "📊 Training CatBoost..."
python -c "
from ml_pipeline.models.ensemble.catboost_model import CatBoostTrader
from scripts.download_data import download_and_prepare_data

X_train, y_train, X_val, y_val, X_test, y_test = download_and_prepare_data('BTCUSD', '15m', 365)
model = CatBoostTrader()
model.train(X_train, y_train, X_val, y_val)
model.save('models/catboost_BTCUSD_15m.cbm')
print('✓ CatBoost model saved')
"

# 4. Train Random Forest
echo "📊 Training Random Forest..."
python -c "
from ml_pipeline.models.ensemble.random_forest import RandomForestTrader
from scripts.download_data import download_and_prepare_data

X_train, y_train, X_val, y_val, X_test, y_test = download_and_prepare_data('BTCUSD', '15m', 365)
model = RandomForestTrader()
model.train(X_train, y_train)
model.save('models/random_forest_BTCUSD_15m.pkl')
print('✓ Random Forest model saved')
"

echo ""
echo "✅ All models trained successfully!"
echo "📁 Models saved in ./models/"
echo ""
echo "Trained models:"
ls -lh models/


