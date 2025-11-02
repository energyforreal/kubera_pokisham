#!/usr/bin/env python3
"""
Data Consistency Checker

Validates data consistency between database records and API responses,
prediction results across predictor types, and portfolio metrics calculations.
"""

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
import pandas as pd
from sqlalchemy import text, func
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal, Trade, Position, OHLCVData, PerformanceMetrics
from src.core.logger import logger


class DataConsistencyChecker:
    """Checks data consistency across all components."""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def log_result(self, test_name: str, status: str, details: str = "", issues: List[str] = None, metrics: Dict = None):
        """Log test result."""
        self.results[test_name] = {
            'status': status,
            'details': details,
            'issues': issues or [],
            'metrics': metrics or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if issues:
            for issue in issues:
                print(f"   Issue: {issue}")
        if metrics:
            for key, value in metrics.items():
                print(f"   {key}: {value}")
    
    def check_database_vs_api_data(self) -> bool:
        """Check database records vs API-returned data."""
        issues = []
        metrics = {}
        
        try:
            db = SessionLocal()
            
            # Get portfolio data from API
            response = requests.get("http://localhost:8000/api/v1/portfolio/status", timeout=10)
            if response.status_code != 200:
                self.log_result("database_vs_api_data", "FAIL", f"API request failed: {response.status_code}")
                return False
            
            api_portfolio = response.json()
            
            # Get positions from API
            response = requests.get("http://localhost:8000/api/v1/positions", timeout=10)
            if response.status_code != 200:
                self.log_result("database_vs_api_data", "FAIL", f"Positions API request failed: {response.status_code}")
                return False
            
            api_positions = response.json()
            
            # Check database positions
            db_positions = db.query(Position).all()
            api_position_count = len(api_positions.get('positions', []))
            db_position_count = len(db_positions)
            
            if api_position_count != db_position_count:
                issues.append(f"Position count mismatch: API={api_position_count}, DB={db_position_count}")
            
            # Check individual position data consistency
            for i, db_pos in enumerate(db_positions):
                api_pos = None
                for api_pos_data in api_positions.get('positions', []):
                    if api_pos_data.get('symbol') == db_pos.symbol:
                        api_pos = api_pos_data
                        break
                
                if api_pos:
                    # Check key fields
                    if abs(float(api_pos.get('entry_price', 0)) - float(db_pos.entry_price)) > 0.01:
                        issues.append(f"Position {db_pos.symbol} entry price mismatch")
                    
                    if abs(float(api_pos.get('size', 0)) - float(db_pos.size)) > 0.01:
                        issues.append(f"Position {db_pos.symbol} size mismatch")
                    
                    if api_pos.get('side') != db_pos.side:
                        issues.append(f"Position {db_pos.symbol} side mismatch")
                else:
                    issues.append(f"Position {db_pos.symbol} not found in API response")
            
            # Check trade history consistency
            response = requests.get("http://localhost:8000/api/v1/trades/history?limit=10", timeout=10)
            if response.status_code == 200:
                api_trades = response.json()
                
                # Get recent trades from database
                recent_trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(10).all()
                
                api_trade_count = len(api_trades.get('trades', []))
                db_trade_count = len(recent_trades)
                
                if api_trade_count != db_trade_count:
                    issues.append(f"Trade count mismatch: API={api_trade_count}, DB={db_trade_count}")
                
                # Check trade data consistency
                for i, db_trade in enumerate(recent_trades):
                    if i < len(api_trades.get('trades', [])):
                        api_trade = api_trades['trades'][i]
                        
                        # Check key fields
                        if abs(float(api_trade.get('entry_price', 0)) - float(db_trade.entry_price)) > 0.01:
                            issues.append(f"Trade {db_trade.id} entry price mismatch")
                        
                        if api_trade.get('side') != db_trade.side:
                            issues.append(f"Trade {db_trade.id} side mismatch")
            
            metrics = {
                'api_positions': api_position_count,
                'db_positions': db_position_count,
                'api_trades': api_trade_count if 'api_trade_count' in locals() else 0,
                'db_trades': db_trade_count if 'db_trade_count' in locals() else 0
            }
            
            db.close()
            
            if issues:
                self.log_result("database_vs_api_data", "FAIL", f"Found {len(issues)} data inconsistencies", issues, metrics)
                return False
            else:
                self.log_result("database_vs_api_data", "PASS", "Database and API data are consistent", "", metrics)
                return True
                
        except Exception as e:
            self.log_result("database_vs_api_data", "ERROR", f"Exception: {e}")
            return False
    
    def check_prediction_results_consistency(self) -> bool:
        """Check prediction results across predictor types."""
        issues = []
        metrics = {}
        
        try:
            # Test different timeframes
            timeframes = ['15m', '1h', '4h']
            predictions = {}
            
            for timeframe in timeframes:
                try:
                    response = requests.get(f"http://localhost:8000/api/v1/predict?symbol=BTCUSD&timeframe={timeframe}", timeout=30)
                    if response.status_code == 200:
                        pred_data = response.json()
                        predictions[timeframe] = pred_data
                    else:
                        issues.append(f"Failed to get prediction for {timeframe}: HTTP {response.status_code}")
                except Exception as e:
                    issues.append(f"Exception getting prediction for {timeframe}: {e}")
            
            # Check prediction format consistency
            for timeframe, pred_data in predictions.items():
                required_fields = ['symbol', 'prediction', 'confidence', 'timestamp']
                missing_fields = [f for f in required_fields if f not in pred_data]
                if missing_fields:
                    issues.append(f"Prediction {timeframe} missing fields: {missing_fields}")
                
                # Check prediction values
                prediction = pred_data.get('prediction', '')
                if prediction not in ['BUY', 'SELL', 'HOLD']:
                    issues.append(f"Prediction {timeframe} has invalid value: {prediction}")
                
                # Check confidence range
                confidence = pred_data.get('confidence', 0)
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    issues.append(f"Prediction {timeframe} confidence out of range: {confidence}")
            
            # Check for reasonable consistency across timeframes
            if len(predictions) >= 2:
                predictions_list = list(predictions.values())
                predictions_values = [p.get('prediction', '') for p in predictions_list]
                confidences = [p.get('confidence', 0) for p in predictions_list]
                
                # Check if predictions are reasonable (not all different)
                unique_predictions = set(predictions_values)
                if len(unique_predictions) == len(predictions_values):
                    issues.append("All timeframes have different predictions (may indicate inconsistency)")
                
                # Check confidence variance
                if len(confidences) > 1:
                    confidence_variance = max(confidences) - min(confidences)
                    if confidence_variance > 0.8:  # 80% variance
                        issues.append(f"High confidence variance across timeframes: {confidence_variance:.2f}")
            
            metrics = {
                'timeframes_tested': len(predictions),
                'avg_confidence': sum(p.get('confidence', 0) for p in predictions.values()) / len(predictions) if predictions else 0,
                'prediction_variety': len(set(p.get('prediction', '') for p in predictions.values()))
            }
            
            if issues:
                self.log_result("prediction_results_consistency", "FAIL", f"Found {len(issues)} prediction issues", issues, metrics)
                return False
            else:
                self.log_result("prediction_results_consistency", "PASS", "Prediction results are consistent", "", metrics)
                return True
                
        except Exception as e:
            self.log_result("prediction_results_consistency", "ERROR", f"Exception: {e}")
            return False
    
    def check_position_data_consistency(self) -> bool:
        """Check position data in trading engine vs database."""
        issues = []
        metrics = {}
        
        try:
            # Get positions from API (which uses trading engine)
            response = requests.get("http://localhost:8000/api/v1/positions", timeout=10)
            if response.status_code != 200:
                self.log_result("position_data_consistency", "FAIL", f"API request failed: {response.status_code}")
                return False
            
            api_positions = response.json()
            
            # Get positions from database
            db = SessionLocal()
            db_positions = db.query(Position).all()
            
            # Check position count
            api_count = len(api_positions.get('positions', []))
            db_count = len(db_positions)
            
            if api_count != db_count:
                issues.append(f"Position count mismatch: API={api_count}, DB={db_count}")
            
            # Check individual position consistency
            for db_pos in db_positions:
                api_pos = None
                for api_pos_data in api_positions.get('positions', []):
                    if api_pos_data.get('symbol') == db_pos.symbol:
                        api_pos = api_pos_data
                        break
                
                if api_pos:
                    # Check critical fields
                    field_checks = [
                        ('symbol', db_pos.symbol, api_pos.get('symbol')),
                        ('side', db_pos.side, api_pos.get('side')),
                        ('entry_price', float(db_pos.entry_price), float(api_pos.get('entry_price', 0))),
                        ('size', float(db_pos.size), float(api_pos.get('size', 0)))
                    ]
                    
                    for field_name, db_value, api_value in field_checks:
                        if field_name in ['entry_price', 'size']:
                            if abs(db_value - api_value) > 0.01:  # Allow small floating point differences
                                issues.append(f"Position {db_pos.symbol} {field_name} mismatch: DB={db_value}, API={api_value}")
                        else:
                            if db_value != api_value:
                                issues.append(f"Position {db_pos.symbol} {field_name} mismatch: DB={db_value}, API={api_value}")
                else:
                    issues.append(f"Position {db_pos.symbol} not found in API response")
            
            metrics = {
                'api_positions': api_count,
                'db_positions': db_count,
                'matched_positions': sum(1 for db_pos in db_positions if any(api_pos.get('symbol') == db_pos.symbol for api_pos in api_positions.get('positions', [])))
            }
            
            db.close()
            
            if issues:
                self.log_result("position_data_consistency", "FAIL", f"Found {len(issues)} position inconsistencies", issues, metrics)
                return False
            else:
                self.log_result("position_data_consistency", "PASS", "Position data is consistent", "", metrics)
                return True
                
        except Exception as e:
            self.log_result("position_data_consistency", "ERROR", f"Exception: {e}")
            return False
    
    def check_portfolio_metrics_calculation(self) -> bool:
        """Check portfolio metrics calculation consistency."""
        issues = []
        metrics = {}
        
        try:
            # Get portfolio status from API
            response = requests.get("http://localhost:8000/api/v1/portfolio/status", timeout=10)
            if response.status_code != 200:
                self.log_result("portfolio_metrics_calculation", "FAIL", f"API request failed: {response.status_code}")
                return False
            
            api_portfolio = response.json()
            
            # Get positions from database to calculate metrics manually
            db = SessionLocal()
            positions = db.query(Position).all()
            trades = db.query(Trade).filter(Trade.is_closed == True).all()
            
            # Calculate metrics manually
            total_pnl = sum(float(trade.pnl or 0) for trade in trades)
            total_pnl_percent = (total_pnl / float(api_portfolio.get('balance', 1))) * 100 if api_portfolio.get('balance', 0) > 0 else 0
            
            # Check balance consistency
            api_balance = api_portfolio.get('balance', 0)
            api_equity = api_portfolio.get('equity', 0)
            api_total_pnl = api_portfolio.get('total_pnl', 0)
            api_total_pnl_percent = api_portfolio.get('total_pnl_percent', 0)
            
            # Check if equity makes sense (should be balance + unrealized PnL)
            if api_balance != 0:
                equity_ratio = api_equity / api_balance
                if equity_ratio < 0.5 or equity_ratio > 2.0:  # Allow some variance
                    issues.append(f"Equity ratio seems unreasonable: {equity_ratio:.2f}")
            
            # Check PnL consistency
            if abs(api_total_pnl - total_pnl) > 0.01:
                issues.append(f"Total PnL mismatch: API={api_total_pnl}, Calculated={total_pnl}")
            
            # Check position count
            api_positions = api_portfolio.get('num_positions', 0)
            db_positions = len(positions)
            if api_positions != db_positions:
                issues.append(f"Position count mismatch: API={api_positions}, DB={db_positions}")
            
            metrics = {
                'api_balance': api_balance,
                'api_equity': api_equity,
                'api_total_pnl': api_total_pnl,
                'api_positions': api_positions,
                'db_positions': db_positions,
                'calculated_pnl': total_pnl,
                'equity_ratio': equity_ratio if 'equity_ratio' in locals() else 0
            }
            
            db.close()
            
            if issues:
                self.log_result("portfolio_metrics_calculation", "FAIL", f"Found {len(issues)} portfolio calculation issues", issues, metrics)
                return False
            else:
                self.log_result("portfolio_metrics_calculation", "PASS", "Portfolio metrics are consistent", "", metrics)
                return True
                
        except Exception as e:
            self.log_result("portfolio_metrics_calculation", "ERROR", f"Exception: {e}")
            return False
    
    def check_trade_history_completeness(self) -> bool:
        """Check trade history completeness and data integrity."""
        issues = []
        metrics = {}
        
        try:
            db = SessionLocal()
            
            # Get all trades
            all_trades = db.query(Trade).all()
            closed_trades = db.query(Trade).filter(Trade.is_closed == True).all()
            open_trades = db.query(Trade).filter(Trade.is_closed == False).all()
            
            # Check for data integrity issues
            integrity_issues = 0
            
            for trade in all_trades:
                # Check required fields
                if not trade.symbol or trade.symbol == "":
                    issues.append(f"Trade {trade.id} missing symbol")
                    integrity_issues += 1
                
                if not trade.side or trade.side not in ['buy', 'sell']:
                    issues.append(f"Trade {trade.id} invalid side: {trade.side}")
                    integrity_issues += 1
                
                if trade.entry_price is None or trade.entry_price <= 0:
                    issues.append(f"Trade {trade.id} invalid entry price: {trade.entry_price}")
                    integrity_issues += 1
                
                if trade.size is None or trade.size <= 0:
                    issues.append(f"Trade {trade.id} invalid size: {trade.size}")
                    integrity_issues += 1
                
                # Check closed trades
                if trade.is_closed:
                    if trade.exit_price is None or trade.exit_price <= 0:
                        issues.append(f"Closed trade {trade.id} missing exit price")
                        integrity_issues += 1
                    
                    if trade.closed_at is None:
                        issues.append(f"Closed trade {trade.id} missing closed_at timestamp")
                        integrity_issues += 1
                    
                    # Check PnL calculation
                    if trade.pnl is not None:
                        expected_pnl = (float(trade.exit_price) - float(trade.entry_price)) * float(trade.size)
                        if trade.side == 'sell':
                            expected_pnl = -expected_pnl
                        
                        if abs(float(trade.pnl) - expected_pnl) > 0.01:
                            issues.append(f"Trade {trade.id} PnL calculation error: stored={trade.pnl}, expected={expected_pnl}")
                            integrity_issues += 1
            
            # Check for orphaned positions
            positions = db.query(Position).all()
            for position in positions:
                # Check if position has corresponding trade
                corresponding_trade = db.query(Trade).filter(
                    Trade.symbol == position.symbol,
                    Trade.side == position.side,
                    Trade.entry_price == position.entry_price
                ).first()
                
                if not corresponding_trade:
                    issues.append(f"Position {position.symbol} has no corresponding trade")
                    integrity_issues += 1
            
            # Check timestamp consistency
            for trade in all_trades:
                if trade.timestamp:
                    # Check if timestamp is reasonable (not in future, not too old)
                    now = datetime.now(timezone.utc)
                    trade_time = trade.timestamp
                    if trade_time.tzinfo is None:
                        trade_time = trade_time.replace(tzinfo=timezone.utc)
                    
                    age_days = (now - trade_time).days
                    if age_days > 365:  # Older than 1 year
                        issues.append(f"Trade {trade.id} is very old: {age_days} days")
                    elif trade_time > now:
                        issues.append(f"Trade {trade.id} has future timestamp")
            
            metrics = {
                'total_trades': len(all_trades),
                'closed_trades': len(closed_trades),
                'open_trades': len(open_trades),
                'positions': len(positions),
                'integrity_issues': integrity_issues
            }
            
            db.close()
            
            if issues:
                self.log_result("trade_history_completeness", "FAIL", f"Found {len(issues)} trade history issues", issues, metrics)
                return False
            else:
                self.log_result("trade_history_completeness", "PASS", "Trade history is complete and consistent", "", metrics)
                return True
                
        except Exception as e:
            self.log_result("trade_history_completeness", "ERROR", f"Exception: {e}")
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all data consistency checks."""
        print("🔍 Starting Data Consistency Checks...")
        print("=" * 60)
        
        checks = [
            ("Database vs API Data", self.check_database_vs_api_data),
            ("Prediction Results Consistency", self.check_prediction_results_consistency),
            ("Position Data Consistency", self.check_position_data_consistency),
            ("Portfolio Metrics Calculation", self.check_portfolio_metrics_calculation),
            ("Trade History Completeness", self.check_trade_history_completeness),
        ]
        
        # Run all checks
        for name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.log_result(name.lower().replace(" ", "_"), "ERROR", f"Exception: {e}")
        
        # Summary
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results.values() if r['status'] == 'ERROR')
        
        print("\n" + "=" * 60)
        print(f"📊 DATA CONSISTENCY CHECK SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"⏱️  Total Time: {total_time:.2f}s")
        print("=" * 60)
        
        return {
            'summary': {
                'total_checks': len(self.results),
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'total_time_seconds': total_time
            },
            'results': self.results
        }


def main():
    """Main entry point."""
    checker = DataConsistencyChecker()
    results = checker.run_all_checks()
    
    # Save results to file
    results_file = Path("data_consistency_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Exit with error code if any failures
    if results['summary']['failed'] > 0 or results['summary']['errors'] > 0:
        print("\n❌ Some data consistency checks failed - check results above")
        sys.exit(1)
    else:
        print("\n✅ All data consistency checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
