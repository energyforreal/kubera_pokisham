"""Check trading bot health status."""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))


def check_health():
    """Check bot health and display status."""
    health_file = Path("bot_health.json")
    
    print("="*60)
    print("🏥 TRADING BOT HEALTH CHECK")
    print("="*60)
    
    if not health_file.exists():
        print("\n❌ Health file not found!")
        print("   Bot may not be running or health check not initialized")
        print("\n💡 To start bot: python src/main.py")
        return
    
    try:
        with open(health_file, 'r') as f:
            status = json.load(f)
        
        print("\n📊 Status Overview:")
        print(f"  ✅ Bot Alive: {status.get('is_alive', False)}")
        print(f"  🤖 Models Loaded: {status.get('models_loaded', 0)}")
        print(f"  🛡️  Circuit Breaker: {'🔴 ACTIVE' if status.get('circuit_breaker_active') else '🟢 Inactive'}")
        
        print("\n⏰ Timestamps:")
        last_heartbeat = status.get('last_heartbeat')
        if last_heartbeat:
            hb_dt = datetime.fromisoformat(last_heartbeat)
            age_seconds = (datetime.now(timezone.utc) - hb_dt).total_seconds()
            print(f"  Last Heartbeat: {last_heartbeat} ({age_seconds:.0f}s ago)")
            
            if age_seconds > 120:
                print("  ⚠️  WARNING: No heartbeat in last 2 minutes - bot may be stuck!")
        
        last_signal = status.get('last_signal')
        if last_signal:
            print(f"  Last Signal: {last_signal}")
        
        last_trade = status.get('last_trade')
        if last_trade:
            print(f"  Last Trade: {last_trade}")
        
        print("\n📈 Activity Counters:")
        print(f"  Signals Generated: {status.get('signals_count', 0)}")
        print(f"  Trades Executed: {status.get('trades_count', 0)}")
        print(f"  Errors Encountered: {status.get('errors_count', 0)}")
        
        if status.get('errors_count', 0) > 0:
            print("\n⚠️  Last Error:")
            last_error = status.get('last_error', {})
            print(f"  Message: {last_error.get('message', 'N/A')}")
            print(f"  Time: {last_error.get('timestamp', 'N/A')}")
        
        print("\n" + "="*60)
        
        # Health assessment
        is_healthy = status.get('is_alive') and last_heartbeat
        if is_healthy and age_seconds < 120:
            print("✅ Bot is HEALTHY and running normally")
        elif is_healthy and age_seconds < 300:
            print("⚠️  Bot is running but may be slow")
        else:
            print("❌ Bot appears to be DOWN or not responding")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error reading health file: {e}")
        return


if __name__ == "__main__":
    check_health()

