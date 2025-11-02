#!/usr/bin/env python3
"""
Integration Test Script for Trading Agent
Tests all critical integration points between frontend, backend API, ML models, and trading bot.
"""

import asyncio
import json
import time
import requests
import websocket
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.config import trading_config
from src.core.logger import logger

class IntegrationTester:
    """Comprehensive integration tester for Trading Agent system."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.ws_url = api_url.replace("http", "ws")
        self.results = {
            "start_time": datetime.now(timezone.utc),
            "tests": {},
            "issues": [],
            "recommendations": []
        }
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log_test(self, test_name: str, success: bool, details: str = "", issue: str = ""):
        """Log test result."""
        self.results["tests"][test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if issue:
            self.results["issues"].append({
                "test": test_name,
                "issue": issue,
                "severity": "high" if not success else "medium"
            })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if issue:
            print(f"   Issue: {issue}")
    
    def test_api_connectivity(self) -> bool:
        """Test basic API connectivity."""
        try:
            response = self.session.get(f"{self.api_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Connectivity", True, f"API responding: {data.get('name', 'Unknown')}")
                return True
            else:
                self.log_test("API Connectivity", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Connectivity", False, f"Connection failed: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        try:
            response = self.session.get(f"{self.api_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                models_loaded = data.get("models_loaded", 0)
                
                if status == "healthy" and models_loaded > 0:
                    self.log_test("Health Endpoint", True, f"Status: {status}, Models: {models_loaded}")
                    return True
                else:
                    self.log_test("Health Endpoint", False, f"Status: {status}, Models: {models_loaded}")
                    return False
            else:
                self.log_test("Health Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_prediction_endpoint(self) -> bool:
        """Test prediction endpoint with different timeframes."""
        timeframes = ["15m", "1h", "4h", "multi"]
        success_count = 0
        
        for tf in timeframes:
            try:
                response = self.session.get(f"{self.api_url}/api/v1/predict?symbol=BTCUSD&timeframe={tf}")
                if response.status_code == 200:
                    data = response.json()
                    prediction = data.get("prediction", "UNKNOWN")
                    confidence = data.get("confidence", 0)
                    
                    if prediction in ["BUY", "SELL", "HOLD"] and 0 <= confidence <= 1:
                        self.log_test(f"Prediction Endpoint ({tf})", True, f"{prediction} @ {confidence:.2%}")
                        success_count += 1
                    else:
                        self.log_test(f"Prediction Endpoint ({tf})", False, f"Invalid response: {prediction}, {confidence}")
                else:
                    self.log_test(f"Prediction Endpoint ({tf})", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Prediction Endpoint ({tf})", False, f"Error: {str(e)}")
        
        return success_count == len(timeframes)
    
    def test_portfolio_endpoint(self) -> bool:
        """Test portfolio status endpoint."""
        try:
            response = self.session.get(f"{self.api_url}/api/v1/portfolio/status")
            if response.status_code == 200:
                data = response.json()
                balance = data.get("balance", 0)
                equity = data.get("equity", 0)
                
                if isinstance(balance, (int, float)) and isinstance(equity, (int, float)):
                    self.log_test("Portfolio Endpoint", True, f"Balance: ${balance}, Equity: ${equity}")
                    return True
                else:
                    self.log_test("Portfolio Endpoint", False, f"Invalid data types: {type(balance)}, {type(equity)}")
                    return False
            else:
                self.log_test("Portfolio Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Portfolio Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_positions_endpoint(self) -> bool:
        """Test positions endpoint."""
        try:
            response = self.session.get(f"{self.api_url}/api/v1/positions")
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                positions = data.get("positions", [])
                
                if isinstance(count, int) and isinstance(positions, list):
                    self.log_test("Positions Endpoint", True, f"Count: {count}")
                    return True
                else:
                    self.log_test("Positions Endpoint", False, f"Invalid data types")
                    return False
            else:
                self.log_test("Positions Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Positions Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_analytics_endpoint(self) -> bool:
        """Test analytics endpoint."""
        try:
            response = self.session.get(f"{self.api_url}/api/v1/analytics/daily")
            if response.status_code == 200:
                data = response.json()
                risk_metrics = data.get("risk_metrics", {})
                
                if isinstance(risk_metrics, dict):
                    self.log_test("Analytics Endpoint", True, f"Risk metrics available: {list(risk_metrics.keys())}")
                    return True
                else:
                    self.log_test("Analytics Endpoint", False, f"Invalid risk_metrics type: {type(risk_metrics)}")
                    return False
            else:
                self.log_test("Analytics Endpoint", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_market_data_endpoints(self) -> bool:
        """Test market data endpoints."""
        endpoints = [
            ("/api/v1/market/ticker/BTCUSD", "Ticker"),
            ("/api/v1/market/ohlc/BTCUSD?resolution=15m&limit=10", "OHLC")
        ]
        
        success_count = 0
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.api_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Market Data ({name})", True, f"Data received")
                    success_count += 1
                else:
                    self.log_test(f"Market Data ({name})", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Market Data ({name})", False, f"Error: {str(e)}")
        
        return success_count == len(endpoints)
    
    def test_websocket_connection(self) -> bool:
        """Test WebSocket connection."""
        try:
            ws_url = f"{self.ws_url}/ws"
            ws = websocket.WebSocket()
            ws.connect(ws_url, timeout=10)
            
            # Send ping
            ws.send("ping")
            
            # Wait for pong
            response = ws.recv()
            ws.close()
            
            if response == "pong" or '"type":"pong"' in response:
                self.log_test("WebSocket Connection", True, "Ping-pong successful")
                return True
            else:
                self.log_test("WebSocket Connection", False, f"Unexpected response: {response}")
                return False
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Error: {str(e)}")
            return False
    
    def test_model_files(self) -> bool:
        """Test that all configured model files exist."""
        try:
            multi_config = trading_config.model.get('multi_model', {})
            model_configs = multi_config.get('models', [])
            
            missing_files = []
            for config in model_configs:
                model_path = Path(config['path'])
                if not model_path.exists():
                    missing_files.append(str(model_path))
            
            if not missing_files:
                self.log_test("Model Files", True, f"All {len(model_configs)} model files exist")
                return True
            else:
                self.log_test("Model Files", False, f"Missing files: {missing_files}")
                return False
        except Exception as e:
            self.log_test("Model Files", False, f"Error checking models: {str(e)}")
            return False
    
    def test_configuration_consistency(self) -> bool:
        """Test configuration consistency."""
        issues = []
        
        try:
            # Check model configuration
            multi_config = trading_config.model.get('multi_model', {})
            if not multi_config.get('enabled', False):
                issues.append("Multi-model not enabled")
            
            # Check model weights sum to 1.0
            models = multi_config.get('models', [])
            total_weight = sum(model.get('weight', 0) for model in models)
            if abs(total_weight - 1.0) > 0.01:
                issues.append(f"Model weights sum to {total_weight:.3f}, should be 1.0")
            
            # Check timeframes
            timeframes = set(model.get('timeframe', '') for model in models)
            expected_timeframes = {'15m', '1h', '4h'}
            if timeframes != expected_timeframes:
                issues.append(f"Timeframes {timeframes} != expected {expected_timeframes}")
            
            if not issues:
                self.log_test("Configuration Consistency", True, f"All {len(models)} models configured correctly")
                return True
            else:
                self.log_test("Configuration Consistency", False, f"Issues: {'; '.join(issues)}")
                return False
        except Exception as e:
            self.log_test("Configuration Consistency", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests."""
        error_tests = [
            ("/api/v1/predict?symbol=INVALID", "Invalid symbol"),
            ("/api/v1/market/ticker/INVALID", "Invalid ticker"),
            ("/api/v1/positions/INVALID/close", "Invalid position close")
        ]
        
        success_count = 0
        for endpoint, description in error_tests:
            try:
                response = self.session.get(f"{self.api_url}{endpoint}")
                # Should return 404 or 400, not 500
                if response.status_code in [400, 404]:
                    self.log_test(f"Error Handling ({description})", True, f"Proper error code: {response.status_code}")
                    success_count += 1
                else:
                    self.log_test(f"Error Handling ({description})", False, f"Unexpected code: {response.status_code}")
            except Exception as e:
                self.log_test(f"Error Handling ({description})", False, f"Exception: {str(e)}")
        
        return success_count == len(error_tests)
    
    def generate_recommendations(self):
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check for common issues
        failed_tests = [name for name, result in self.results["tests"].items() if not result["success"]]
        
        if "API Connectivity" in failed_tests:
            recommendations.append("Ensure backend API is running on port 8000")
        
        if "Health Endpoint" in failed_tests:
            recommendations.append("Check trading bot is running and models are loaded")
        
        if "Model Files" in failed_tests:
            recommendations.append("Train models or check model file paths in config.yaml")
        
        if "WebSocket Connection" in failed_tests:
            recommendations.append("Check WebSocket server configuration and firewall settings")
        
        if "Configuration Consistency" in failed_tests:
            recommendations.append("Review model configuration in config.yaml")
        
        # Add general recommendations
        recommendations.extend([
            "Set up proper CORS origins for production deployment",
            "Add integration tests to CI/CD pipeline",
            "Implement health check monitoring",
            "Add API rate limiting",
            "Set up proper logging and monitoring"
        ])
        
        self.results["recommendations"] = recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("🚀 Starting Trading Agent Integration Tests")
        print("=" * 60)
        
        # Core connectivity tests
        self.test_api_connectivity()
        self.test_health_endpoint()
        
        # API endpoint tests
        self.test_prediction_endpoint()
        self.test_portfolio_endpoint()
        self.test_positions_endpoint()
        self.test_analytics_endpoint()
        self.test_market_data_endpoints()
        
        # Real-time communication tests
        self.test_websocket_connection()
        
        # Configuration tests
        self.test_model_files()
        self.test_configuration_consistency()
        
        # Error handling tests
        self.test_error_handling()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Calculate summary
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for result in self.results["tests"].values() if result["success"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "end_time": datetime.now(timezone.utc)
        }
        
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        if self.results["issues"]:
            print(f"⚠️  Issues Found: {len(self.results['issues'])}")
            for issue in self.results["issues"]:
                print(f"   - {issue['test']}: {issue['issue']}")
        
        if self.results["recommendations"]:
            print(f"💡 Recommendations: {len(self.results['recommendations'])}")
            for rec in self.results["recommendations"]:
                print(f"   - {rec}")
        
        return self.results

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading Agent Integration Tests")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", help="Output results to JSON file")
    
    args = parser.parse_args()
    
    tester = IntegrationTester(args.api_url)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Results saved to {args.output}")
    
    # Exit with error code if tests failed
    if results["summary"]["failed_tests"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
