"""
Diagnostic endpoints for backend API
Provides metrics and diagnostic information for the monitoring system
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, List, Any
import psutil
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger
from src.shared_state import shared_state
from backend.monitoring.prometheus_metrics import metrics_collector

router = APIRouter(prefix="/api/v1/diagnostic", tags=["Diagnostic"])


@router.get("/metrics")
async def get_diagnostic_metrics() -> Dict[str, Any]:
    """
    Get comprehensive diagnostic metrics for monitoring service
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Shared state metrics
        state_status = shared_state.get_status()
        
        # Backend uptime
        start_time = getattr(get_diagnostic_metrics, 'start_time', datetime.utcnow())
        if not hasattr(get_diagnostic_metrics, 'start_time'):
            get_diagnostic_metrics.start_time = start_time
        
        uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "backend": {
                "uptime_seconds": uptime_seconds,
                "status": "running",
                "trading_agent_connected": state_status['is_trading_agent_running']
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "memory_total_mb": memory.total / 1024 / 1024,
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / 1024 / 1024 / 1024,
                "disk_total_gb": disk.total / 1024 / 1024 / 1024
            },
            "trading_agent": state_status
        }
        
    except Exception as e:
        logger.error(f"Error getting diagnostic metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_recent_logs(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent log entries from the log file
    """
    try:
        log_file = Path(project_root) / "logs" / "kubera_pokisham.log"
        
        if not log_file.exists():
            return {
                "logs": [],
                "message": "Log file not found"
            }
        
        # Read last N lines from log file
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            recent_lines = lines[-limit:]
        
        logs = []
        for line in recent_lines:
            # Try to parse structured logs
            try:
                import json
                if line.strip().startswith('{'):
                    log_data = json.loads(line)
                    logs.append(log_data)
                else:
                    logs.append({
                        "message": line.strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                logs.append({
                    "message": line.strip(),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return {
            "logs": logs,
            "count": len(logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance-related metrics
    """
    try:
        # Get process info
        process = psutil.Process()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "process": {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "num_threads": process.num_threads(),
                "connections": len(process.connections())
            },
            "shared_state": shared_state.get_status()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report")
async def report_diagnostic_event(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Receive diagnostic events from other components
    
    Example:
    {
        "component": "trading_agent",
        "event_type": "trade_executed",
        "data": {...}
    }
    """
    try:
        logger.info("Diagnostic event received", 
                   component=event.get('component'),
                   event_type=event.get('event_type'))
        
        # Record in metrics collector
        metrics_collector.record_event(
            event.get('event_type', 'unknown'),
            event.get('component', 'unknown')
        )
        
        return {
            "status": "success",
            "message": "Event recorded"
        }
        
    except Exception as e:
        logger.error(f"Error recording diagnostic event", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
