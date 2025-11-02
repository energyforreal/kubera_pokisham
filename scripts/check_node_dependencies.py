#!/usr/bin/env python3
"""
Node.js Dependency Checker and Installer

Automatically checks and installs Node.js dependencies for frontend services.
Prevents startup failures due to missing node_modules.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


class NodeDependencyChecker:
    """Handles Node.js dependency checking and installation."""
    
    def __init__(self):
        self.services = {
            'frontend_web': {
                'path': 'frontend_web',
                'package_json': 'frontend_web/package.json',
                'critical_packages': ['next', 'react', 'react-dom'],
                'description': 'Frontend Dashboard (Next.js)'
            },
            'diagnostic_service': {
                'path': 'diagnostic_service',
                'package_json': 'diagnostic_service/package.json',
                'critical_packages': ['express', 'ws', 'axios'],
                'description': 'Diagnostic Service (Node.js)'
            },
            'diagnostic_dashboard': {
                'path': 'diagnostic_dashboard',
                'package_json': 'diagnostic_dashboard/package.json',
                'critical_packages': ['next', 'react', 'react-dom'],
                'description': 'Diagnostic Dashboard (Next.js)'
            }
        }
        self.install_results = {}
    
    def check_npm_available(self) -> bool:
        """Check if npm is available."""
        try:
            # Try multiple ways to find npm
            npm_commands = ['npm', 'npm.cmd', 'npm.exe']
            for npm_cmd in npm_commands:
                try:
                    result = subprocess.run([npm_cmd, '--version'], 
                                         capture_output=True, text=True, timeout=5,
                                         shell=True)  # Use shell=True to inherit PATH
                    if result.returncode == 0:
                        print(f"✅ npm available: {result.stdout.strip()}")
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            print("❌ npm not found - please install Node.js")
            return False
        except Exception as e:
            print(f"❌ npm check error: {e}")
            return False
    
    def check_node_modules_exists(self, service_name: str) -> bool:
        """Check if node_modules directory exists for a service."""
        service_config = self.services[service_name]
        node_modules_path = Path(service_config['path']) / 'node_modules'
        return node_modules_path.exists() and node_modules_path.is_dir()
    
    def check_critical_packages(self, service_name: str) -> Tuple[bool, List[str]]:
        """Check if critical packages are installed."""
        service_config = self.services[service_name]
        service_path = Path(service_config['path'])
        missing_packages = []
        
        if not self.check_node_modules_exists(service_name):
            return False, service_config['critical_packages']
        
        for package in service_config['critical_packages']:
            package_path = service_path / 'node_modules' / package
            if not package_path.exists():
                missing_packages.append(package)
        
        return len(missing_packages) == 0, missing_packages
    
    def install_dependencies(self, service_name: str) -> Tuple[bool, str]:
        """Install dependencies for a service."""
        service_config = self.services[service_name]
        service_path = Path(service_config['path'])
        
        print(f"📦 Installing dependencies for {service_config['description']}...")
        
        try:
            # Change to service directory
            original_dir = os.getcwd()
            os.chdir(service_path)
            
            # Run npm install
            result = subprocess.run(['npm', 'install'], 
                                  capture_output=True, text=True, timeout=60,
                                  shell=True)  # Use shell=True to inherit PATH
            
            # Return to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print(f"✅ {service_config['description']} dependencies installed successfully")
                return True, ""
            else:
                error_msg = result.stderr.strip()
                print(f"❌ {service_config['description']} installation failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Installation timed out after 5 minutes"
            print(f"❌ {service_config['description']} {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Installation error: {e}"
            print(f"❌ {service_config['description']} {error_msg}")
            return False, error_msg
        finally:
            # Ensure we return to original directory
            try:
                os.chdir(original_dir)
            except:
                pass
    
    def check_and_install_all(self) -> Tuple[bool, Dict[str, str]]:
        """Check and install dependencies for all services."""
        print("🔍 Checking Node.js dependencies...")
        print("=" * 60)
        
        # Check npm availability first
        if not self.check_npm_available():
            return False, {"npm": "npm not available"}
        
        all_successful = True
        errors = {}
        
        for service_name, service_config in self.services.items():
            print(f"\n📋 Checking {service_config['description']}...")
            
            # Check if package.json exists
            package_json_path = Path(service_config['package_json'])
            if not package_json_path.exists():
                print(f"⚠️  {service_config['description']}: package.json not found")
                errors[service_name] = "package.json not found"
                all_successful = False
                continue
            
            # Check if node_modules exists
            if not self.check_node_modules_exists(service_name):
                print(f"⚠️  {service_config['description']}: node_modules missing")
                
                # Install dependencies
                success, error = self.install_dependencies(service_name)
                self.install_results[service_name] = {'success': success, 'error': error}
                
                if not success:
                    errors[service_name] = error
                    all_successful = False
                else:
                    print(f"✅ {service_config['description']}: Dependencies installed")
            else:
                # Check critical packages
                packages_ok, missing = self.check_critical_packages(service_name)
                if packages_ok:
                    print(f"✅ {service_config['description']}: All dependencies present")
                else:
                    print(f"⚠️  {service_config['description']}: Missing packages: {missing}")
                    
                    # Try to install missing packages
                    success, error = self.install_dependencies(service_name)
                    self.install_results[service_name] = {'success': success, 'error': error}
                    
                    if not success:
                        errors[service_name] = error
                        all_successful = False
                    else:
                        print(f"✅ {service_config['description']}: Dependencies reinstalled")
        
        return all_successful, errors
    
    def get_installation_summary(self) -> str:
        """Get a summary of installation results."""
        if not self.install_results:
            return "No installations performed"
        
        successful = sum(1 for r in self.install_results.values() if r['success'])
        total = len(self.install_results)
        
        return f"Installed {successful}/{total} services successfully"


def main():
    """Main entry point."""
    print("🔧 Node.js Dependency Checker and Installer")
    print("=" * 60)
    
    checker = NodeDependencyChecker()
    success, errors = checker.check_and_install_all()
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ All Node.js dependencies are ready!")
        print("\nYou can proceed with starting the services.")
        
        summary = checker.get_installation_summary()
        if summary != "No installations performed":
            print(f"\n📋 {summary}")
        
        sys.exit(0)
    else:
        print("❌ Some Node.js dependencies failed to install!")
        print(f"\n🔧 Errors ({len(errors)}):")
        for service, error in errors.items():
            print(f"   • {service}: {error}")
        
        print("\n🔧 SOLUTIONS:")
        print("1. Check your internet connection")
        print("2. Update npm: npm install -g npm@latest")
        print("3. Try installing manually:")
        print("   cd frontend_web && npm install")
        print("   cd diagnostic_service && npm install")
        print("4. Check Node.js version compatibility")
        print("5. Try clearing npm cache: npm cache clean --force")
        
        summary = checker.get_installation_summary()
        if summary != "No installations performed":
            print(f"\n📋 {summary}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
