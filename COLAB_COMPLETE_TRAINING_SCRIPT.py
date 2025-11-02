"""
COMPLETE TRAINING SCRIPT FOR GOOGLE COLAB
==========================================

Copy this entire script into a single Google Colab cell and run it.
It will train all 8 ML models and package them for download.

Models trained:
- XGBoost (3 timeframes)
- LightGBM (3 timeframes)  
- CatBoost (3 timeframes)
- Random Forest (3 timeframes)
- LSTM with Attention (2 timeframes) - GPU recommended
- Transformer (optional) - Disabled by default

Total: 10-14 model files depending on configuration
"""

# ============================================================================
# CONFIGURATION - EDIT THESE
# ============================================================================

SYMBOL = 'BTCUSD'
TIMEFRAMES = ['15m', '1h']  # Add '4h' if needed
HISTORICAL_DAYS = 365

# Enable/disable models (set to False to skip)
TRAIN_MODELS = {
    'xgboost': True,
    'lightgbm': True,
    'catboost': True,
    'random_forest': True,
    'lstm_attention': True,  # Requires GPU for reasonable speed
    'transformer': False,     # Very slow, disabled by default
}

# ============================================================================
# IMPORTS
# ============================================================================

import os
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
import torch

# Add project to path
sys.path.insert(0, os.getcwd())

# Import project modules
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.ml.xgboost_model import XGBoostTradingModel

# Import ML frameworks
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import joblib

# Try importing new models
try:
    from ml_pipeline.models.ensemble.lightgbm_model import LightGBMTrader
    from ml_pipeline.models.ensemble.catboost_model import CatBoostTrader
    from ml_pipeline.models.ensemble.random_forest import RandomForestTrader
    from ml_pipeline.models.deep_learning.lstm_attention import LSTMAttentionTrader
    from ml_pipeline.models.deep_learning.transformer import TransformerTrader
    NEW_MODELS = True
except ImportError as e:
    print(f"⚠️  New models not available: {e}")
    NEW_MODELS = False

# Check GPU
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

print("="*70)
print("🚀 AI TRADING AGENT - COMPLETE MODEL TRAINING")
print("="*70)
print(f"\\nDevice: {DEVICE.upper()}")
if DEVICE == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Symbol: {SYMBOL}")
print(f"Timeframes: {TIMEFRAMES}")
print(f"Models to train: {[k for k, v in TRAIN_MODELS.items() if v]}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_target(df, forward_periods=3):
    """Create target variable."""
    df['future_return'] = df['close'].shift(-forward_periods) / df['close'] - 1
    df['target'] = 1  # HOLD
    df.loc[df['future_return'] > 0.01, 'target'] = 2  # BUY
    df.loc[df['future_return'] < -0.01, 'target'] = 0  # SELL
    return df.iloc[:-forward_periods]


def split_data(df, train_ratio=0.7, val_ratio=0.15):
    """Split into train/val/test."""
    total = len(df)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


def prepare_for_model(df, target_col='target'):
    """Prepare features and target."""
    exclude = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 
               'volume', 'future_return', target_col]
    features = [c for c in df.columns if c not in exclude]
    X = df[features].replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(0)
    return X.values, df[target_col].values, features


# ============================================================================
# FETCH DATA
# ============================================================================

print("\\n" + "="*70)
print("📥 FETCHING DATA")
print("="*70)

delta_client = DeltaExchangeClient()
feature_engineer = FeatureEngineer()
validator = DataValidator()

datasets = {}
for tf in tqdm(TIMEFRAMES, desc="Fetching data"):
    df = delta_client.get_ohlc_candles(SYMBOL, tf, limit=HISTORICAL_DAYS * 100)
    df, metrics = validator.validate_and_clean(df)
    df = feature_engineer.create_features(df)
    df = create_target(df)
    datasets[tf] = df
    print(f"  ✓ {tf}: {len(df)} samples, {len(df.columns)} features")

# ============================================================================
# TRAIN ALL MODELS
# ============================================================================

all_results = []

for timeframe in TIMEFRAMES:
    print(f"\\n{'='*70}")
    print(f"📊 TIMEFRAME: {timeframe}")
    print(f"{'='*70}")
    
    df = datasets[timeframe]
    train_df, val_df, test_df = split_data(df)
    X_train, y_train, features = prepare_for_model(train_df)
    X_val, y_val, _ = prepare_for_model(val_df)
    X_test, y_test, _ = prepare_for_model(test_df)
    
    # 1. XGBoost
    if TRAIN_MODELS['xgboost']:
        print(f"\\n[1/6] Training XGBoost...")
        start = time.time()
        model = XGBoostTradingModel()
        model.scaler = StandardScaler()
        X_train_s = model.scaler.fit_transform(X_train)
        X_test_s = model.scaler.transform(X_test)
        model.model = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                    objective='multi:softprob', num_class=3, n_jobs=-1, random_state=42)
        model.model.fit(X_train_s, y_train, verbose=False)
        test_acc = (model.model.predict(X_test_s) == y_test).mean()
        model_file = f"models/xgboost_{SYMBOL}_{timeframe}.pkl"
        model.save(model_file)
        all_results.append({'model': 'XGBoost', 'tf': timeframe, 'test_acc': test_acc, 
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")
    
    # 2. LightGBM
    if TRAIN_MODELS['lightgbm'] and NEW_MODELS:
        print(f"\\n[2/6] Training LightGBM...")
        start = time.time()
        model = LightGBMTrader()
        model.train(X_train, y_train, X_val, y_val)
        test_pred, _ = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        model_file = f"models/lightgbm_{SYMBOL}_{timeframe}.txt"
        model.save(model_file)
        all_results.append({'model': 'LightGBM', 'tf': timeframe, 'test_acc': test_acc,
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")
    
    # 3. CatBoost
    if TRAIN_MODELS['catboost'] and NEW_MODELS:
        print(f"\\n[3/6] Training CatBoost...")
        start = time.time()
        model = CatBoostTrader()
        model.train(X_train, y_train, X_val, y_val)
        test_pred, _ = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        model_file = f"models/catboost_{SYMBOL}_{timeframe}.cbm"
        model.save(model_file)
        all_results.append({'model': 'CatBoost', 'tf': timeframe, 'test_acc': test_acc,
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")
    
    # 4. Random Forest
    if TRAIN_MODELS['random_forest'] and NEW_MODELS:
        print(f"\\n[4/6] Training Random Forest...")
        start = time.time()
        model = RandomForestTrader()
        model.train(X_train, y_train)
        test_pred, _ = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        model_file = f"models/randomforest_{SYMBOL}_{timeframe}.pkl"
        model.save(model_file)
        all_results.append({'model': 'RandomForest', 'tf': timeframe, 'test_acc': test_acc,
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")
    
    # 5. LSTM Attention
    if TRAIN_MODELS['lstm_attention'] and NEW_MODELS:
        print(f"\\n[5/6] Training LSTM with Attention on {DEVICE.upper()}...")
        if DEVICE == 'cpu':
            print("  ⚠️  WARNING: This will take 1-2 hours on CPU!")
        start = time.time()
        model = LSTMAttentionTrader(input_dim=len(features), device=DEVICE)
        model.train(X_train, y_train, X_val, y_val, epochs=30, batch_size=32)
        test_pred, _ = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        model_file = f"models/lstm_attention_{SYMBOL}_{timeframe}.pth"
        model.save(model_file)
        all_results.append({'model': 'LSTM_Attention', 'tf': timeframe, 'test_acc': test_acc,
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")
    
    # 6. Transformer
    if TRAIN_MODELS['transformer'] and NEW_MODELS:
        print(f"\\n[6/6] Training Transformer on {DEVICE.upper()}...")
        start = time.time()
        model = TransformerTrader(input_dim=len(features), device=DEVICE)
        model.train(X_train, y_train, X_val, y_val, epochs=30, batch_size=32)
        test_pred, _ = model.predict(X_test)
        test_acc = (test_pred == y_test).mean()
        model_file = f"models/transformer_{SYMBOL}_{timeframe}.pth"
        model.save(model_file)
        all_results.append({'model': 'Transformer', 'tf': timeframe, 'test_acc': test_acc,
                           'time': time.time()-start, 'file': model_file})
        print(f"  ✅ Acc: {test_acc:.4f}, Time: {time.time()-start:.1f}s")

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

results_df = pd.DataFrame(all_results)
results_df.columns = ['Model', 'Timeframe', 'Test Accuracy', 'Training Time (s)', 'File']

print("\\n" + "="*70)
print("📊 TRAINING SUMMARY")
print("="*70)
print(results_df.to_string(index=False))
print(f"\\n✅ Trained {len(all_results)} models successfully!")

# Save summary
results_df.to_csv('training_summary.csv', index=False)

# ============================================================================
# CREATE ZIP FOR DOWNLOAD
# ============================================================================

zip_name = f'all_models_{SYMBOL}_{datetime.now().strftime("%Y%m%d_%H%M")}.zip'

print(f"\\n📦 Creating ZIP: {zip_name}")
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for _, row in results_df.iterrows():
        model_file = row['File']
        if os.path.exists(model_file):
            zipf.write(model_file, arcname=model_file)
            size_mb = os.path.getsize(model_file) / (1024*1024)
            print(f"  ✓ {os.path.basename(model_file)} ({size_mb:.1f} MB)")
    
    zipf.write('training_summary.csv')

zip_size = os.path.getsize(zip_name) / (1024*1024)
print(f"\\n✅ ZIP created: {zip_name} ({zip_size:.1f} MB)")

# Download in Colab
try:
    from google.colab import files
    print(f"\\n⬇️  Downloading...")
    files.download(zip_name)
    print("✅ Download started! Check your browser.")
except:
    print(f"\\n✓ File ready: {zip_name}")

print("\\n🎉 TRAINING COMPLETE!")
print("\\nNext steps:")
print("1. Extract the ZIP file on your local machine")
print("2. Copy model files to your project's models/ directory")
print("3. Update config/config.yaml with new model paths")
print("4. Run your trading agent!")

