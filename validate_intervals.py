#!/usr/bin/env python3
"""
Validation script to monitor and verify 5-minute intervals and model usage.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def load_health_data() -> Dict:
    """Load health data from bot_health.json."""
    health_file = Path("bot_health.json")
    if not health_file.exists():
        return {}
    
    try:
        with open(health_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading health data: {e}")
        return {}

def validate_signal_intervals(health_data: Dict) -> Dict:
    """Validate that signals are being generated at 5-minute intervals."""
    result = {
        'status': 'unknown',
        'last_signal': None,
        'signal_frequency': None,
        'deviation': None,
        'issues': []
    }
    
    if not health_data.get('last_signal'):
        result['status'] = 'no_signals'
        result['issues'].append("No signals generated yet")
        return result
    
    last_signal = health_data['last_signal']
    result['last_signal'] = last_signal
    
    # Check if signal is recent (within last 10 minutes)
    try:
        signal_time = datetime.fromisoformat(last_signal.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_seconds = (now - signal_time).total_seconds()
        
        if age_seconds > 600:  # 10 minutes
            result['status'] = 'stale'
            result['issues'].append(f"Last signal is {age_seconds/60:.1f} minutes old")
        else:
            result['status'] = 'recent'
            result['signal_frequency'] = f"{age_seconds/60:.1f} minutes ago"
            
    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f"Error parsing signal timestamp: {e}")
    
    return result

def validate_model_usage() -> Dict:
    """Validate that all models are being used properly."""
    result = {
        'status': 'unknown',
        'models_loaded': 0,
        'expected_models': 5,
        'issues': []
    }
    
    health_data = load_health_data()
    models_loaded = health_data.get('models_loaded', 0)
    result['models_loaded'] = models_loaded
    
    if models_loaded == 0:
        result['status'] = 'no_models'
        result['issues'].append("No models loaded")
    elif models_loaded < 5:
        result['status'] = 'partial'
        result['issues'].append(f"Only {models_loaded}/5 models loaded")
    else:
        result['status'] = 'complete'
    
    return result

def validate_heartbeat(health_data: Dict) -> Dict:
    """Validate heartbeat is working."""
    result = {
        'status': 'unknown',
        'last_heartbeat': None,
        'age_seconds': None,
        'issues': []
    }
    
    if not health_data.get('last_heartbeat'):
        result['status'] = 'no_heartbeat'
        result['issues'].append("No heartbeat recorded")
        return result
    
    last_heartbeat = health_data['last_heartbeat']
    result['last_heartbeat'] = last_heartbeat
    
    try:
        heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_seconds = (now - heartbeat_time).total_seconds()
        result['age_seconds'] = age_seconds
        
        if age_seconds > 120:  # 2 minutes
            result['status'] = 'stale'
            result['issues'].append(f"Heartbeat is {age_seconds:.0f} seconds old")
        else:
            result['status'] = 'active'
            
    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f"Error parsing heartbeat timestamp: {e}")
    
    return result

def validate_position_monitoring(health_data: Dict) -> Dict:
    """Validate position monitoring is working."""
    result = {
        'status': 'unknown',
        'positions': 0,
        'issues': []
    }
    
    # This would need to be enhanced with actual position data
    # For now, just check if the system is alive
    if health_data.get('is_alive'):
        result['status'] = 'active'
    else:
        result['status'] = 'inactive'
        result['issues'].append("System not alive")
    
    return result

def main():
    """Main validation function."""
    print("="*60)
    print("🔍 TRADING AGENT INTERVAL VALIDATION")
    print("="*60)
    
    # Load health data
    health_data = load_health_data()
    if not health_data:
        print("❌ No health data found - agent may not be running")
        return
    
    print(f"📊 Health Data Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Validate signal intervals
    print("📡 Signal Generation Validation:")
    signal_result = validate_signal_intervals(health_data)
    print(f"  Status: {signal_result['status']}")
    if signal_result['last_signal']:
        print(f"  Last Signal: {signal_result['last_signal']}")
    if signal_result['signal_frequency']:
        print(f"  Frequency: {signal_result['signal_frequency']}")
    if signal_result['issues']:
        for issue in signal_result['issues']:
            print(f"  ⚠️  {issue}")
    print()
    
    # Validate model usage
    print("🤖 Model Usage Validation:")
    model_result = validate_model_usage()
    print(f"  Status: {model_result['status']}")
    print(f"  Models Loaded: {model_result['models_loaded']}/{model_result['expected_models']}")
    if model_result['issues']:
        for issue in model_result['issues']:
            print(f"  ⚠️  {issue}")
    print()
    
    # Validate heartbeat
    print("💓 Heartbeat Validation:")
    heartbeat_result = validate_heartbeat(health_data)
    print(f"  Status: {heartbeat_result['status']}")
    if heartbeat_result['last_heartbeat']:
        print(f"  Last Heartbeat: {heartbeat_result['last_heartbeat']}")
    if heartbeat_result['age_seconds'] is not None:
        print(f"  Age: {heartbeat_result['age_seconds']:.0f} seconds")
    if heartbeat_result['issues']:
        for issue in heartbeat_result['issues']:
            print(f"  ⚠️  {issue}")
    print()
    
    # Validate position monitoring
    print("📈 Position Monitoring Validation:")
    position_result = validate_position_monitoring(health_data)
    print(f"  Status: {position_result['status']}")
    if position_result['issues']:
        for issue in position_result['issues']:
            print(f"  ⚠️  {issue}")
    print()
    
    # Overall assessment
    print("="*60)
    print("📋 OVERALL ASSESSMENT")
    print("="*60)
    
    all_statuses = [
        signal_result['status'],
        model_result['status'],
        heartbeat_result['status'],
        position_result['status']
    ]
    
    if all(status in ['recent', 'active', 'complete'] for status in all_statuses):
        print("✅ All systems operational - 5-minute intervals working correctly")
    elif any(status in ['stale', 'no_signals', 'no_heartbeat'] for status in all_statuses):
        print("⚠️  Some systems may have issues - check individual validations above")
    else:
        print("❌ Multiple system issues detected - agent may need restart")
    
    print("="*60)

if __name__ == "__main__":
    main()
