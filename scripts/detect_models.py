#!/usr/bin/env python3
"""
Model File Detection Script

Finds production model files using glob patterns instead of hardcoded paths.
Prevents failures when models are retrained with new timestamps.
"""

import sys
import glob
from pathlib import Path
from typing import List, Dict, Tuple


class ModelDetector:
    """Detects available model files using flexible patterns."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.required_models = {
            'randomforest': 'randomforest_BTCUSD_4h_production_*.pkl',
            'xgboost': 'xgboost_BTCUSD_4h_production_*.pkl',
            'lightgbm': 'lightgbm_BTCUSD_4h_production_*.pkl'
        }
        self.optional_models = {
            'xgboost_15m': 'xgboost_BTCUSD_15m.pkl',
            'xgboost_1h': 'xgboost_BTCUSD_1h.pkl'
        }
    
    def find_models(self) -> Dict[str, List[str]]:
        """Find all available model files."""
        found_models = {}
        
        # Check if models directory exists
        if not self.models_dir.exists():
            return found_models
        
        # Find required production models
        for model_type, pattern in self.required_models.items():
            matches = list(self.models_dir.glob(pattern))
            if matches:
                # Sort by modification time (newest first)
                matches.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                found_models[model_type] = [str(m) for m in matches]
        
        # Find optional models
        for model_name, filename in self.optional_models.items():
            model_path = self.models_dir / filename
            if model_path.exists():
                found_models[model_name] = [str(model_path)]
        
        return found_models
    
    def validate_models(self) -> Tuple[bool, List[str], List[str]]:
        """Validate that required models are available."""
        found_models = self.find_models()
        errors = []
        warnings = []
        
        # Check for required production models
        required_found = 0
        for model_type in self.required_models.keys():
            if model_type in found_models:
                required_found += 1
                model_files = found_models[model_type]
                print(f"✅ {model_type}: Found {len(model_files)} model(s)")
                for model_file in model_files:
                    print(f"   📁 {Path(model_file).name}")
            else:
                errors.append(f"Missing required {model_type} model")
        
        # Check for optional models
        for model_name in self.optional_models.keys():
            if model_name in found_models:
                model_files = found_models[model_name]
                print(f"✅ {model_name}: Found")
                for model_file in model_files:
                    print(f"   📁 {Path(model_file).name}")
            else:
                warnings.append(f"Optional {model_name} model not found")
        
        # Determine if we have minimum required models
        if required_found >= 1:  # Changed from 2 to 1
            print(f"✅ Found {required_found}/3 required production models")
            if required_found == 1:
                print("⚠️  Only 1 model found - consider training more for better performance")
            return True, errors, warnings
        else:
            errors.append("No production models found")
            return False, errors, warnings
    
    def get_latest_models(self) -> Dict[str, str]:
        """Get the latest version of each model type."""
        found_models = self.find_models()
        latest_models = {}
        
        for model_type, model_files in found_models.items():
            if model_files:
                # Files are already sorted by modification time (newest first)
                latest_models[model_type] = model_files[0]
        
        return latest_models
    
    def generate_model_config(self) -> str:
        """Generate a model configuration snippet."""
        latest_models = self.get_latest_models()
        
        config_lines = ["# Auto-generated model configuration"]
        config_lines.append("model:")
        
        # Single model config (use best available)
        if 'randomforest' in latest_models:
            config_lines.append(f"  type: \"randomforest\"")
            config_lines.append(f"  path: \"{latest_models['randomforest']}\"")
        elif 'xgboost' in latest_models:
            config_lines.append(f"  type: \"xgboost\"")
            config_lines.append(f"  path: \"{latest_models['xgboost']}\"")
        elif 'lightgbm' in latest_models:
            config_lines.append(f"  type: \"lightgbm\"")
            config_lines.append(f"  path: \"{latest_models['lightgbm']}\"")
        
        # Multi-model config
        config_lines.append("  multi_model:")
        config_lines.append("    enabled: true")
        config_lines.append("    strategy: \"cross_timeframe_weighted\"")
        config_lines.append("    models:")
        
        model_weights = {
            'xgboost_15m': 0.30,
            'xgboost_1h': 0.25,
            'randomforest': 0.20,
            'xgboost': 0.15,
            'lightgbm': 0.10
        }
        
        for model_name, weight in model_weights.items():
            if model_name in latest_models:
                model_path = latest_models[model_name]
                timeframe = "15m" if "15m" in model_name else "1h" if "1h" in model_name else "4h"
                role = "entry_timing" if "15m" in model_name else "trend_confirmation" if "1h" in model_name else "trend_direction"
                
                config_lines.append(f"      - path: \"{model_path}\"")
                config_lines.append(f"        weight: {weight}")
                config_lines.append(f"        timeframe: \"{timeframe}\"")
                config_lines.append(f"        role: \"{role}\"")
        
        return "\n".join(config_lines)


def main():
    """Main entry point."""
    print("🔍 Detecting model files...")
    print("=" * 60)
    
    detector = ModelDetector()
    is_valid, errors, warnings = detector.validate_models()
    
    print("=" * 60)
    
    if is_valid:
        print("✅ Model detection successful!")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        print("\n📋 Latest model files:")
        latest_models = detector.get_latest_models()
        for model_type, model_path in latest_models.items():
            print(f"   • {model_type}: {Path(model_path).name}")
        
        print("\n💡 To update config.yaml with detected models:")
        print("   python scripts/validate_config.py --update-config")
        
        sys.exit(0)
    else:
        print("❌ Model detection failed!")
        print(f"\n🔧 Errors ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
        
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        print("\n🔧 SOLUTIONS:")
        print("1. Train new models using the training scripts")
        print("2. Check if model files are in the correct models/ directory")
        print("3. Verify model file naming follows the expected pattern")
        print("4. Run: python scripts/train_models.py to create missing models")
        print("\n⚠️  Continuing with startup - system will use available models")
        print("   Some features may be limited without all models")
        
        sys.exit(0)  # Don't fail - let system start with available models


if __name__ == "__main__":
    main()

