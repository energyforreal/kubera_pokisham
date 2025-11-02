"""
Diagnostic Reporter - Reports metrics and events to diagnostic service
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.core.logger import logger


class DiagnosticReporter:
    """Reports diagnostic events to the diagnostic service."""
    
    def __init__(self, diagnostic_url: str = "http://localhost:8080/api"):
        self.diagnostic_url = diagnostic_url
        self.enabled = True
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def report_event(self, event_type: str, component: str, data: Dict[str, Any]):
        """
        Report a diagnostic event.
        
        Args:
            event_type: Type of event (e.g., 'trade_executed', 'signal_generated')
            component: Component name (e.g., 'trading_agent')
            data: Event data
        """
        if not self.enabled:
            return
        
        try:
            if not self.session:
                await self.initialize()
            
            payload = {
                "component": component,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            async with self.session.post(
                f"{self.diagnostic_url}/events",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    logger.warning(
                        "Failed to report diagnostic event",
                        status=response.status,
                        event_type=event_type
                    )
        
        except asyncio.TimeoutError:
            logger.debug("Diagnostic report timeout", event_type=event_type)
        except Exception as e:
            logger.debug("Failed to report diagnostic event", error=str(e))
    
    async def report_trade_execution(self, trade_result: Dict[str, Any]):
        """Report a trade execution event."""
        await self.report_event(
            event_type="trade_executed",
            component="trading_agent",
            data={
                "symbol": trade_result.get('symbol'),
                "side": trade_result.get('side'),
                "status": trade_result.get('status'),
                "price": trade_result.get('price'),
                "confidence": trade_result.get('confidence')
            }
        )
    
    async def report_signal_generation(self, signal: Dict[str, Any]):
        """Report a signal generation event."""
        await self.report_event(
            event_type="signal_generated",
            component="trading_agent",
            data={
                "symbol": signal.get('symbol'),
                "prediction": signal.get('prediction'),
                "confidence": signal.get('confidence'),
                "is_actionable": signal.get('is_actionable')
            }
        )
    
    async def report_error(self, error_message: str, context: Dict[str, Any] = None):
        """Report an error event."""
        await self.report_event(
            event_type="error",
            component="trading_agent",
            data={
                "message": error_message,
                "context": context or {}
            }
        )
    
    async def report_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Report a performance metric."""
        await self.report_event(
            event_type="performance_metric",
            component="trading_agent",
            data={
                "metric_name": metric_name,
                "value": value,
                "unit": unit
            }
        )


# Global instance
_reporter: Optional[DiagnosticReporter] = None


def get_diagnostic_reporter() -> DiagnosticReporter:
    """Get global diagnostic reporter instance."""
    global _reporter
    if _reporter is None:
        _reporter = DiagnosticReporter()
    return _reporter

