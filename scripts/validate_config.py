#!/usr/bin/env python3
"""
Configuration File Validator

Validates config.yaml syntax, required fields, and data types.
Prevents cryptic errors during startup due to invalid configuration.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple


class ConfigValidator:
    """Validates configuration file structure and content."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.errors = []
        self.warnings = []
        self.config_data = None
    
    def validate_file_exists(self) -> bool:
        """Check if config file exists."""
        if not self.config_path.exists():
            self.errors.append(f"Configuration file not found: {self.config_path}")
            print("💡 SOLUTION: Copy config/env.example to config/config.yaml and customize it")
            return False
        return True
    
    def validate_yaml_syntax(self) -> bool:
        """Check if YAML syntax is valid."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading config file: {e}")
            return False
    
    def validate_required_sections(self) -> bool:
        """Check if all required sections exist."""
        required_sections = ['trading', 'model', 'risk_management']
        missing_sections = []
        
        for section in required_sections:
            if section not in self.config_data:
                missing_sections.append(section)
        
        if missing_sections:
            self.errors.append(f"Missing required sections: {missing_sections}")
            return False
        
        return True
    
    def validate_trading_config(self) -> bool:
        """Validate trading configuration section."""
        trading = self.config_data.get('trading', {})
        valid = True
        
        # Required fields
        required_fields = {
            'symbol': str,
            'initial_balance': (int, float),
            'mode': str,
            'update_interval': int
        }
        
        for field, expected_type in required_fields.items():
            if field not in trading:
                self.errors.append(f"Trading config missing required field: {field}")
                valid = False
            elif not isinstance(trading[field], expected_type):
                self.errors.append(f"Trading.{field} should be {expected_type.__name__}, got {type(trading[field]).__name__}")
                valid = False
        
        # Validate specific values
        if 'symbol' in trading:
            symbol = trading['symbol']
            if not symbol or not isinstance(symbol, str):
                self.errors.append("Trading.symbol should be non-empty string")
                valid = False
        
        if 'initial_balance' in trading:
            balance = trading['initial_balance']
            if not isinstance(balance, (int, float)) or balance <= 0:
                self.errors.append("Trading.initial_balance should be positive number")
                valid = False
        
        if 'mode' in trading:
            mode = trading['mode']
            if mode not in ['paper', 'live']:
                self.warnings.append(f"Trading.mode '{mode}' is unusual (expected 'paper' or 'live')")
        
        if 'update_interval' in trading:
            interval = trading['update_interval']
            if not isinstance(interval, int) or interval < 60:
                self.warnings.append(f"Trading.update_interval {interval}s is very short (minimum recommended: 60s)")
        
        return valid
    
    def validate_model_config(self) -> bool:
        """Validate model configuration section."""
        model = self.config_data.get('model', {})
        valid = True
        
        # Check single model config
        if 'path' in model:
            model_path = Path(model['path'])
            if not model_path.exists():
                self.warnings.append(f"Model file not found: {model_path}")
                print(f"💡 SOLUTION: Train models with: python scripts/train_models.py")
                # Don't fail validation for missing models
        
        # Check multi-model config
        multi_model = model.get('multi_model', {})
        if multi_model.get('enabled', False):
            models = multi_model.get('models', [])
            if not models:
                self.errors.append("Multi-model enabled but no models configured")
                valid = False
            else:
                total_weight = 0
                for i, model_config in enumerate(models):
                    # Check required fields
                    if 'path' not in model_config:
                        self.errors.append(f"Model {i} missing path")
                        valid = False
                    elif not Path(model_config['path']).exists():
                        self.warnings.append(f"Model {i} file not found: {model_config['path']}")
                        print(f"💡 SOLUTION: Train models with: python scripts/train_models.py")
                        # Don't fail validation for missing models
                    
                    # Check weight
                    if 'weight' in model_config:
                        weight = model_config['weight']
                        if not isinstance(weight, (int, float)) or weight < 0:
                            self.errors.append(f"Model {i} weight should be non-negative number")
                            valid = False
                        else:
                            total_weight += weight
                
                # Check weight normalization
                if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
                    self.warnings.append(f"Model weights sum to {total_weight:.2f} (should be 1.0)")
        
        return valid
    
    def validate_risk_management_config(self) -> bool:
        """Validate risk management configuration section."""
        risk = self.config_data.get('risk_management', {})
        valid = True
        
        # Required fields
        required_fields = {
            'max_daily_loss_percent': (int, float),
            'max_drawdown_percent': (int, float),
            'max_consecutive_losses': int
        }
        
        for field, expected_type in required_fields.items():
            if field not in risk:
                self.errors.append(f"Risk management missing required field: {field}")
                valid = False
            elif not isinstance(risk[field], expected_type):
                self.errors.append(f"Risk_management.{field} should be {expected_type.__name__}, got {type(risk[field]).__name__}")
                valid = False
        
        # Validate specific values
        if 'max_daily_loss_percent' in risk:
            max_loss = risk['max_daily_loss_percent']
            if not isinstance(max_loss, (int, float)) or max_loss <= 0 or max_loss > 100:
                self.errors.append("Risk_management.max_daily_loss_percent should be 0-100")
                valid = False
        
        if 'max_drawdown_percent' in risk:
            max_dd = risk['max_drawdown_percent']
            if not isinstance(max_dd, (int, float)) or max_dd <= 0 or max_dd > 100:
                self.errors.append("Risk_management.max_drawdown_percent should be 0-100")
                valid = False
        
        if 'max_consecutive_losses' in risk:
            max_losses = risk['max_consecutive_losses']
            if not isinstance(max_losses, int) or max_losses < 1:
                self.errors.append("Risk_management.max_consecutive_losses should be positive integer")
                valid = False
        
        return valid
    
    def validate_signal_filters_config(self) -> bool:
        """Validate signal filters configuration."""
        signal_filters = self.config_data.get('signal_filters', {})
        valid = True
        
        if 'min_confidence' in signal_filters:
            min_conf = signal_filters['min_confidence']
            if not isinstance(min_conf, (int, float)) or min_conf < 0 or min_conf > 1:
                self.errors.append("Signal_filters.min_confidence should be 0-1")
                valid = False
        
        return valid
    
    def validate_timeframes(self) -> bool:
        """Validate timeframe strings."""
        valid = True
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '1d']
        
        # Check trading timeframes
        trading = self.config_data.get('trading', {})
        timeframes = trading.get('timeframes', [])
        
        for tf in timeframes:
            if tf not in valid_timeframes:
                self.errors.append(f"Invalid timeframe format: {tf} (valid: {valid_timeframes})")
                valid = False
        
        # Check model timeframes
        model = self.config_data.get('model', {})
        multi_model = model.get('multi_model', {})
        if multi_model.get('enabled', False):
            models = multi_model.get('models', [])
            for i, model_config in enumerate(models):
                tf = model_config.get('timeframe', '')
                if tf and tf not in valid_timeframes:
                    self.errors.append(f"Model {i} has invalid timeframe: {tf}")
                    valid = False
        
        return valid
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks."""
        print("🔍 Validating configuration file...")
        print("=" * 60)
        
        # Run all validations
        checks = [
            ("File Exists", self.validate_file_exists),
            ("YAML Syntax", self.validate_yaml_syntax),
            ("Required Sections", self.validate_required_sections),
            ("Trading Config", self.validate_trading_config),
            ("Model Config", self.validate_model_config),
            ("Risk Management", self.validate_risk_management_config),
            ("Signal Filters", self.validate_signal_filters_config),
            ("Timeframes", self.validate_timeframes),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.errors.append(f"Error in {check_name}: {e}")
        
        # Print results
        for error in self.errors:
            print(f"❌ {error}")
        
        for warning in self.warnings:
            print(f"⚠️  {warning}")
        
        if not self.errors:
            print("✅ Configuration validation passed!")
            if self.warnings:
                print(f"⚠️  {len(self.warnings)} warnings found (see above)")
            return True, self.errors, self.warnings
        else:
            print(f"❌ Configuration validation failed with {len(self.errors)} errors")
            return False, self.errors, self.warnings


def main():
    """Main entry point."""
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_all()
    
    print("=" * 60)
    
    if is_valid:
        print("✅ Configuration is valid!")
        print("\nYou can proceed with starting the services.")
        sys.exit(0)
    else:
        print("⚠️  Configuration has issues, but continuing...")
        print("\n🔧 SOLUTIONS:")
        print("1. Fix the errors listed above")
        print("2. Check the example config in config/env.example")
        print("3. Ensure all model files exist in the models/ directory")
        print("4. Verify all paths are correct and files exist")
        print("\n💡 Common fixes:")
        print("   - Check YAML indentation (use spaces, not tabs)")
        print("   - Ensure all required fields are present")
        print("   - Verify model file paths are correct")
        print("   - Check that numeric values are valid")
        print("\n⚠️  Continuing with startup - some features may not work")
        print("   Check service logs for specific errors")
        sys.exit(0)  # Don't fail - let services handle config issues


if __name__ == "__main__":
    main()

