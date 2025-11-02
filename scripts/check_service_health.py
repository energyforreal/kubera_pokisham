#!/usr/bin/env python3
"""
Service Health Check Polling Script

Replaces fixed timeouts with intelligent health check polling.
Ensures services are actually ready before proceeding.
"""

import time
import requests
import subprocess
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class ServiceHealthChecker:
    """Checks service health with intelligent polling."""
    
    def __init__(self):
        self.services = {
            'backend_api': {
                'url': 'http://localhost:8000/api/v1/health',
                'timeout': 5,
                'max_wait': 60,  # Maximum wait time in seconds
                'poll_interval': 2,  # Check every 2 seconds
                'startup_command': 'python backend/api/main.py'
            },
            'diagnostic_service': {
                'url': 'http://localhost:8080/api',
                'timeout': 5,
                'max_wait': 45,
                'poll_interval': 2,
                'startup_command': 'npm start'
            },
            'frontend_dashboard': {
                'url': 'http://localhost:3000',
                'timeout': 5,
                'max_wait': 30,
                'poll_interval': 2,
                'startup_command': 'npm run dev'
            },
            'diagnostic_dashboard': {
                'url': 'http://localhost:3001',
                'timeout': 5,
                'max_wait': 30,
                'poll_interval': 2,
                'startup_command': 'npm run dev'
            }
        }
    
    def check_service_health(self, service_name: str) -> Tuple[bool, str, float]:
        """
        Check if a service is healthy.
        
        Returns:
            Tuple of (is_healthy, message, response_time_ms)
        """
        service_config = self.services[service_name]
        
        try:
            start_time = time.time()
            response = requests.get(
                service_config['url'], 
                timeout=service_config['timeout']
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return True, f"Service healthy (HTTP {response.status_code})", response_time
            else:
                return False, f"Service returned HTTP {response.status_code}", response_time
                
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - service not running", 0
        except requests.exceptions.Timeout:
            return False, f"Request timeout after {service_config['timeout']}s", 0
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {e}", 0
        except Exception as e:
            return False, f"Unexpected error: {e}", 0
    
    def wait_for_service(self, service_name: str, verbose: bool = True) -> Tuple[bool, str]:
        """
        Wait for a service to become healthy.
        
        Returns:
            Tuple of (success, final_message)
        """
        service_config = self.services[service_name]
        max_wait = service_config['max_wait']
        poll_interval = service_config['poll_interval']
        
        if verbose:
            print(f"⏳ Waiting for {service_name} to start (max {max_wait}s)...")
        
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < max_wait:
            attempt += 1
            is_healthy, message, response_time = self.check_service_health(service_name)
            
            if is_healthy:
                elapsed = time.time() - start_time
                if verbose:
                    print(f"✅ {service_name} is healthy! ({elapsed:.1f}s, {response_time:.0f}ms)")
                return True, f"Service started successfully in {elapsed:.1f}s"
            
            if verbose and attempt % 5 == 0:  # Show progress every 10 seconds
                elapsed = time.time() - start_time
                print(f"   Attempt {attempt}: {message} (elapsed: {elapsed:.1f}s)")
            
            time.sleep(poll_interval)
        
        # Timeout reached
        elapsed = time.time() - start_time
        timeout_msg = f"Service failed to start within {max_wait}s"
        if verbose:
            print(f"❌ {service_name} timeout: {timeout_msg}")
        return False, timeout_msg
    
    def check_all_services(self) -> Dict[str, Tuple[bool, str]]:
        """Check health of all services."""
        results = {}
        
        print("🔍 Checking service health...")
        print("=" * 60)
        
        for service_name in self.services.keys():
            is_healthy, message, response_time = self.check_service_health(service_name)
            results[service_name] = (is_healthy, message)
            
            status_icon = "✅" if is_healthy else "❌"
            print(f"{status_icon} {service_name}: {message}")
            if response_time > 0:
                print(f"   Response time: {response_time:.0f}ms")
        
        return results
    
    def wait_for_all_services(self, services: List[str], verbose: bool = True) -> Tuple[bool, List[str]]:
        """
        Wait for multiple services to become healthy.
        
        Returns:
            Tuple of (all_successful, list_of_failed_services)
        """
        failed_services = []
        
        if verbose:
            print(f"⏳ Waiting for {len(services)} services to start...")
            print("=" * 60)
        
        for service_name in services:
            success, message = self.wait_for_service(service_name, verbose)
            if not success:
                failed_services.append(service_name)
        
        all_successful = len(failed_services) == 0
        
        if verbose:
            print("=" * 60)
            if all_successful:
                print("✅ All services started successfully!")
            else:
                print(f"❌ {len(failed_services)} service(s) failed to start: {', '.join(failed_services)}")
        
        return all_successful, failed_services
    
    def get_service_startup_order(self) -> List[str]:
        """Get recommended service startup order."""
        return [
            'backend_api',           # Start first - other services depend on it
            'diagnostic_service',    # Independent service
            'frontend_dashboard',    # Depends on backend_api
            'diagnostic_dashboard'   # Depends on diagnostic_service
        ]
    
    def check_port_availability(self, service_name: str) -> bool:
        """Check if service port is available before starting."""
        import socket
        
        service_config = self.services[service_name]
        port = int(service_config['url'].split(':')[-1].split('/')[0])
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                print(f"⚠️  Port {port} is already in use for {service_name}")
                return False
            else:
                print(f"✅ Port {port} is available for {service_name}")
                return True
        except Exception as e:
            print(f"❌ Error checking port {port}: {e}")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Service Health Checker')
    parser.add_argument('--service', help='Check specific service')
    parser.add_argument('--wait', action='store_true', help='Wait for services to start')
    parser.add_argument('--all', action='store_true', help='Check all services')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    checker = ServiceHealthChecker()
    
    if args.service:
        # Check specific service
        if args.service not in checker.services:
            print(f"❌ Unknown service: {args.service}")
            print(f"Available services: {', '.join(checker.services.keys())}")
            sys.exit(1)
        
        if args.wait:
            success, message = checker.wait_for_service(args.service, args.verbose)
            sys.exit(0 if success else 1)
        else:
            is_healthy, message, response_time = checker.check_service_health(args.service)
            print(f"{'✅' if is_healthy else '❌'} {args.service}: {message}")
            sys.exit(0 if is_healthy else 1)
    
    elif args.all:
        # Check all services
        results = checker.check_all_services()
        all_healthy = all(result[0] for result in results.values())
        sys.exit(0 if all_healthy else 1)
    
    elif args.wait:
        # Wait for all services in startup order
        services = checker.get_service_startup_order()
        success, failed = checker.wait_for_all_services(services, args.verbose)
        sys.exit(0 if success else 1)
    
    else:
        # Default: check all services
        results = checker.check_all_services()
        all_healthy = all(result[0] for result in results.values())
        
        print("\n💡 Usage:")
        print("  python scripts/check_service_health.py --wait    # Wait for all services")
        print("  python scripts/check_service_health.py --service backend_api --wait")
        print("  python scripts/check_service_health.py --all     # Check all services")
        
        sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()

