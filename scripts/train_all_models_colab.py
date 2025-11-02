"""
Complete ML Model Training Script for Google Colab
Trains all 8 models: XGBoost, LightGBM, CatBoost, Random Forest, LSTM, Transformer

Usage in Colab:
    !python scripts/train_all_models_colab.py
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.getcwd())

# Import all required libraries
from sklearn.preprocessing import StandardScaler
import torch
import joblib

# Import project modules
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.ml.xgboost_model import XGBoostTradingModel

# Try to import new model classes
try:
    from ml_pipeline.models.ensemble.lightgbm_model import LightGBMTrader
    from ml_pipeline.models.ensemble.catboost_model import CatBoostTrader
    from ml_pipeline.models.ensemble.random_forest import RandomForestTrader
    from ml_pipeline.models.deep_learning.lstm_attention import LSTMAttentionTrader
    from ml_pipeline.models.deep_learning.transformer import TransformerTrader
    NEW_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Some model classes not available: {e}")
    NEW_MODELS_AVAILABLE = False

# Configuration
SYMBOL = 'BTCUSD'
TIMEFRAMES = ['15m', '1h']
HISTORICAL_DAYS = 365
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Model selection
MODELS_TO_TRAIN = {
    'xgboost': True,
    'lightgbm': True and NEW_MODELS_AVAILABLE,
    'catboost': True and NEW_MODELS_AVAILABLE,
    'random_forest': True and NEW_MODELS_AVAILABLE,
    'lstm_attention': True and NEW_MODELS_AVAILABLE and torch.cuda.is_available(),  # Requires GPU
    'transformer': False,  # Disabled by default (too slow)
}

# Training parameters
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15


def create_target(df, forward_periods=3):
    """Create target variable based on future returns."""
    df['future_return'] = df['close'].shift(-forward_periods) / df['close'] - 1
    
    buy_threshold = 0.01
    sell_threshold = -0.01
    
    df['target'] = 1  # Default HOLD
    df.loc[df['future_return'] > buy_threshold, 'target'] = 2  # BUY
    df.loc[df['future_return'] < sell_threshold, 'target'] = 0  # SELL
    
    df = df.iloc[:-forward_periods]
    return df


def split_data(df, train_ratio=0.7, val_ratio=0.15):
    """Split data into train, val, test sets."""
    total = len(df)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))
    
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


def prepare_for_model(df, target_col='target'):
    """Prepare features and target for model training."""
    exclude_cols = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume',
                   'future_return', target_col]
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(method='ffill').fillna(0)
    
    return X.values, y.values, feature_cols


def train_xgboost(X_train, y_train, X_val, y_val, X_test, y_test, timeframe):
    """Train XGBoost model."""
    print(f"\\n🔄 Training XGBoost...")
    start_time = time.time()
    
    model = XGBoostTradingModel()
    model.scaler = StandardScaler()
    X_train_scaled = model.scaler.fit_transform(X_train)
    X_val_scaled = model.scaler.transform(X_val)
    X_test_scaled = model.scaler.transform(X_test)
    
    from xgboost import XGBClassifier
    model.model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        objective='multi:softprob', num_class=3, random_state=42, n_jobs=-1
    )
    model.model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
    
    train_acc = (model.model.predict(X_train_scaled) == y_train).mean()
    val_acc = (model.model.predict(X_val_scaled) == y_val).mean()
    test_acc = (model.model.predict(X_test_scaled) == y_test).mean()
    
    model_file = f"models/xgboost_{SYMBOL}_{timeframe}.pkl"
    model.save(model_file)
    
    return {
        'model_name': 'XGBoost',
        'timeframe': timeframe,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'test_accuracy': test_acc,
        'training_time': time.time() - start_time,
        'model_file': model_file
    }


def train_ensemble_model(model_class, model_name, X_train, y_train, X_val, y_val, X_test, y_test, timeframe):
    """Train ensemble models (LightGBM, CatBoost, Random Forest)."""
    print(f"\\n🔄 Training {model_name}...")
    start_time = time.time()
    
    model = model_class()
    model.train(X_train, y_train, X_val, y_val)
    
    train_pred, _ = model.predict(X_train)
    val_pred, _ = model.predict(X_val)
    test_pred, _ = model.predict(X_test)
    
    train_acc = (train_pred == y_train).mean()
    val_acc = (val_pred == y_val).mean()
    test_acc = (test_pred == y_test).mean()
    
    ext = '.txt' if model_name == 'LightGBM' else ('.cbm' if model_name == 'CatBoost' else '.pkl')
    model_file = f"models/{model_name.lower().replace(' ', '_')}_{SYMBOL}_{timeframe}{ext}"
    model.save(model_file)
    
    return {
        'model_name': model_name,
        'timeframe': timeframe,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'test_accuracy': test_acc,
        'training_time': time.time() - start_time,
        'model_file': model_file
    }


def train_deep_learning_model(model_class, model_name, X_train, y_train, X_val, y_val, X_test, y_test, 
                               timeframe, input_dim):
    """Train deep learning models (LSTM, Transformer)."""
    print(f"\\n🔄 Training {model_name} on {DEVICE.upper()}...")
    print(f"   ⏰ This may take 10-20 minutes...")
    start_time = time.time()
    
    model = model_class(input_dim=input_dim, sequence_length=60, device=DEVICE)
    model.train(X_train, y_train, X_val, y_val, epochs=30, batch_size=32, learning_rate=0.001)
    
    train_pred, _ = model.predict(X_train)
    val_pred, _ = model.predict(X_val)
    test_pred, _ = model.predict(X_test)
    
    train_acc = (train_pred == y_train).mean()
    val_acc = (val_pred == y_val).mean()
    test_acc = (test_pred == y_test).mean()
    
    model_file = f"models/{model_name.lower().replace(' ', '_')}_{SYMBOL}_{timeframe}.pth"
    model.save(model_file)
    
    return {
        'model_name': model_name,
        'timeframe': timeframe,
        'train_accuracy': train_acc,
        'val_accuracy': val_acc,
        'test_accuracy': test_acc,
        'training_time': time.time() - start_time,
        'model_file': model_file
    }


def main():
    """Main training loop."""
    print("="*70)
    print("🚀 AI Trading Agent - Complete Model Training")
    print("="*70)
    print(f"\\nDevice: {DEVICE.upper()}")
    print(f"Models to train: {[k for k, v in MODELS_TO_TRAIN.items() if v]}")
    print(f"Timeframes: {TIMEFRAMES}\\n")
    
    # Initialize data pipeline
    delta_client = DeltaExchangeClient()
    feature_engineer = FeatureEngineer()
    validator = DataValidator()
    
    # Fetch and prepare data
    datasets = {}
    for tf in tqdm(TIMEFRAMES, desc="Fetching data"):
        df = delta_client.get_ohlc_candles(SYMBOL, tf, limit=HISTORICAL_DAYS * 100)
        df, _ = validator.validate_and_clean(df)
        df = feature_engineer.create_features(df)
        df = create_target(df)
        datasets[tf] = df
        print(f"  ✓ {tf}: {len(df)} samples")
    
    # Train all models
    all_results = []
    
    for timeframe in TIMEFRAMES:
        print(f"\\n{'='*70}")
        print(f"📊 TIMEFRAME: {SYMBOL} - {timeframe}")
        print(f"{'='*70}")
        
        df = datasets[timeframe]
        train_df, val_df, test_df = split_data(df, TRAIN_RATIO, VAL_RATIO)
        X_train, y_train, feature_names = prepare_for_model(train_df)
        X_val, y_val, _ = prepare_for_model(val_df)
        X_test, y_test, _ = prepare_for_model(test_df)
        input_dim = len(feature_names)
        
        # 1. XGBoost
        if MODELS_TO_TRAIN['xgboost']:
            result = train_xgboost(X_train, y_train, X_val, y_val, X_test, y_test, timeframe)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
        
        # 2. LightGBM
        if MODELS_TO_TRAIN['lightgbm']:
            result = train_ensemble_model(LightGBMTrader, 'LightGBM', X_train, y_train, X_val, y_val, 
                                         X_test, y_test, timeframe)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
        
        # 3. CatBoost
        if MODELS_TO_TRAIN['catboost']:
            result = train_ensemble_model(CatBoostTrader, 'CatBoost', X_train, y_train, X_val, y_val,
                                         X_test, y_test, timeframe)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
        
        # 4. Random Forest
        if MODELS_TO_TRAIN['random_forest']:
            result = train_ensemble_model(RandomForestTrader, 'RandomForest', X_train, y_train, X_val, y_val,
                                         X_test, y_test, timeframe)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
        
        # 5. LSTM Attention
        if MODELS_TO_TRAIN['lstm_attention']:
            result = train_deep_learning_model(LSTMAttentionTrader, 'LSTM_Attention', X_train, y_train,
                                               X_val, y_val, X_test, y_test, timeframe, input_dim)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
        
        # 6. Transformer
        if MODELS_TO_TRAIN['transformer']:
            result = train_deep_learning_model(TransformerTrader, 'Transformer', X_train, y_train,
                                               X_val, y_val, X_test, y_test, timeframe, input_dim)
            all_results.append(result)
            print(f"  ✅ Test Acc: {result['test_accuracy']:.4f}, Time: {result['training_time']:.1f}s")
    
    # Display results
    results_df = pd.DataFrame(all_results)
    print(f"\\n\\n{'='*70}")
    print("📊 TRAINING SUMMARY")
    print(f"{'='*70}")
    print(results_df.to_string(index=False))
    print(f"\\n✅ Training complete! Trained {len(all_results)} models")
    print(f"📁 Model files saved in: models/")
    
    # Save summary
    results_df.to_csv('training_summary.csv', index=False)
    print(f"✅ Summary saved to: training_summary.csv")


if __name__ == "__main__":
    main()

