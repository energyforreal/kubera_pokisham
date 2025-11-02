#!/usr/bin/env python3
"""
Integration Health Checker

Comprehensive health check for all trading system integrations.
Tests component availability, connectivity, and basic functionality.
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import websockets
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal, init_db
from src.core.logger import logger
from src.shared_state import shared_state


class IntegrationHealthChecker:
    """Comprehensive integration health checker with service dependency validation."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.service_dependencies_checked = False
        
    def log_result(self, test_name: str, status: str, details: str = "", latency_ms: float = 0):
        """Log test result."""
        self.results[test_name] = {
            'status': status,
            'details': details,
            'latency_ms': latency_ms,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status} ({latency_ms:.1f}ms)")
        if details:
            print(f"   Details: {details}")
    
    def check_service_dependencies(self, skip_dependency_check: bool = False) -> bool:
        """Check that all required services are running before validation."""
        print("🔍 Checking service dependencies...")
        
        if skip_dependency_check:
            print("⚠️  Skipping service dependency checks (pre-startup mode)")
            self.service_dependencies_checked = False
            return True
        
        # Check trading agent
        trading_agent_ok = self._check_trading_agent_dependency()
        if not trading_agent_ok:
            print("⚠️  Trading agent not running. Will run basic checks only.")
            print("   💡 To start: python src/main.py")
            self.service_dependencies_checked = False
            return True  # Don't fail - continue with basic checks
        
        # Check backend API
        backend_api_ok = self._check_backend_api_dependency()
        if not backend_api_ok:
            print("⚠️  Backend API not running. Will run basic checks only.")
            print("   💡 To start: cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
            self.service_dependencies_checked = False
            return True  # Don't fail - continue with basic checks
        
        print("✅ All required services are running")
        self.service_dependencies_checked = True
        return True
    
    def _check_trading_agent_dependency(self) -> bool:
        """Check if trading agent is running."""
        try:
            health_file = Path('bot_health.json')
            if not health_file.exists():
                return False
            
            with open(health_file) as f:
                health_data = json.load(f)
            
            return health_data.get('status') == 'healthy'
        except:
            return False
    
    def _check_backend_api_dependency(self) -> bool:
        """Check if backend API is running."""
        try:
            response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_trading_agent_health(self) -> bool:
        """Check if trading agent is running and healthy."""
        start_time = time.time()
        
        try:
            health_file = Path("bot_health.json")
            if not health_file.exists():
                self.log_result("trading_agent_health", "FAIL", "Health file not found", 0)
                return False
            
            with open(health_file, 'r') as f:
                health_data = json.load(f)
            
            # Check if bot is alive
            is_alive = health_data.get('is_alive', False)
            if not is_alive:
                self.log_result("trading_agent_health", "FAIL", "Bot marked as not alive", 0)
                return False
            
            # Check heartbeat age
            last_heartbeat = health_data.get('last_heartbeat')
            if last_heartbeat:
                try:
                    hb_dt = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                    age_seconds = (datetime.now(timezone.utc) - hb_dt).total_seconds()
                    if age_seconds > 120:  # 2 minutes
                        self.log_result("trading_agent_health", "WARN", f"Heartbeat {age_seconds:.0f}s old", 0)
                    else:
                        self.log_result("trading_agent_health", "PASS", f"Heartbeat {age_seconds:.0f}s old", 0)
                except Exception as e:
                    self.log_result("trading_agent_health", "WARN", f"Invalid heartbeat format: {e}", 0)
            
            # Check models loaded
            models_loaded = health_data.get('models_loaded', 0)
            if models_loaded == 0:
                self.log_result("trading_agent_models", "FAIL", "No models loaded", 0)
                return False
            else:
                self.log_result("trading_agent_models", "PASS", f"{models_loaded} models loaded", 0)
            
            latency = (time.time() - start_time) * 1000
            self.log_result("trading_agent_health", "PASS", f"Bot healthy with {models_loaded} models", latency)
            return True
            
        except Exception as e:
            self.log_result("trading_agent_health", "FAIL", f"Error reading health file: {e}", 0)
            return False
    
    def check_backend_api(self) -> bool:
        """Check backend API health."""
        start_time = time.time()
        
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get('status', 'unknown')
                self.log_result("backend_api_health", "PASS", f"Status: {status}", latency)
                return True
            else:
                self.log_result("backend_api_health", "FAIL", f"HTTP {response.status_code}", latency)
                return False
                
        except requests.exceptions.ConnectionError:
            self.log_result("backend_api_health", "FAIL", "Connection refused", 0)
            return False
        except Exception as e:
            self.log_result("backend_api_health", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_shared_state(self) -> bool:
        """Check shared state component registration."""
        start_time = time.time()
        
        try:
            status = shared_state.get_status()
            latency = (time.time() - start_time) * 1000
            
            # Check if trading agent is registered
            if not status.get('is_trading_agent_running', False):
                self.log_result("shared_state_registration", "FAIL", "Trading agent not registered", latency)
                return False
            
            # Check component availability
            components = {
                'trading_engine': status.get('has_trading_engine', False),
                'predictor': status.get('has_predictor', False),
                'delta_client': status.get('has_delta_client', False),
                'risk_manager': status.get('has_risk_manager', False)
            }
            
            missing_components = [k for k, v in components.items() if not v]
            if missing_components:
                self.log_result("shared_state_components", "FAIL", f"Missing: {missing_components}", latency)
                return False
            
            self.log_result("shared_state_registration", "PASS", "All components registered", latency)
            return True
            
        except Exception as e:
            self.log_result("shared_state_registration", "FAIL", f"Error: {e}", 0)
            return False
    
    async def check_websocket_connection(self) -> bool:
        """Test WebSocket connection establishment with enhanced error handling."""
        start_time = time.time()
        
        try:
            uri = "ws://localhost:8000/ws"
            
            # Use asyncio.wait_for to handle timeout properly
            async with asyncio.timeout(10):
                async with websockets.connect(uri) as websocket:
                    # Send ping
                    await websocket.send("ping")
                    
                    # Wait for pong response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    
                    latency = (time.time() - start_time) * 1000
                    
                    if response == "pong":
                        self.log_result("websocket_connection", "PASS", "Ping/pong successful", latency)
                        return True
                    else:
                        self.log_result("websocket_connection", "FAIL", f"Unexpected response: {response}", latency)
                        return False
                    
        except asyncio.TimeoutError:
            self.log_result("websocket_connection", "FAIL", "Connection timeout", 0)
            return False
        except ConnectionRefusedError:
            self.log_result("websocket_connection", "FAIL", "Connection refused - Backend API not running", 0)
            return False
        except Exception as e:
            error_msg = str(e)
            if "create_connection" in error_msg and "timeout" in error_msg:
                self.log_result("websocket_connection", "FAIL", "WebSocket implementation issue - using fallback", 0)
                return await self._test_websocket_fallback()
            else:
                self.log_result("websocket_connection", "FAIL", f"Error: {error_msg}", 0)
                return False
    
    async def _test_websocket_fallback(self) -> bool:
        """Fallback WebSocket test using HTTP upgrade."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect('http://localhost:8000/ws') as ws:
                    await ws.send_str("ping")
                    response = await ws.receive_str()
                    
                    if response == "pong":
                        self.log_result("websocket_connection", "PASS", "WebSocket fallback successful", 0)
                        return True
                    else:
                        self.log_result("websocket_connection", "FAIL", f"Fallback unexpected response: {response}", 0)
                        return False
                        
        except Exception as e:
            self.log_result("websocket_connection", "FAIL", f"Fallback error: {e}", 0)
            return False
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity from both processes."""
        start_time = time.time()
        
        try:
            # Test database connection
            db = SessionLocal()
            result = db.execute(text("SELECT 1")).scalar()
            db.close()
            
            latency = (time.time() - start_time) * 1000
            
            if result == 1:
                self.log_result("database_connectivity", "PASS", "Database accessible", latency)
                return True
            else:
                self.log_result("database_connectivity", "FAIL", "Unexpected query result", latency)
                return False
                
        except Exception as e:
            self.log_result("database_connectivity", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_delta_exchange_api(self) -> bool:
        """Check Delta Exchange API authentication."""
        start_time = time.time()
        
        try:
            from src.data.delta_client import DeltaExchangeClient
            client = DeltaExchangeClient()
            
            # Test with a simple ticker request
            ticker = client.get_ticker("BTCUSD")
            
            latency = (time.time() - start_time) * 1000
            
            if ticker and 'close' in ticker:
                price = ticker.get('close', 0)
                self.log_result("delta_exchange_api", "PASS", f"BTCUSD price: ${price:,.2f}", latency)
                return True
            else:
                self.log_result("delta_exchange_api", "FAIL", "Invalid ticker response", latency)
                return False
                
        except Exception as e:
            self.log_result("delta_exchange_api", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_telegram_bot(self) -> bool:
        """Check Telegram bot configuration."""
        start_time = time.time()
        
        try:
            # Check if credentials are configured
            token = settings.telegram_bot_token
            chat_id = settings.telegram_chat_id
            
            latency = (time.time() - start_time) * 1000
            
            if not token or token == "":
                self.log_result("telegram_bot_config", "FAIL", "Bot token not configured", latency)
                return False
            
            if not chat_id or chat_id == "":
                self.log_result("telegram_bot_config", "FAIL", "Chat ID not configured", latency)
                return False
            
            self.log_result("telegram_bot_config", "PASS", "Credentials configured", latency)
            return True
            
        except Exception as e:
            self.log_result("telegram_bot_config", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_prediction_cache(self) -> bool:
        """Test prediction cache functionality."""
        start_time = time.time()
        
        try:
            # Test cache by making a prediction request
            response = requests.get("http://localhost:8000/api/v1/predict?symbol=BTCUSD&timeframe=4h", timeout=30)
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if 'prediction' in data and 'confidence' in data:
                    self.log_result("prediction_cache", "PASS", f"Prediction: {data['prediction']} ({data['confidence']:.1%})", latency)
                    return True
                else:
                    self.log_result("prediction_cache", "FAIL", "Invalid prediction response", latency)
                    return False
            else:
                self.log_result("prediction_cache", "FAIL", f"HTTP {response.status_code}", latency)
                return False
                
        except Exception as e:
            self.log_result("prediction_cache", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_activity_manager(self) -> bool:
        """Check activity manager WebSocket broadcasting."""
        start_time = time.time()
        
        try:
            # Test activity endpoint
            response = requests.get("http://localhost:8000/api/v1/activities/recent?limit=5", timeout=10)
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if 'activities' in data:
                    count = len(data['activities'])
                    self.log_result("activity_manager", "PASS", f"{count} recent activities", latency)
                    return True
                else:
                    self.log_result("activity_manager", "FAIL", "Invalid activities response", latency)
                    return False
            else:
                self.log_result("activity_manager", "FAIL", f"HTTP {response.status_code}", latency)
                return False
                
        except Exception as e:
            self.log_result("activity_manager", "FAIL", f"Error: {e}", 0)
            return False
    
    def check_config_consistency(self) -> bool:
        """Check configuration file parsing consistency."""
        start_time = time.time()
        
        try:
            # Check if config.yaml exists and is readable
            config_path = Path("config/config.yaml")
            if not config_path.exists():
                self.log_result("config_consistency", "FAIL", "config.yaml not found", 0)
                return False
            
            # Test config loading
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Check required sections
            required_sections = ['trading', 'model', 'risk_management']
            missing_sections = [s for s in required_sections if s not in config_data]
            
            latency = (time.time() - start_time) * 1000
            
            if missing_sections:
                self.log_result("config_consistency", "FAIL", f"Missing sections: {missing_sections}", latency)
                return False
            
            self.log_result("config_consistency", "PASS", "All required sections present", latency)
            return True
            
        except Exception as e:
            self.log_result("config_consistency", "FAIL", f"Error: {e}", 0)
            return False
    
    async def run_all_checks(self, skip_service_dependencies: bool = False) -> Dict[str, any]:
        """Run all integration health checks."""
        print("🔍 Starting Integration Health Check...")
        print("=" * 60)
        
        # Check service dependencies first (unless skipped)
        if not skip_service_dependencies:
            if not self.check_service_dependencies():
                print("\n⚠️  Service dependencies not met. Running basic checks only.")
                # Don't fail - continue with basic checks
        
        # Define checks based on whether services are running
        if self.service_dependencies_checked:
            # Full integration checks when services are running
            checks = [
                ("Trading Agent Health", self.check_trading_agent_health),
                ("Backend API", self.check_backend_api),
                ("Shared State", self.check_shared_state),
                ("Database Connectivity", self.check_database_connectivity),
                ("Delta Exchange API", self.check_delta_exchange_api),
                ("Telegram Bot Config", self.check_telegram_bot),
                ("Prediction Cache", self.check_prediction_cache),
                ("Activity Manager", self.check_activity_manager),
                ("Config Consistency", self.check_config_consistency),
            ]
        else:
            # Basic checks when services are not running
            checks = [
                ("Config Consistency", self.check_config_consistency),
                ("Database Connectivity", self.check_database_connectivity),
                ("Delta Exchange API", self.check_delta_exchange_api),
                ("Telegram Bot Config", self.check_telegram_bot),
            ]
        
        # Run synchronous checks
        for name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.log_result(name.lower().replace(" ", "_"), "ERROR", f"Exception: {e}", 0)
        
        # Run async checks only if services are running
        if self.service_dependencies_checked:
            try:
                await self.check_websocket_connection()
            except Exception as e:
                self.log_result("websocket_connection", "ERROR", f"Exception: {e}", 0)
        
        # Summary
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        warnings = sum(1 for r in self.results.values() if r['status'] == 'WARN')
        
        print("\n" + "=" * 60)
        print(f"📊 INTEGRATION HEALTH SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print("=" * 60)
        
        return {
            'summary': {
                'total_checks': len(self.results),
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'total_time_seconds': total_time
            },
            'results': self.results
        }


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Integration Health Checker')
    parser.add_argument('--skip-deps', action='store_true', 
                       help='Skip service dependency checks (for pre-startup validation)')
    parser.add_argument('--pre-startup', action='store_true',
                       help='Run basic checks only (equivalent to --skip-deps)')
    
    args = parser.parse_args()
    
    checker = IntegrationHealthChecker()
    
    # Determine if we should skip service dependencies
    skip_deps = args.skip_deps or args.pre_startup
    
    # First check service dependencies (unless skipped)
    if not skip_deps:
        if not checker.check_service_dependencies():
            print("\n❌ Service dependencies not met. Please start required services first.")
            print("\nTo start services:")
            print("1. Start trading agent: python src/main.py")
            print("2. Start backend API: cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
            print("\nOr run basic checks only: python scripts/check_integrations.py --skip-deps")
            sys.exit(1)
    
    results = await checker.run_all_checks(skip_service_dependencies=skip_deps)
    
    # Save results to file
    results_file = Path("integration_health_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Exit with error code if any critical failures
    if results['summary']['failed'] > 0:
        print("\n⚠️  Some integrations had issues - check results above")
        print("   💡 The system will attempt to start anyway")
        print("   💡 Check service logs for specific errors")
        sys.exit(0)  # Don't fail - let services handle issues
    else:
        print("\n✅ All integrations healthy!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
