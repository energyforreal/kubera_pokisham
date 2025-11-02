"""Test script to validate the intelligent trading system components."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all new modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from src.ml.model_coordinator import ModelCoordinator, ModelInfo
        print("✅ ModelCoordinator imported successfully")
    except Exception as e:
        print(f"❌ ModelCoordinator import failed: {e}")
        return False
    
    try:
        from src.ml.cross_timeframe_aggregator import CrossTimeframeAggregator
        print("✅ CrossTimeframeAggregator imported successfully")
    except Exception as e:
        print(f"❌ CrossTimeframeAggregator import failed: {e}")
        return False
    
    try:
        from src.trading.model_position_manager import ModelPositionManager, PositionConfidenceTracker
        print("✅ ModelPositionManager imported successfully")
    except Exception as e:
        print(f"❌ ModelPositionManager import failed: {e}")
        return False
    
    try:
        from src.trading.intelligent_entry import IntelligentEntry
        print("✅ IntelligentEntry imported successfully")
    except Exception as e:
        print(f"❌ IntelligentEntry import failed: {e}")
        return False
    
    try:
        from src.data.multi_timeframe_sync import MultiTimeframeDataSync
        print("✅ MultiTimeframeDataSync imported successfully")
    except Exception as e:
        print(f"❌ MultiTimeframeDataSync import failed: {e}")
        return False
    
    print()
    return True


def test_configuration():
    """Test that configuration is set up correctly."""
    print("=" * 60)
    print("TEST 2: Configuration")
    print("=" * 60)
    
    try:
        from src.core.config import trading_config
        
        # Check strategy
        multi_config = trading_config.model.get('multi_model', {})
        strategy = multi_config.get('strategy', '')
        
        if strategy == 'cross_timeframe_weighted':
            print(f"✅ Strategy set to: {strategy}")
        else:
            print(f"⚠️  Strategy is: {strategy} (expected 'cross_timeframe_weighted')")
            print("   System will work but may use legacy predictor")
        
        # Check models
        models = multi_config.get('models', [])
        print(f"✅ Number of models configured: {len(models)}")
        
        if len(models) == 5:
            print("✅ All 5 models configured")
        else:
            print(f"⚠️  Expected 5 models, found {len(models)}")
        
        # Check timeframes
        timeframes = trading_config.trading.get('timeframes', [])
        print(f"✅ Timeframes: {timeframes}")
        
        # Check intervals
        update_interval = trading_config.trading.get('update_interval')
        entry_interval = trading_config.trading.get('entry_signal_interval')
        print(f"✅ Position monitoring: {update_interval}s (expected 60)")
        print(f"✅ Entry signals: {entry_interval}s (expected 900)")
        
        # Check model-driven exits
        model_exits = trading_config.get('model_driven_exits', {})
        enabled = model_exits.get('enabled', False)
        use_fixed = model_exits.get('use_fixed_sl_tp', True)
        
        if enabled and not use_fixed:
            print("✅ Model-driven exits: ENABLED")
        else:
            print(f"⚠️  Model-driven exits: enabled={enabled}, use_fixed_sl_tp={use_fixed}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_model_files():
    """Test that all required model files exist."""
    print("=" * 60)
    print("TEST 3: Model Files")
    print("=" * 60)
    
    required_models = [
        "models/xgboost_BTCUSD_15m.pkl",
        "models/xgboost_BTCUSD_1h.pkl",
        "models/randomforest_BTCUSD_4h_production_20251014_125258.pkl",
        "models/xgboost_BTCUSD_4h_production_20251014_114541.pkl",
        "models/lightgbm_BTCUSD_4h_production_20251014_115655.pkl"
    ]
    
    all_exist = True
    for model_path in required_models:
        if Path(model_path).exists():
            size_mb = Path(model_path).stat().st_size / (1024 * 1024)
            print(f"✅ {model_path} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {model_path} - NOT FOUND")
            all_exist = False
    
    print()
    return all_exist


def test_component_initialization():
    """Test that components can be initialized."""
    print("=" * 60)
    print("TEST 4: Component Initialization")
    print("=" * 60)
    
    try:
        from src.ml.cross_timeframe_aggregator import CrossTimeframeAggregator
        aggregator = CrossTimeframeAggregator()
        print("✅ CrossTimeframeAggregator initialized")
    except Exception as e:
        print(f"❌ CrossTimeframeAggregator failed: {e}")
        return False
    
    try:
        from src.trading.model_position_manager import ModelPositionManager
        pos_mgr = ModelPositionManager()
        print("✅ ModelPositionManager initialized")
    except Exception as e:
        print(f"❌ ModelPositionManager failed: {e}")
        return False
    
    try:
        from src.trading.intelligent_entry import IntelligentEntry
        entry_engine = IntelligentEntry()
        print("✅ IntelligentEntry initialized")
    except Exception as e:
        print(f"❌ IntelligentEntry failed: {e}")
        return False
    
    try:
        from src.data.multi_timeframe_sync import MultiTimeframeDataSync
        sync = MultiTimeframeDataSync()
        print("✅ MultiTimeframeDataSync initialized")
    except Exception as e:
        print(f"❌ MultiTimeframeDataSync failed: {e}")
        return False
    
    print()
    return True


def test_model_coordinator():
    """Test ModelCoordinator with actual model loading."""
    print("=" * 60)
    print("TEST 5: ModelCoordinator (with model loading)")
    print("=" * 60)
    print("⚠️  This test loads all 5 models - may take 10-30 seconds...")
    print()
    
    try:
        from src.ml.model_coordinator import ModelCoordinator
        
        coordinator = ModelCoordinator()
        
        # Check models loaded
        total_models = len(coordinator.all_models)
        print(f"✅ Total models loaded: {total_models}")
        
        # Check by timeframe
        for timeframe in ['15m', '1h', '4h']:
            count = len(coordinator.models_by_timeframe[timeframe])
            print(f"   - {timeframe}: {count} model(s)")
        
        # Validate health
        health = coordinator.validate_model_health()
        print(f"✅ Healthy models: {health['healthy_models']}/{health['total_models']}")
        
        if health['all_healthy']:
            print("✅ All models healthy")
        else:
            print(f"⚠️  Some models unhealthy: {health['unhealthy_models']}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ ModelCoordinator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation tests."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "INTELLIGENT TRADING SYSTEM VALIDATOR" + " " * 11 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = []
    
    # Test 1: Imports
    results.append(("Module Imports", test_imports()))
    
    # Test 2: Configuration
    results.append(("Configuration", test_configuration()))
    
    # Test 3: Model Files
    results.append(("Model Files", test_model_files()))
    
    # Test 4: Component Initialization
    results.append(("Component Init", test_component_initialization()))
    
    # Test 5: Model Coordinator (heavy test)
    results.append(("Model Loading", test_model_coordinator()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ Your intelligent trading system is ready to run!")
        print()
        print("Next steps:")
        print("  1. Run: python -m src.main")
        print("  2. Or:  start_SIMPLE.bat")
        print("  3. Watch for: '🧠 Initializing INTELLIGENT MULTI-TIMEFRAME SYSTEM'")
        print()
        print("Documentation:")
        print("  - INTELLIGENT_AGENT_IMPLEMENTATION.md (full details)")
        print("  - INTELLIGENT_SYSTEM_QUICK_START.md (quick start)")
        print()
        return True
    else:
        print()
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Please fix the issues above before running the trading agent.")
        print()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

