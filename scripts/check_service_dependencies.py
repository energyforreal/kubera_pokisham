#!/usr/bin/env python3
"""
Service Dependency Checker
Ensures all required services are running before validation.
"""

import asyncio
import aiohttp
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger

class ServiceDependencyChecker:
    """Check that all required services are running."""
    
    def __init__(self):
        self.services = {
            'trading_agent': {
                'health_file': 'bot_health.json',
                'required': True
            },
            'backend_api': {
                'url': 'http://localhost:8000/api/v1/health',
                'required': True
            },
            'database': {
                'file': 'kubera_pokisham.db',
                'required': True
            }
        }
    
    async def check_all_services(self):
        """Check all service dependencies."""
        results = {}
        
        # Check trading agent
        results['trading_agent'] = await self._check_trading_agent()
        
        # Check backend API
        results['backend_api'] = await self._check_backend_api()
        
        # Check database
        results['database'] = await self._check_database()
        
        return results
    
    async def _check_trading_agent(self):
        """Check if trading agent is running."""
        try:
            health_file = Path('bot_health.json')
            if not health_file.exists():
                return {'status': 'FAIL', 'details': 'Health file not found - trading agent not running'}
            
            with open(health_file) as f:
                health_data = json.load(f)
            
            if health_data.get('status') == 'healthy':
                return {'status': 'PASS', 'details': 'Trading agent is healthy'}
            else:
                return {'status': 'FAIL', 'details': f"Trading agent status: {health_data.get('status')}"}
                
        except Exception as e:
            return {'status': 'FAIL', 'details': f'Error checking trading agent: {e}'}
    
    async def _check_backend_api(self):
        """Check if backend API is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8000/api/v1/health', timeout=5) as response:
                    if response.status == 200:
                        return {'status': 'PASS', 'details': 'Backend API is responding'}
                    else:
                        return {'status': 'FAIL', 'details': f'Backend API returned status {response.status}'}
        except Exception as e:
            return {'status': 'FAIL', 'details': f'Backend API not responding: {e}'}
    
    async def _check_database(self):
        """Check if database is accessible."""
        try:
            db_file = Path('kubera_pokisham.db')
            if db_file.exists():
                return {'status': 'PASS', 'details': 'Database file exists'}
            else:
                return {'status': 'WARN', 'details': 'Database file not found (will be created on first run)'}
        except Exception as e:
            return {'status': 'FAIL', 'details': f'Error checking database: {e}'}

async def main():
    """Main function."""
    print("🔍 Checking service dependencies...")
    print("=" * 50)
    
    checker = ServiceDependencyChecker()
    results = await checker.check_all_services()
    
    all_passed = True
    for service, result in results.items():
        status = result['status']
        details = result['details']
        
        if status == 'PASS':
            print(f"✅ {service}: {details}")
        elif status == 'WARN':
            print(f"⚠️  {service}: {details}")
        else:
            print(f"❌ {service}: {details}")
            all_passed = False
    
    print("=" * 50)
    
    if not all_passed:
        print("\n❌ Some services are not running. Please start required services before running validation.")
        print("\nTo start services:")
        print("1. Start trading agent: python src/main.py")
        print("2. Start backend API: cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    else:
        print("\n✅ All required services are running. Validation can proceed.")

if __name__ == "__main__":
    asyncio.run(main())
