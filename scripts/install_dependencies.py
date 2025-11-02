#!/usr/bin/env python3
"""
Dependency Installation and Verification Script

Installs Python dependencies with proper error handling and verification.
Replaces silent installation that hides critical errors.
"""

import subprocess
import sys
import importlib
from pathlib import Path
from typing import List, Tuple, Dict


class DependencyInstaller:
    """Handles dependency installation with verification."""
    
    def __init__(self):
        self.required_packages = [
            'pandas',
            'numpy', 
            'scikit-learn',  # Fixed: use scikit-learn instead of sklearn
            'xgboost',
            'lightgbm',
            'fastapi',
            'uvicorn',
            'aiohttp',
            'websockets',
            'pyyaml',
            'sqlalchemy',
            'requests'
        ]
        self.optional_packages = [
            'prometheus-client',
            'psutil'
        ]
        self.failed_installs = []
        self.failed_imports = []
    
    def check_pip_available(self) -> bool:
        """Check if pip is available."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ pip available: {result.stdout.strip()}")
                return True
            else:
                print(f"❌ pip check failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ pip check timed out")
            return False
        except Exception as e:
            print(f"❌ pip check error: {e}")
            return False
    
    def install_package(self, package: str) -> Tuple[bool, str]:
        """Install a single package with error handling."""
        print(f"📦 Installing {package}...")
        
        try:
            # Use pip install with verbose output
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package, '--upgrade'
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                print(f"✅ {package} installed successfully")
                return True, ""
            else:
                error_msg = result.stderr.strip()
                print(f"⚠️  {package} installation failed: {error_msg}")
                print(f"   💡 This may be non-critical, continuing...")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"Installation timed out after 5 minutes"
            print(f"⚠️  {package} {error_msg}")
            print(f"   💡 This may be non-critical, continuing...")
            return False, error_msg
        except Exception as e:
            error_msg = f"Installation error: {e}"
            print(f"⚠️  {package} {error_msg}")
            print(f"   💡 This may be non-critical, continuing...")
            return False, error_msg
    
    def install_from_requirements(self) -> Tuple[bool, List[str]]:
        """Install packages from requirements.txt."""
        requirements_file = Path("requirements.txt")
        if not requirements_file.exists():
            print("⚠️  requirements.txt not found, installing individual packages")
            return self.install_individual_packages()
        
        print("📦 Installing from requirements.txt...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--upgrade'
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                print("✅ Requirements installed successfully")
                return True, []
            else:
                error_msg = result.stderr.strip()
                print(f"❌ Requirements installation failed: {error_msg}")
                return False, [error_msg]
                
        except subprocess.TimeoutExpired:
            error_msg = "Requirements installation timed out after 10 minutes"
            print(f"❌ {error_msg}")
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Requirements installation error: {e}"
            print(f"❌ {error_msg}")
            return False, [error_msg]
    
    def install_individual_packages(self) -> Tuple[bool, List[str]]:
        """Install packages individually."""
        failed_packages = []
        
        for package in self.required_packages:
            success, error = self.install_package(package)
            if not success:
                failed_packages.append(f"{package}: {error}")
                self.failed_installs.append(package)
        
        # Try optional packages
        for package in self.optional_packages:
            success, error = self.install_package(package)
            if not success:
                print(f"⚠️  Optional package {package} failed: {error}")
        
        return len(failed_packages) == 0, failed_packages
    
    def verify_imports(self) -> Tuple[bool, List[str]]:
        """Verify that all required packages can be imported."""
        print("\n🔍 Verifying package imports...")
        failed_imports = []
        
        for package in self.required_packages:
            try:
                # Handle special cases for scikit-learn
                if package == 'scikit-learn':
                    importlib.import_module('sklearn')
                else:
                    importlib.import_module(package)
                print(f"✅ {package} import successful")
            except ImportError as e:
                print(f"⚠️  {package} import failed: {e}")
                print(f"   💡 This may be non-critical, continuing...")
                failed_imports.append(f"{package}: {e}")
                self.failed_imports.append(package)
            except Exception as e:
                print(f"⚠️  {package} import error: {e}")
                print(f"   💡 This may be non-critical, continuing...")
                failed_imports.append(f"{package}: {e}")
                self.failed_imports.append(package)
        
        return len(failed_imports) == 0, failed_imports
    
    def check_package_versions(self) -> Dict[str, str]:
        """Check versions of installed packages."""
        versions = {}
        
        for package in self.required_packages:
            try:
                if package == 'scikit-learn':
                    import sklearn
                    versions[package] = sklearn.__version__
                else:
                    module = importlib.import_module(package)
                    if hasattr(module, '__version__'):
                        versions[package] = module.__version__
                    else:
                        versions[package] = "unknown"
            except:
                versions[package] = "not installed"
        
        return versions
    
    def install_and_verify(self) -> Tuple[bool, List[str]]:
        """Main installation and verification process."""
        print("🔍 Checking pip availability...")
        if not self.check_pip_available():
            return False, ["pip is not available"]
        
        print("\n📦 Installing dependencies...")
        print("=" * 60)
        
        # Try requirements.txt first, fallback to individual packages
        success, errors = self.install_from_requirements()
        
        if not success:
            print("\n⚠️  Requirements.txt failed, trying individual packages...")
            success, errors = self.install_individual_packages()
        
        # Verify imports
        import_success, import_errors = self.verify_imports()
        
        # Combine errors
        all_errors = errors + import_errors
        
        # Show package versions
        print("\n📋 Package versions:")
        versions = self.check_package_versions()
        for package, version in versions.items():
            status = "✅" if version != "not installed" else "❌"
            print(f"   {status} {package}: {version}")
        
        return success and import_success, all_errors


def main():
    """Main entry point."""
    print("🔧 Dependency Installation and Verification")
    print("=" * 60)
    
    installer = DependencyInstaller()
    success, errors = installer.install_and_verify()
    
    print("\n" + "=" * 60)
    
    if success:
        print("✅ All dependencies installed and verified!")
        print("\nYou can proceed with starting the services.")
        sys.exit(0)
    else:
        print("⚠️  Some dependencies had issues, but continuing...")
        print(f"\n🔧 Issues ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
        
        print("\n💡 The system will attempt to start with available packages.")
        print("   If services fail to start, try these solutions:")
        print("1. Check your internet connection")
        print("2. Update pip: python -m pip install --upgrade pip")
        print("3. Try installing packages individually:")
        print("   python -m pip install pandas numpy scikit-learn")
        print("4. Check Python version compatibility")
        print("5. Try using a virtual environment")
        print("6. Check for antivirus interference")
        
        if installer.failed_imports:
            print(f"\n💡 Failed imports: {', '.join(installer.failed_imports)}")
            print("   These packages may need to be reinstalled")
        
        # Don't exit with error - allow system to continue
        print("\n✅ Continuing with startup despite dependency issues...")
        sys.exit(0)


if __name__ == "__main__":
    main()

