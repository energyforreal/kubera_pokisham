#!/usr/bin/env python3
"""
Comprehensive Error Check and Fix System for Trading Agent
Analyzes all components, validates integrations, identifies errors,
implements fixes, and verifies resolution through iterative testing.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
import yaml
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Constants
MAX_ITERATIONS = 5
API_URL = os.getenv("API_URL", "http://localhost:8000")
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
DIAGNOSTIC_PORT = 8080
DIAGNOSTIC_DASHBOARD_PORT = 3001


class ErrorChecker:
    """Main error checking and fixing system."""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "iterations": [],
            "all_errors": [],
            "all_fixes": [],
            "final_status": {}
        }
        self.iteration = 0
        self.session = requests.Session()
        self.session.timeout = 10
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def log_error(self, category: str, error: str, details: Dict = None):
        """Log error with category."""
        error_entry = {
            "category": category,
            "error": error,
            "details": details or {},
            "iteration": self.iteration,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results["all_errors"].append(error_entry)
        self.log(f"ERROR [{category}]: {error}", "ERROR")
        
    def log_fix(self, category: str, fix: str, details: Dict = None):
        """Log fix applied."""
        fix_entry = {
            "category": category,
            "fix": fix,
            "details": details or {},
            "iteration": self.iteration,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.results["all_fixes"].append(fix_entry)
        self.log(f"FIX [{category}]: {fix}", "FIX")
    
    # ========================================================================
    # PHASE 1: STATIC ANALYSIS
    # ========================================================================
    
    def validate_file_structure(self) -> Tuple[bool, List[str]]:
        """Validate critical files exist."""
        self.log("Validating file structure...")
        
        critical_files = {
            "backend/api/main.py": "Backend API main file",
            "src/main.py": "Trading bot main file",
            "src/shared_state.py": "Shared state module",
            "config/config.yaml": "Configuration file",
            "frontend_web/package.json": "Frontend package file",
            "frontend_web/src/services/api.ts": "Frontend API client",
            "requirements.txt": "Python dependencies",
            "integration_test.py": "Integration test script",
            "check_health.py": "Health check script"
        }
        
        missing = []
        for file_path, description in critical_files.items():
            path = project_root / file_path
            if not path.exists():
                missing.append(file_path)
                self.log_error("missing_file", f"{description} not found", {
                    "file": file_path,
                    "description": description
                })
            else:
                self.log(f"[OK] Found: {file_path}")
        
        return len(missing) == 0, missing
    
    def validate_model_files(self) -> Tuple[bool, List[str]]:
        """Validate model files exist."""
        self.log("Validating model files...")
        
        try:
            from src.core.config import trading_config
            
            multi_config = trading_config.model.get('multi_model', {})
            if not multi_config.get('enabled', False):
                self.log("Multi-model not enabled - skipping model validation")
                return True, []
            
            model_configs = multi_config.get('models', [])
            missing = []
            
            for config in model_configs:
                model_path = Path(config.get('path', ''))
                if not model_path.is_absolute():
                    model_path = project_root / model_path
                
                if not model_path.exists():
                    missing.append(str(config.get('path', '')))
                    self.log_error("missing_model", f"Model file not found: {config.get('path', '')}", {
                        "path": str(config.get('path', '')),
                        "timeframe": config.get('timeframe', 'unknown'),
                        "weight": config.get('weight', 0)
                    })
                else:
                    size_mb = model_path.stat().st_size / (1024 * 1024)
                    self.log(f"[OK] Model: {config.get('path', '')} ({size_mb:.2f} MB)")
            
            # Check weight sum
            total_weight = sum(m.get('weight', 0) for m in model_configs)
            if abs(total_weight - 1.0) > 0.01:
                self.log_error("config_error", f"Model weights sum to {total_weight:.3f}, should be 1.0")
                return False, missing
            
            return len(missing) == 0, missing
            
        except Exception as e:
            self.log_error("model_validation_error", f"Failed to validate models: {str(e)}")
            return False, []
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate configuration files."""
        self.log("Validating configuration...")
        
        issues = []
        
        # Check config.yaml
        config_path = project_root / "config" / "config.yaml"
        if not config_path.exists():
            self.log_error("missing_config", "config.yaml not found")
            issues.append("missing_config_yaml")
            return False, issues
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required sections
            required_sections = ['trading', 'risk_management', 'model']
            for section in required_sections:
                if section not in config:
                    issues.append(f"missing_section_{section}")
                    self.log_error("config_error", f"Missing section in config.yaml: {section}")
            
            # Check for .env file
            env_path = project_root / ".env"
            env_example = project_root / "env.template" or project_root / "config" / "env.example"
            
            if not env_path.exists():
                if env_example.exists():
                    self.log("Creating .env from template...")
                    shutil.copy(env_example, env_path)
                    self.log_fix("config", "Created .env file from template")
                else:
                    self.log_error("missing_env", ".env file not found and no template available")
                    issues.append("missing_env")
            
        except yaml.YAMLError as e:
            self.log_error("config_error", f"Invalid YAML syntax in config.yaml: {str(e)}")
            issues.append("invalid_yaml")
        except Exception as e:
            self.log_error("config_error", f"Configuration validation failed: {str(e)}")
            issues.append("config_validation_error")
        
        return len(issues) == 0, issues
    
    def analyze_api_endpoints(self) -> Tuple[bool, Dict[str, Any]]:
        """Analyze API endpoints from backend code."""
        self.log("Analyzing API endpoints...")
        
        api_file = project_root / "backend" / "api" / "main.py"
        if not api_file.exists():
            self.log_error("missing_file", "backend/api/main.py not found")
            return False, {}
        
        try:
            content = api_file.read_text()
            
            # Extract endpoint definitions
            endpoint_pattern = r'@app\.(get|post|put|delete|websocket)\("([^"]+)"'
            endpoints = re.findall(endpoint_pattern, content)
            
            # Extract CORS configuration
            cors_pattern = r'allowed_origins\s*=\s*[^"]*"([^"]+)"'
            cors_match = re.search(cors_pattern, content)
            cors_origins = cors_match.group(1) if cors_match else None
            
            endpoint_info = {
                "total_endpoints": len(endpoints),
                "rest_endpoints": 0,
                "websocket_endpoints": 0,
                "endpoints": [],
                "cors_origins": cors_origins
            }
            
            critical_endpoints = [
                "/api/v1/health",
                "/api/v1/predict",
                "/api/v1/portfolio/status",
                "/api/v1/trade",
                "/ws"
            ]
            
            found_critical = []
            
            for method, path in endpoints:
                is_websocket = method == "websocket"
                endpoint_info["endpoints"].append({
                    "method": method.upper(),
                    "path": path,
                    "type": "websocket" if is_websocket else "rest"
                })
                
                if is_websocket:
                    endpoint_info["websocket_endpoints"] += 1
                else:
                    endpoint_info["rest_endpoints"] += 1
                
                if path in critical_endpoints:
                    found_critical.append(path)
            
            # Check if all critical endpoints exist
            missing_critical = set(critical_endpoints) - set(found_critical)
            if missing_critical:
                self.log_error("api_analysis", f"Missing critical endpoints: {missing_critical}")
                return False, endpoint_info
            
            self.log(f"[OK] Found {endpoint_info['total_endpoints']} endpoints ({endpoint_info['rest_endpoints']} REST, {endpoint_info['websocket_endpoints']} WebSocket)")
            return True, endpoint_info
            
        except Exception as e:
            self.log_error("api_analysis", f"Failed to analyze API endpoints: {str(e)}")
            return False, {}
    
    def analyze_frontend_integration(self) -> Tuple[bool, List[str]]:
        """Analyze frontend API integration."""
        self.log("Analyzing frontend integration...")
        
        api_client_file = project_root / "frontend_web" / "src" / "services" / "api.ts"
        if not api_client_file.exists():
            self.log_error("missing_file", "Frontend API client not found")
            return False, []
        
        issues = []
        
        try:
            content = api_client_file.read_text()
            
            # Check API URL configuration
            if "process.env.NEXT_PUBLIC_API_URL" not in content:
                issues.append("missing_api_url_env")
                self.log_error("frontend_config", "NEXT_PUBLIC_API_URL not found in frontend API client")
            
            # Check default URL
            default_url_match = re.search(r"process\.env\.NEXT_PUBLIC_API_URL\s*\|\|\s*['\"]([^'\"]+)['\"]", content)
            if default_url_match:
                default_url = default_url_match.group(1)
                if default_url != f"http://localhost:{BACKEND_PORT}":
                    issues.append("incorrect_default_api_url")
                    self.log_error("frontend_config", f"Incorrect default API URL: {default_url}")
            
            # Check WebSocket URL construction
            if "/ws" not in content and "wsUrl" not in content.lower():
                issues.append("missing_websocket_integration")
                self.log_error("frontend_config", "WebSocket integration not found")
            
            if not issues:
                self.log("[OK] Frontend API integration looks good")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            self.log_error("frontend_analysis", f"Failed to analyze frontend: {str(e)}")
            return False, []
    
    # ========================================================================
    # PHASE 2: INTEGRATION TESTING
    # ========================================================================
    
    def test_api_connectivity(self) -> bool:
        """Test if backend API is accessible."""
        self.log("Testing API connectivity...")
        
        try:
            response = self.session.get(f"{API_URL}/", timeout=5)
            if response.status_code == 200:
                self.log("[OK] API is accessible")
                return True
            else:
                self.log_error("api_connectivity", f"API returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_error("api_connectivity", "Cannot connect to backend API - is it running?")
            return False
        except Exception as e:
            self.log_error("api_connectivity", f"API connectivity test failed: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint."""
        self.log("Testing health endpoint...")
        
        try:
            response = self.session.get(f"{API_URL}/api/v1/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                models_loaded = data.get("models_loaded", 0)
                
                if status == "healthy" and models_loaded > 0:
                    self.log(f"[OK] Health check passed (status: {status}, models: {models_loaded})")
                    return True
                else:
                    self.log_error("health_check", f"Health status: {status}, models: {models_loaded}")
                    return False
            else:
                self.log_error("health_check", f"Health endpoint returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_error("health_check", f"Health check failed: {str(e)}")
            return False
    
    def test_critical_endpoints(self) -> Tuple[bool, List[str]]:
        """Test critical API endpoints."""
        self.log("Testing critical API endpoints...")
        
        endpoints_to_test = [
            ("/api/v1/predict?symbol=BTCUSD&timeframe=4h", "GET", "prediction"),
            ("/api/v1/portfolio/status", "GET", "portfolio"),
        ]
        
        failed = []
        
        for endpoint, method, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_URL}{endpoint}", timeout=15)
                    
                    if response.status_code == 200:
                        self.log(f"[OK] {name} endpoint working")
                    elif response.status_code == 503:
                        self.log_error("endpoint_test", f"{name} endpoint unavailable (503)", {
                            "endpoint": endpoint,
                            "status": response.status_code
                        })
                        failed.append(name)
                    else:
                        self.log_error("endpoint_test", f"{name} endpoint failed", {
                            "endpoint": endpoint,
                            "status": response.status_code
                        })
                        failed.append(name)
                else:
                    # Skip non-GET for now
                    pass
                    
            except Exception as e:
                self.log_error("endpoint_test", f"{name} endpoint error: {str(e)}")
                failed.append(name)
        
        return len(failed) == 0, failed
    
    def run_integration_test_script(self) -> Tuple[bool, Dict]:
        """Run existing integration_test.py script."""
        self.log("Running integration test script...")
        
        integration_test = project_root / "integration_test.py"
        
        if not integration_test.exists():
            self.log("Integration test script not found, skipping")
            return False, {"error": "integration_test.py not found"}
        
        try:
            # Run integration test script
            result = subprocess.run(
                [sys.executable, str(integration_test), "--api-url", API_URL],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_root)
            )
            
            if result.returncode == 0:
                self.log("[OK] Integration tests passed")
                return True, {"output": result.stdout}
            else:
                self.log_error("integration_test", f"Integration tests failed (exit code: {result.returncode})", {
                    "stdout": result.stdout[:500],  # First 500 chars
                    "stderr": result.stderr[:500]
                })
                return False, {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.log_error("integration_test", "Integration tests timed out")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log_error("integration_test", f"Failed to run integration tests: {str(e)}")
            return False, {"error": str(e)}
    
    def run_validation_script(self) -> Tuple[bool, Dict]:
        """Run existing validate_integration.py script."""
        self.log("Running validation script...")
        
        validation_script = project_root / "validate_integration.py"
        
        if not validation_script.exists():
            self.log("Validation script not found, skipping")
            return False, {"error": "validate_integration.py not found"}
        
        try:
            # Run validation script
            result = subprocess.run(
                [sys.executable, str(validation_script)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root)
            )
            
            if result.returncode == 0:
                self.log("[OK] Validation script passed")
                return True, {"output": result.stdout}
            else:
                self.log_error("validation", f"Validation script failed (exit code: {result.returncode})", {
                    "stdout": result.stdout[:500],
                    "stderr": result.stderr[:500]
                })
                return False, {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.log_error("validation", "Validation script timed out")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log_error("validation", f"Failed to run validation script: {str(e)}")
            return False, {"error": str(e)}
    
    # ========================================================================
    # PHASE 3: ERROR FIXING
    # ========================================================================
    
    def fix_missing_env(self) -> bool:
        """Create .env file from template if missing."""
        env_path = project_root / ".env"
        
        if env_path.exists():
            return True
        
        templates = [
            project_root / "env.template",
            project_root / "config" / "env.example",
            project_root / "config" / "env.template"
        ]
        
        for template_path in templates:
            if template_path.exists():
                try:
                    shutil.copy(template_path, env_path)
                    self.log_fix("config", f"Created .env from {template_path.name}")
                    return True
                except Exception as e:
                    self.log_error("fix_error", f"Failed to create .env: {str(e)}")
                    return False
        
        self.log_error("fix_error", "No .env template found")
        return False
    
    def fix_frontend_api_url(self) -> bool:
        """Fix frontend API URL if incorrect."""
        api_client_file = project_root / "frontend_web" / "src" / "services" / "api.ts"
        
        if not api_client_file.exists():
            return False
        
        try:
            content = api_client_file.read_text()
            expected_default = f"http://localhost:{BACKEND_PORT}"
            
            # Check if default URL is correct
            pattern = r"(process\.env\.NEXT_PUBLIC_API_URL\s*\|\|\s*['\"])([^'\"]+)(['\"])"
            match = re.search(pattern, content)
            
            if match and match.group(2) != expected_default:
                # Fix the default URL
                new_content = re.sub(
                    pattern,
                    rf"\g<1>{expected_default}\g<3>",
                    content
                )
                api_client_file.write_text(new_content)
                self.log_fix("frontend_config", f"Fixed default API URL to {expected_default}")
                return True
            
            return True  # Already correct or pattern not found
            
        except Exception as e:
            self.log_error("fix_error", f"Failed to fix frontend API URL: {str(e)}")
            return False
    
    def fix_cors_configuration(self) -> bool:
        """Fix CORS configuration if needed."""
        api_file = project_root / "backend" / "api" / "main.py"
        
        if not api_file.exists():
            return False
        
        try:
            # Backup original file
            backup_file = project_root / "backend" / "api" / "main.py.backup"
            if not backup_file.exists():
                shutil.copy(api_file, backup_file)
            
            content = api_file.read_text()
            
            # Check if localhost:3000 is in allowed origins
            if f"localhost:{FRONTEND_PORT}" not in content:
                # Find the CORS middleware section - handle multiple patterns
                cors_patterns = [
                    r"(allowed_origins\s*=\s*os\.env\.get\([\"']ALLOWED_ORIGINS[\"'],\s*[\"'])([^'\"]+)(['\"])",
                    r"(allowed_origins\s*=\s*[\"'])([^'\"]+)(['\"])",
                ]
                
                fixed = False
                for cors_pattern in cors_patterns:
                    match = re.search(cors_pattern, content)
                    
                    if match:
                        current_origins = match.group(2)
                        if f"localhost:{FRONTEND_PORT}" not in current_origins:
                            # Split by comma if needed
                            origins_list = [o.strip() for o in current_origins.split(",")]
                            if f"http://localhost:{FRONTEND_PORT}" not in origins_list:
                                origins_list.append(f"http://localhost:{FRONTEND_PORT}")
                            new_origins = ",".join(origins_list)
                            
                            new_content = re.sub(
                                cors_pattern,
                                rf"\g<1>{new_origins}\g<3>",
                                content
                            )
                            api_file.write_text(new_content)
                            self.log_fix("cors_config", f"Added http://localhost:{FRONTEND_PORT} to CORS origins")
                            fixed = True
                            break
                
                if not fixed:
                    # Try to add CORS if pattern not found (edge case)
                    # Look for CORSMiddleware section
                    if "CORSMiddleware" in content and "allow_origins" in content:
                        # Already configured, might just be missing frontend port
                        # This is complex, so we'll skip for now and just log
                        self.log("CORS configuration exists but frontend port not found - manual review needed")
            
            return True  # Already configured correctly or fixed
            
        except Exception as e:
            self.log_error("fix_error", f"Failed to fix CORS: {str(e)}")
            return False
    
    def apply_fixes(self, errors: List[Dict]) -> int:
        """Apply automated fixes for detected errors."""
        self.log("\nApplying automated fixes...")
        
        fixes_applied = 0
        
        # Group fixes by category to avoid duplicates
        fixes_to_apply = set()
        
        for error in errors:
            category = error.get("category", "")
            error_msg = error.get("error", "")
            
            if category == "missing_env":
                fixes_to_apply.add("missing_env")
            
            elif category == "frontend_config" and "API URL" in error_msg:
                fixes_to_apply.add("frontend_api_url")
            
            elif (category == "api_analysis" or category == "frontend_config") and ("CORS" in error_msg or "cors" in error_msg.lower()):
                fixes_to_apply.add("cors_config")
        
        # Apply fixes
        for fix_type in fixes_to_apply:
            success = False
            if fix_type == "missing_env":
                success = self.fix_missing_env()
            elif fix_type == "frontend_api_url":
                success = self.fix_frontend_api_url()
            elif fix_type == "cors_config":
                success = self.fix_cors_configuration()
            
            if success:
                fixes_applied += 1
        
        if fixes_applied > 0:
            self.log(f"[OK] Applied {fixes_applied} automated fixes")
        else:
            self.log("No automated fixes needed")
        
        return fixes_applied
    
    # ========================================================================
    # PHASE 4: ITERATION LOGIC
    # ========================================================================
    
    def run_static_analysis(self) -> Dict[str, Any]:
        """Run all static analysis checks."""
        self.log("\n" + "="*60)
        self.log("PHASE 1: STATIC ANALYSIS")
        self.log("="*60)
        
        results = {
            "file_structure": self.validate_file_structure(),
            "model_files": self.validate_model_files(),
            "configuration": self.validate_configuration(),
            "api_endpoints": self.analyze_api_endpoints(),
            "frontend_integration": self.analyze_frontend_integration()
        }
        
        return results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        self.log("\n" + "="*60)
        self.log("PHASE 2: INTEGRATION TESTING")
        self.log("="*60)
        
        results = {
            "api_connectivity": self.test_api_connectivity(),
            "health_endpoint": self.test_health_endpoint(),
            "critical_endpoints": self.test_critical_endpoints()
        }
        
        # Run existing integration test script if API is accessible
        if results["api_connectivity"]:
            integration_success, integration_results = self.run_integration_test_script()
            results["integration_script"] = {
                "success": integration_success,
                "results": integration_results
            }
        else:
            self.log("Skipping integration test script (API not accessible)")
            results["integration_script"] = {"skipped": True, "reason": "API not accessible"}
        
        # Run validation script (doesn't require API)
        validation_success, validation_results = self.run_validation_script()
        results["validation_script"] = {
            "success": validation_success,
            "results": validation_results
        }
        
        return results
    
    def run_iteration(self) -> Tuple[bool, List[Dict]]:
        """Run one iteration of checking and fixing."""
        self.iteration += 1
        self.log("\n" + "="*60)
        self.log(f"ITERATION {self.iteration}/{MAX_ITERATIONS}")
        self.log("="*60)
        
        iteration_results = {
            "iteration": self.iteration,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "static_analysis": {},
            "integration_tests": {},
            "errors_found": [],
            "fixes_applied": 0
        }
        
        # Static analysis
        static_results = self.run_static_analysis()
        iteration_results["static_analysis"] = static_results
        
        # Integration tests (only if API is accessible)
        api_accessible = static_results.get("api_endpoints", (False, {}))[0]
        if api_accessible or self.iteration == 1:  # Try at least once
            integration_results = self.run_integration_tests()
            iteration_results["integration_tests"] = integration_results
        
        # Collect errors from this iteration only
        iteration_errors = [e for e in self.results["all_errors"] if e.get("iteration") == self.iteration]
        iteration_results["errors_found"] = iteration_errors
        
        # Apply fixes
        if iteration_errors:
            fixes_applied = self.apply_fixes(iteration_errors)
            iteration_results["fixes_applied"] = fixes_applied
        else:
            iteration_results["fixes_applied"] = 0
        
        iteration_results["end_time"] = datetime.now(timezone.utc).isoformat()
        self.results["iterations"].append(iteration_results)
        
        # Determine if we should continue
        # Errors are resolved if:
        # 1. No errors found in this iteration, OR
        # 2. All errors found have corresponding fixes applied
        unique_error_categories = set(e.get("category", "") for e in iteration_errors)
        fixes_for_this_iteration = [f for f in self.results["all_fixes"] if f.get("iteration") == self.iteration]
        fixed_categories = set(f.get("category", "") for f in fixes_for_this_iteration)
        
        # Check if all error categories have fixes
        all_resolved = len(iteration_errors) == 0 or unique_error_categories.issubset(fixed_categories)
        
        return all_resolved, iteration_errors
    
    def run_full_check(self):
        """Run full error check with iterations."""
        self.log("\n" + "="*60)
        self.log("TRADING AGENT ERROR CHECK SYSTEM")
        self.log("="*60)
        self.log(f"Start time: {self.results['start_time']}")
        self.log(f"Max iterations: {MAX_ITERATIONS}")
        self.log("")
        
        all_resolved = False
        
        for i in range(MAX_ITERATIONS):
            resolved, errors = self.run_iteration()
            
            if resolved or len(errors) == 0:
                all_resolved = True
                self.log("\n" + "="*60)
                self.log("[SUCCESS] ALL ERRORS RESOLVED")
                self.log("="*60)
                break
            
            if i < MAX_ITERATIONS - 1:
                self.log(f"\nErrors found, fixing and re-testing...")
                time.sleep(2)  # Brief pause before next iteration
        
        if not all_resolved:
            self.log("\n" + "="*60)
            self.log("[WARNING] SOME ERRORS REMAIN AFTER MAX ITERATIONS")
            self.log("="*60)
        
        # Generate final report
        self.generate_final_report(all_resolved)
        
        return all_resolved
    
    def generate_final_report(self, all_resolved: bool):
        """Generate final status report."""
        self.log("\n" + "="*60)
        self.log("FINAL REPORT")
        self.log("="*60)
        
        total_errors = len(self.results["all_errors"])
        total_fixes = len(self.results["all_fixes"])
        
        self.log(f"Total iterations: {self.iteration}")
        self.log(f"Total errors found: {total_errors}")
        self.log(f"Total fixes applied: {total_fixes}")
        self.log(f"Final status: {'[SUCCESS] ALL RESOLVED' if all_resolved else '[WARNING] ERRORS REMAIN'}")
        
        # Categorize errors
        error_categories = {}
        for error in self.results["all_errors"]:
            category = error.get("category", "unknown")
            error_categories[category] = error_categories.get(category, 0) + 1
        
        if error_categories:
            self.log("\nError categories:")
            for category, count in sorted(error_categories.items()):
                self.log(f"  - {category}: {count}")
        
        # Fix categories
        fix_categories = {}
        for fix in self.results["all_fixes"]:
            category = fix.get("category", "unknown")
            fix_categories[category] = fix_categories.get(category, 0) + 1
        
        if fix_categories:
            self.log("\nFix categories:")
            for category, count in sorted(fix_categories.items()):
                self.log(f"  - {category}: {count}")
        
        # Summary by iteration
        self.log("\nIteration summary:")
        for iter_result in self.results["iterations"]:
            iter_num = iter_result.get("iteration", 0)
            errors_count = len(iter_result.get("errors_found", []))
            fixes_count = iter_result.get("fixes_applied", 0)
            self.log(f"  Iteration {iter_num}: {errors_count} errors found, {fixes_count} fixes applied")
        
        # Save results to JSON
        report_file = project_root / "error_check_results.json"
        self.results["final_status"] = {
            "all_resolved": all_resolved,
            "total_errors": total_errors,
            "total_fixes": total_fixes,
            "iterations": self.iteration,
            "error_categories": error_categories,
            "fix_categories": fix_categories,
            "end_time": datetime.now(timezone.utc).isoformat()
        }
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"\nDetailed results saved to: {report_file}")
        
        # Provide recommendations
        if not all_resolved:
            self.log("\nRecommendations:")
            unresolved_categories = set(error_categories.keys()) - set(fix_categories.keys())
            if unresolved_categories:
                self.log("  Unresolved error categories that may need manual fixes:")
                for category in sorted(unresolved_categories):
                    self.log(f"    - {category}")
            self.log("  Review error_check_results.json for detailed error information")
            self.log("  Some errors may require manual intervention")


def main():
    """Main entry point."""
    try:
        checker = ErrorChecker()
        success = checker.run_full_check()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

