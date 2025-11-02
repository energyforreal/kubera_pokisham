#!/usr/bin/env python3
"""
Synchronization Validator

Validates data format consistency, configuration synchronization,
and cross-component communication protocols.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import yaml
from sqlalchemy import text, inspect

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal
from src.core.logger import logger


class SynchronizationValidator:
    """Validates synchronization across all components."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def log_result(self, test_name: str, status: str, details: str = "", issues: List[str] = None):
        """Log validation result."""
        self.results[test_name] = {
            'status': status,
            'details': details,
            'issues': issues or [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if issues:
            for issue in issues:
                print(f"   Issue: {issue}")
    
    def validate_timestamp_formats(self) -> bool:
        """Validate timestamp format consistency across components."""
        issues = []
        
        try:
            # Test API response timestamp format
            response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                timestamp = health_data.get('timestamp')
                
                if timestamp:
                    # Check if it's a valid ISO format
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            issues.append("API timestamp missing timezone info")
                    except ValueError:
                        issues.append("API timestamp not in valid ISO format")
            
            # Test shared state timestamp format
            from src.shared_state import shared_state
            status = shared_state.get_status()
            heartbeat = status.get('last_heartbeat')
            
            if heartbeat:
                try:
                    dt = datetime.fromisoformat(heartbeat)
                    if dt.tzinfo is None:
                        issues.append("Shared state timestamp missing timezone info")
                except ValueError:
                    issues.append("Shared state timestamp not in valid ISO format")
            
            # Test database timestamp format
            db = SessionLocal()
            try:
                result = db.execute(text("SELECT datetime('now') as current_time")).fetchone()
                if result:
                    db_time = result[0]
                    # SQLite returns string, check if it's parseable
                    try:
                        datetime.fromisoformat(db_time)
                    except ValueError:
                        issues.append("Database timestamp format not ISO compatible")
            finally:
                db.close()
            
            if issues:
                self.log_result("timestamp_formats", "FAIL", f"Found {len(issues)} timestamp issues", issues)
                return False
            else:
                self.log_result("timestamp_formats", "PASS", "All timestamps in valid ISO format")
                return True
                
        except Exception as e:
            self.log_result("timestamp_formats", "ERROR", f"Exception: {e}")
            return False
    
    def validate_api_response_schemas(self) -> bool:
        """Validate API response schemas match frontend expectations."""
        issues = []
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                
                # Check required fields
                required_fields = ['status', 'timestamp', 'uptime_seconds', 'models_loaded']
                missing_fields = [f for f in required_fields if f not in health_data]
                if missing_fields:
                    issues.append(f"Health endpoint missing fields: {missing_fields}")
                
                # Check field types
                if 'timestamp' in health_data and not isinstance(health_data['timestamp'], str):
                    issues.append("Health timestamp should be string")
                if 'models_loaded' in health_data and not isinstance(health_data['models_loaded'], int):
                    issues.append("Health models_loaded should be integer")
            
            # Test prediction endpoint
            response = requests.get("http://localhost:8000/api/v1/predict?symbol=BTCUSD&timeframe=4h", timeout=30)
            if response.status_code == 200:
                pred_data = response.json()
                
                # Check required fields
                required_fields = ['symbol', 'prediction', 'confidence', 'is_actionable', 'timestamp']
                missing_fields = [f for f in required_fields if f not in pred_data]
                if missing_fields:
                    issues.append(f"Prediction endpoint missing fields: {missing_fields}")
                
                # Check field types
                if 'confidence' in pred_data and not isinstance(pred_data['confidence'], (int, float)):
                    issues.append("Prediction confidence should be numeric")
                if 'is_actionable' in pred_data and not isinstance(pred_data['is_actionable'], bool):
                    issues.append("Prediction is_actionable should be boolean")
            
            # Test portfolio endpoint
            response = requests.get("http://localhost:8000/api/v1/portfolio/status", timeout=10)
            if response.status_code == 200:
                portfolio_data = response.json()
                
                # Check required fields
                required_fields = ['balance', 'equity', 'num_positions', 'total_pnl', 'positions']
                missing_fields = [f for f in required_fields if f not in portfolio_data]
                if missing_fields:
                    issues.append(f"Portfolio endpoint missing fields: {missing_fields}")
                
                # Check field types
                if 'num_positions' in portfolio_data and not isinstance(portfolio_data['num_positions'], int):
                    issues.append("Portfolio num_positions should be integer")
                if 'positions' in portfolio_data and not isinstance(portfolio_data['positions'], list):
                    issues.append("Portfolio positions should be array")
            
            if issues:
                self.log_result("api_response_schemas", "FAIL", f"Found {len(issues)} schema issues", issues)
                return False
            else:
                self.log_result("api_response_schemas", "PASS", "All API responses match expected schemas")
                return True
                
        except Exception as e:
            self.log_result("api_response_schemas", "ERROR", f"Exception: {e}")
            return False
    
    def validate_database_model_alignment(self) -> bool:
        """Validate database models align with API responses."""
        issues = []
        
        try:
            db = SessionLocal()
            inspector = inspect(db.bind)
            
            # Check if required tables exist
            required_tables = ['trades', 'positions', 'ohlcv_data', 'performance_metrics']
            existing_tables = inspector.get_table_names()
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                issues.append(f"Missing database tables: {missing_tables}")
            
            # Check trade table structure
            if 'trades' in existing_tables:
                trade_columns = [col['name'] for col in inspector.get_columns('trades')]
                required_trade_columns = ['id', 'symbol', 'side', 'entry_price', 'size', 'timestamp']
                missing_columns = [c for c in required_trade_columns if c not in trade_columns]
                if missing_columns:
                    issues.append(f"Trade table missing columns: {missing_columns}")
            
            # Check position table structure
            if 'positions' in existing_tables:
                position_columns = [col['name'] for col in inspector.get_columns('positions')]
                required_position_columns = ['id', 'symbol', 'side', 'entry_price', 'size', 'timestamp']
                missing_columns = [c for c in required_position_columns if c not in position_columns]
                if missing_columns:
                    issues.append(f"Position table missing columns: {missing_columns}")
            
            db.close()
            
            if issues:
                self.log_result("database_model_alignment", "FAIL", f"Found {len(issues)} database issues", issues)
                return False
            else:
                self.log_result("database_model_alignment", "PASS", "Database models align with API expectations")
                return True
                
        except Exception as e:
            self.log_result("database_model_alignment", "ERROR", f"Exception: {e}")
            return False
    
    def validate_config_consistency(self) -> bool:
        """Validate configuration consistency across modules."""
        issues = []
        
        try:
            # Load config.yaml
            config_path = Path("config/config.yaml")
            if not config_path.exists():
                issues.append("config.yaml not found")
                self.log_result("config_consistency", "FAIL", "Config file missing", issues)
                return False
            
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Check trading config
            trading_config = config_data.get('trading', {})
            if not trading_config:
                issues.append("Missing trading configuration section")
            else:
                # Check required trading fields
                required_trading_fields = ['symbol', 'initial_balance', 'update_interval']
                missing_fields = [f for f in required_trading_fields if f not in trading_config]
                if missing_fields:
                    issues.append(f"Trading config missing fields: {missing_fields}")
                
                # Validate symbol format
                symbol = trading_config.get('symbol', '')
                if not symbol or not isinstance(symbol, str):
                    issues.append("Trading symbol should be non-empty string")
                
                # Validate balance
                balance = trading_config.get('initial_balance', 0)
                if not isinstance(balance, (int, float)) or balance <= 0:
                    issues.append("Initial balance should be positive number")
            
            # Check model config
            model_config = config_data.get('model', {})
            if not model_config:
                issues.append("Missing model configuration section")
            else:
                # Check multi-model config
                multi_model = model_config.get('multi_model', {})
                if multi_model.get('enabled', False):
                    models = multi_model.get('models', [])
                    if not models:
                        issues.append("Multi-model enabled but no models configured")
                    else:
                        # Validate model paths
                        for i, model in enumerate(models):
                            if 'path' not in model:
                                issues.append(f"Model {i} missing path")
                            elif not Path(model['path']).exists():
                                issues.append(f"Model {i} file not found: {model['path']}")
            
            # Check risk management config
            risk_config = config_data.get('risk_management', {})
            if not risk_config:
                issues.append("Missing risk management configuration section")
            else:
                # Check required risk fields
                required_risk_fields = ['max_daily_loss_percent', 'max_drawdown_percent', 'max_consecutive_losses']
                missing_fields = [f for f in required_risk_fields if f not in risk_config]
                if missing_fields:
                    issues.append(f"Risk config missing fields: {missing_fields}")
                
                # Validate risk values
                max_daily_loss = risk_config.get('max_daily_loss_percent', 0)
                if not isinstance(max_daily_loss, (int, float)) or max_daily_loss <= 0 or max_daily_loss > 100:
                    issues.append("Max daily loss should be positive number <= 100")
            
            if issues:
                self.log_result("config_consistency", "FAIL", f"Found {len(issues)} config issues", issues)
                return False
            else:
                self.log_result("config_consistency", "PASS", "Configuration is consistent and valid")
                return True
                
        except Exception as e:
            self.log_result("config_consistency", "ERROR", f"Exception: {e}")
            return False
    
    def validate_timeframe_strings(self) -> bool:
        """Validate timeframe string format consistency."""
        issues = []
        
        try:
            # Check config timeframes
            config_path = Path("config/config.yaml")
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            trading_config = config_data.get('trading', {})
            timeframes = trading_config.get('timeframes', [])
            
            # Validate timeframe format
            valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '1d']
            invalid_timeframes = [tf for tf in timeframes if tf not in valid_timeframes]
            if invalid_timeframes:
                issues.append(f"Invalid timeframe formats: {invalid_timeframes}")
            
            # Check model timeframes
            model_config = config_data.get('model', {})
            multi_model = model_config.get('multi_model', {})
            if multi_model.get('enabled', False):
                models = multi_model.get('models', [])
                for i, model in enumerate(models):
                    tf = model.get('timeframe', '')
                    if tf and tf not in valid_timeframes:
                        issues.append(f"Model {i} has invalid timeframe: {tf}")
            
            if issues:
                self.log_result("timeframe_strings", "FAIL", f"Found {len(issues)} timeframe issues", issues)
                return False
            else:
                self.log_result("timeframe_strings", "PASS", "All timeframes use valid format")
                return True
                
        except Exception as e:
            self.log_result("timeframe_strings", "ERROR", f"Exception: {e}")
            return False
    
    def validate_health_file_sync(self) -> bool:
        """Validate health file read/write synchronization."""
        issues = []
        
        try:
            health_file = Path("bot_health.json")
            if not health_file.exists():
                issues.append("Health file not found")
                self.log_result("health_file_sync", "FAIL", "Health file missing", issues)
                return False
            
            # Read health file
            with open(health_file, 'r') as f:
                health_data = json.load(f)
            
            # Check required fields
            required_fields = ['is_alive', 'last_heartbeat', 'models_loaded']
            missing_fields = [f for f in required_fields if f not in health_data]
            if missing_fields:
                issues.append(f"Health file missing fields: {missing_fields}")
            
            # Check heartbeat format
            heartbeat = health_data.get('last_heartbeat')
            if heartbeat:
                try:
                    dt = datetime.fromisoformat(heartbeat.replace('Z', '+00:00'))
                    # Check if heartbeat is recent (within last 5 minutes)
                    age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
                    if age_seconds > 300:  # 5 minutes
                        issues.append(f"Heartbeat is {age_seconds:.0f}s old (may indicate sync issues)")
                except ValueError:
                    issues.append("Heartbeat timestamp format invalid")
            
            # Check models loaded
            models_loaded = health_data.get('models_loaded', 0)
            if not isinstance(models_loaded, int) or models_loaded < 0:
                issues.append("Models loaded should be non-negative integer")
            
            if issues:
                self.log_result("health_file_sync", "FAIL", f"Found {len(issues)} health sync issues", issues)
                return False
            else:
                self.log_result("health_file_sync", "PASS", "Health file synchronization is working")
                return True
                
        except Exception as e:
            self.log_result("health_file_sync", "ERROR", f"Exception: {e}")
            return False
    
    def validate_websocket_message_formats(self) -> bool:
        """Validate WebSocket message format consistency."""
        issues = []
        
        try:
            # Test WebSocket connection and message format
            import websockets
            import asyncio
            
            async def test_websocket():
                uri = "ws://localhost:8000/ws"
                async with websockets.connect(uri, timeout=10) as websocket:
                    # Send ping
                    await websocket.send("ping")
                    
                    # Receive response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    
                    # Check response format
                    if response == "pong":
                        return True, "Ping/pong format correct"
                    else:
                        return False, f"Unexpected response format: {response}"
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success, message = loop.run_until_complete(test_websocket())
                if not success:
                    issues.append(message)
            finally:
                loop.close()
            
            if issues:
                self.log_result("websocket_message_formats", "FAIL", f"Found {len(issues)} WebSocket format issues", issues)
                return False
            else:
                self.log_result("websocket_message_formats", "PASS", "WebSocket message formats are consistent")
                return True
                
        except Exception as e:
            self.log_result("websocket_message_formats", "ERROR", f"Exception: {e}")
            return False
    
    def validate_signal_trade_data_structures(self) -> bool:
        """Validate signal and trade data structure consistency."""
        issues = []
        
        try:
            # Test signal generation
            response = requests.get("http://localhost:8000/api/v1/predict?symbol=BTCUSD&timeframe=4h", timeout=30)
            if response.status_code == 200:
                signal_data = response.json()
                
                # Check signal structure
                required_signal_fields = ['symbol', 'prediction', 'confidence', 'timestamp']
                missing_fields = [f for f in required_signal_fields if f not in signal_data]
                if missing_fields:
                    issues.append(f"Signal missing fields: {missing_fields}")
                
                # Validate prediction values
                prediction = signal_data.get('prediction', '')
                valid_predictions = ['BUY', 'SELL', 'HOLD']
                if prediction not in valid_predictions:
                    issues.append(f"Invalid prediction value: {prediction}")
                
                # Validate confidence range
                confidence = signal_data.get('confidence', 0)
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    issues.append(f"Confidence should be 0-1, got: {confidence}")
            
            # Test trade execution (if possible)
            # Note: This might fail if no positions exist, which is OK
            response = requests.get("http://localhost:8000/api/v1/positions", timeout=10)
            if response.status_code == 200:
                positions_data = response.json()
                
                # Check positions structure
                if 'positions' in positions_data:
                    positions = positions_data['positions']
                    if isinstance(positions, list):
                        for i, position in enumerate(positions):
                            if not isinstance(position, dict):
                                issues.append(f"Position {i} should be dictionary")
                                continue
                            
                            # Check position fields
                            required_position_fields = ['symbol', 'side', 'entry_price', 'size']
                            missing_fields = [f for f in required_position_fields if f not in position]
                            if missing_fields:
                                issues.append(f"Position {i} missing fields: {missing_fields}")
            
            if issues:
                self.log_result("signal_trade_data_structures", "FAIL", f"Found {len(issues)} data structure issues", issues)
                return False
            else:
                self.log_result("signal_trade_data_structures", "PASS", "Signal and trade data structures are consistent")
                return True
                
        except Exception as e:
            self.log_result("signal_trade_data_structures", "ERROR", f"Exception: {e}")
            return False
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all synchronization validations."""
        print("🔍 Starting Synchronization Validation...")
        print("=" * 60)
        
        validations = [
            ("Timestamp Formats", self.validate_timestamp_formats),
            ("API Response Schemas", self.validate_api_response_schemas),
            ("Database Model Alignment", self.validate_database_model_alignment),
            ("Config Consistency", self.validate_config_consistency),
            ("Timeframe Strings", self.validate_timeframe_strings),
            ("Health File Sync", self.validate_health_file_sync),
            ("WebSocket Message Formats", self.validate_websocket_message_formats),
            ("Signal/Trade Data Structures", self.validate_signal_trade_data_structures),
        ]
        
        # Run all validations
        for name, validation_func in validations:
            try:
                validation_func()
            except Exception as e:
                self.log_result(name.lower().replace(" ", "_"), "ERROR", f"Exception: {e}")
        
        # Summary
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        
        print("\n" + "=" * 60)
        print(f"📊 SYNCHRONIZATION VALIDATION SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print("=" * 60)
        
        return {
            'summary': {
                'total_validations': len(self.results),
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'total_time_seconds': total_time
            },
            'results': self.results
        }


def main():
    """Main entry point."""
    validator = SynchronizationValidator()
    results = validator.run_all_validations()
    
    # Save results to file
    results_file = Path("sync_validation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Exit with error code if any failures
    if results['summary']['failed'] > 0 or results['summary']['errors'] > 0:
        print("\n❌ Some synchronizations failed - check results above")
        sys.exit(1)
    else:
        print("\n✅ All synchronizations valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
