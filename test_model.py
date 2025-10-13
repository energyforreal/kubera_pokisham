"""Quick test to verify models work."""
from src.ml.xgboost_model import XGBoostTradingModel

print("🔍 Testing model loading...\n")

# Test 15m model
model_15m = XGBoostTradingModel()
model_15m.load("models/xgboost_BTCUSD_15m.pkl")
print(f"✅ 15m model: {len(model_15m.feature_names)} features")

# Test 1h model  
model_1h = XGBoostTradingModel()
model_1h.load("models/xgboost_BTCUSD_1h.pkl")
print(f"✅ 1h model: {len(model_1h.feature_names)} features")

print("\n🎉 All models loaded successfully!")
