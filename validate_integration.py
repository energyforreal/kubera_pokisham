#!/usr/bin/env python3
"""
Simple Integration Validation Script
Validates configuration and model files without requiring running services.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_model_files() -> Dict[str, Any]:
    """Validate that all configured model files exist."""
    try:
        from src.core.config import trading_config
        
        multi_config = trading_config.model.get('multi_model', {})
        model_configs = multi_config.get('models', [])
        
        results = {
            "total_models": len(model_configs),
            "missing_files": [],
            "existing_files": [],
            "total_weight": 0.0
        }
        
        for config in model_configs:
            model_path = Path(config['path'])
            weight = config.get('weight', 0)
            timeframe = config.get('timeframe', 'unknown')
            
            results["total_weight"] += weight
            
            if model_path.exists():
                results["existing_files"].append({
                    "path": str(model_path),
                    "timeframe": timeframe,
                    "weight": weight,
                    "size_mb": model_path.stat().st_size / (1024 * 1024)
                })
            else:
                results["missing_files"].append(str(model_path))
        
        results["weight_valid"] = abs(results["total_weight"] - 1.0) < 0.01
        results["all_files_exist"] = len(results["missing_files"]) == 0
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

def validate_configuration() -> Dict[str, Any]:
    """Validate configuration consistency."""
    try:
        from src.core.config import trading_config
        
        results = {
            "multi_model_enabled": False,
            "strategy": None,
            "timeframes": set(),
            "risk_config": {},
            "issues": []
        }
        
        # Check multi-model configuration
        multi_config = trading_config.model.get('multi_model', {})
        results["multi_model_enabled"] = multi_config.get('enabled', False)
        results["strategy"] = multi_config.get('strategy', 'unknown')
        
        # Check timeframes
        models = multi_config.get('models', [])
        timeframes = set()
        for model in models:
            timeframe = model.get('timeframe', '')
            if timeframe:
                timeframes.add(timeframe)
        results["timeframes"] = list(timeframes)
        
        # Check risk configuration
        results["risk_config"] = {
            "max_daily_loss_percent": trading_config.risk_management.get('max_daily_loss_percent'),
            "max_drawdown_percent": trading_config.risk_management.get('max_drawdown_percent'),
            "max_consecutive_losses": trading_config.risk_management.get('max_consecutive_losses'),
            "stop_loss_atr_multiplier": trading_config.risk_management.get('stop_loss_atr_multiplier'),
            "take_profit_risk_reward": trading_config.risk_management.get('take_profit_risk_reward')
        }
        
        # Validate configuration
        if not results["multi_model_enabled"]:
            results["issues"].append("Multi-model system not enabled")
        
        if results["strategy"] != "cross_timeframe_weighted":
            results["issues"].append(f"Unexpected strategy: {results['strategy']}")
        
        expected_timeframes = {'15m', '1h', '4h'}
        if set(results["timeframes"]) != expected_timeframes:
            results["issues"].append(f"Timeframes {results['timeframes']} != expected {list(expected_timeframes)}")
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

def validate_file_structure() -> Dict[str, Any]:
    """Validate critical file structure."""
    critical_files = [
        "backend/api/main.py",
        "frontend_web/src/services/api.ts",
        "frontend_web/src/app/page.tsx",
        "src/main.py",
        "src/ml/model_coordinator.py",
        "src/shared_state.py",
        "config/config.yaml",
        "requirements.txt",
        "frontend_web/package.json"
    ]
    
    results = {
        "missing_files": [],
        "existing_files": [],
        "total_files": len(critical_files)
    }
    
    for file_path in critical_files:
        path = Path(file_path)
        if path.exists():
            results["existing_files"].append(str(path))
        else:
            results["missing_files"].append(str(path))
    
    results["all_files_exist"] = len(results["missing_files"]) == 0
    
    return results

def validate_api_endpoints() -> Dict[str, Any]:
    """Validate API endpoint definitions."""
    try:
        # Read the main.py file and extract endpoint definitions
        main_py_path = Path("backend/api/main.py")
        if not main_py_path.exists():
            return {"error": "backend/api/main.py not found"}
        
        content = main_py_path.read_text()
        
        # Extract endpoint patterns
        import re
        endpoint_patterns = re.findall(r'@app\.(get|post|put|delete|websocket)\("([^"]+)"', content)
        
        results = {
            "endpoints": [],
            "total_endpoints": len(endpoint_patterns),
            "websocket_endpoints": 0,
            "rest_endpoints": 0
        }
        
        for method, path in endpoint_patterns:
            endpoint_info = {
                "method": method.upper(),
                "path": path,
                "type": "websocket" if method == "websocket" else "rest"
            }
            results["endpoints"].append(endpoint_info)
            
            if method == "websocket":
                results["websocket_endpoints"] += 1
            else:
                results["rest_endpoints"] += 1
        
        return results
        
    except Exception as e:
        return {"error": str(e)}

def main():
    """Run all validation checks."""
    # Use plain text for Windows console compatibility
    print("Trading Agent Integration Validation")
    print("=" * 50)
    
    all_results = {
        "timestamp": "2025-01-19T00:00:00Z",
        "validations": {}
    }
    
    # Run validations
    print("Validating file structure...")
    all_results["validations"]["file_structure"] = validate_file_structure()
    
    print("Validating model files...")
    all_results["validations"]["model_files"] = validate_model_files()
    
    print("Validating configuration...")
    all_results["validations"]["configuration"] = validate_configuration()
    
    print("Validating API endpoints...")
    all_results["validations"]["api_endpoints"] = validate_api_endpoints()
    
    # Print results
    print("\n" + "=" * 50)
    print("Validation Results:")
    
    for validation_name, results in all_results["validations"].items():
        print(f"\n{validation_name.upper()}:")
        
        if "error" in results:
            print(f"  [ERROR] Error: {results['error']}")
            continue
        
        if validation_name == "file_structure":
            print(f"  Files: {len(results['existing_files'])}/{results['total_files']} exist")
            if results["missing_files"]:
                print(f"  [WARNING] Missing: {', '.join(results['missing_files'])}")
            else:
                print("  [OK] All critical files present")
        
        elif validation_name == "model_files":
            print(f"  Models: {len(results['existing_files'])}/{results['total_models']} exist")
            print(f"  Total weight: {results['total_weight']:.3f}")
            if results["missing_files"]:
                print(f"  [WARNING] Missing: {', '.join(results['missing_files'])}")
            else:
                print("  [OK] All model files present")
            
            if not results["weight_valid"]:
                print(f"  [WARNING] Weight sum invalid: {results['total_weight']:.3f} (should be 1.0)")
            else:
                print("  [OK] Model weights valid")
        
        elif validation_name == "configuration":
            print(f"  Multi-model: {'Enabled' if results['multi_model_enabled'] else 'Disabled'}")
            print(f"  Strategy: {results['strategy']}")
            print(f"  Timeframes: {sorted(results['timeframes'])}")
            
            if results["issues"]:
                print(f"  [WARNING] Issues: {', '.join(results['issues'])}")
            else:
                print("  [OK] Configuration valid")
        
        elif validation_name == "api_endpoints":
            print(f"  Total endpoints: {results['total_endpoints']}")
            print(f"  REST endpoints: {results['rest_endpoints']}")
            print(f"  WebSocket endpoints: {results['websocket_endpoints']}")
            
            # List critical endpoints
            critical_endpoints = [
                "/api/v1/health",
                "/api/v1/predict", 
                "/api/v1/portfolio/status",
                "/api/v1/trade",
                "/ws"
            ]
            
            found_critical = []
            for endpoint in results["endpoints"]:
                if endpoint["path"] in critical_endpoints:
                    found_critical.append(f"{endpoint['method']} {endpoint['path']}")
            
            print(f"  [OK] Critical endpoints: {len(found_critical)}/{len(critical_endpoints)}")
            for ep in found_critical:
                print(f"    - {ep}")
    
    # Overall assessment
    print("\n" + "=" * 50)
    print("Overall Assessment:")
    
    issues_found = 0
    for validation_name, results in all_results["validations"].items():
        if "error" in results:
            issues_found += 1
        elif validation_name == "file_structure" and results.get("missing_files"):
            issues_found += 1
        elif validation_name == "model_files" and results.get("missing_files"):
            issues_found += 1
        elif validation_name == "configuration" and results.get("issues"):
            issues_found += 1
    
    if issues_found == 0:
        print("[OK] All validations passed - system ready for integration testing")
        print("[INFO] Next step: Start the services and run full integration tests")
    else:
        print(f"[WARNING] {issues_found} validation issues found - review before deployment")
        print("[INFO] Fix the issues above before running integration tests")
    
    # Save results
    with open("validation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n[INFO] Detailed results saved to validation_results.json")
    
    return issues_found == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
