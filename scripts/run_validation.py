#!/usr/bin/env python3
"""
Enhanced Validation Runner
Runs all validation scripts with proper service management.
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

def run_script(script_path, script_name):
    """Run a validation script and return results."""
    print(f"\n🔍 Running {script_name}...")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], cwd=Path(__file__).parent.parent, 
           capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            return {
                'script': script_name,
                'status': 'PASS',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            print(f"❌ {script_name} failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return {
                'script': script_name,
                'status': 'FAIL',
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {script_name} timed out")
        return {
            'script': script_name,
            'status': 'TIMEOUT',
            'returncode': -1,
            'stdout': '',
            'stderr': 'Script timed out after 60 seconds'
        }
    except Exception as e:
        print(f"❌ {script_name} failed with exception: {e}")
        return {
            'script': script_name,
            'status': 'ERROR',
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def check_service_dependencies():
    """Check if required services are running."""
    print("🔍 Checking service dependencies...")
    
    # Check trading agent
    trading_agent_ok = False
    try:
        health_file = Path('bot_health.json')
        if health_file.exists():
            with open(health_file) as f:
                health_data = json.load(f)
                if health_data.get('status') == 'healthy':
                    trading_agent_ok = True
                    print("✅ Trading agent is healthy")
    except:
        pass
    
    if not trading_agent_ok:
        print("❌ Trading agent not running")
        return False
    
    # Check backend API
    backend_api_ok = False
    try:
        import requests
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            backend_api_ok = True
            print("✅ Backend API is responding")
    except:
        pass
    
    if not backend_api_ok:
        print("❌ Backend API not running")
        return False
    
    return True

def run_validation_suite():
    """Run the complete validation suite."""
    print("🧪 Running KUBERA POKISHAM Validation Suite...")
    print("=" * 60)
    
    # Check service dependencies first
    if not check_service_dependencies():
        print("\n❌ Service dependencies not met.")
        print("Please start required services first:")
        print("1. python scripts/start_services.py")
        print("2. Or manually start services:")
        print("   - Trading agent: python src/main.py")
        print("   - Backend API: cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return False
    
    scripts = [
        ('scripts/check_service_dependencies.py', 'Service Dependencies'),
        ('scripts/check_integrations.py', 'Integration Health'),
        ('scripts/validate_sync.py', 'Synchronization Validation'),
        ('scripts/test_realtime.py', 'Real-time Communication'),
        ('scripts/check_data_consistency.py', 'Data Consistency')
    ]
    
    results = []
    start_time = time.time()
    
    for script_path, script_name in scripts:
        result = run_script(script_path, script_name)
        results.append(result)
    
    # Calculate summary
    total_time = time.time() - start_time
    total_scripts = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] in ['ERROR', 'TIMEOUT'])
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 Validation Suite Summary:")
    print("=" * 60)
    print(f"   Total Scripts: {total_scripts}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Errors: {errors}")
    print(f"   Success Rate: {(passed/total_scripts)*100:.1f}%")
    print(f"   Total Time: {total_time:.2f}s")
    
    # Show detailed results
    print("\n📋 Detailed Results:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
        print(f"   {status_emoji} {result['script']}: {result['status']}")
        if result['stderr'] and result['status'] != 'PASS':
            print(f"      Error: {result['stderr'][:100]}...")
    
    # Save results
    results_data = {
        'summary': {
            'total_scripts': total_scripts,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed/total_scripts)*100,
            'total_time_seconds': total_time,
            'timestamp': datetime.now(timezone.utc).isoformat()
        },
        'results': results
    }
    
    results_file = Path('validation_suite_results.json')
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Return success status
    if failed > 0 or errors > 0:
        print("\n❌ Some validations failed. Check the output above for details.")
        return False
    else:
        print("\n✅ All validations passed successfully!")
        return True

def main():
    """Main function."""
    try:
        success = run_validation_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Validation suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
