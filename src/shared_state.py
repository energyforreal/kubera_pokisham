"""Shared state manager for communication between trading agent and API."""

import threading
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.trading.paper_engine import PaperTradingEngine
from src.ml.predictor import TradingPredictor
from src.ml.multi_model_predictor import MultiModelPredictor
from src.data.delta_client import DeltaExchangeClient
from src.risk.risk_manager import RiskManager
from typing import Union


class SharedState:
    """Thread-safe shared state between trading agent and API."""
    
    _instance: Optional['SharedState'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.trading_engine: Optional[PaperTradingEngine] = None
            self.predictor: Optional[Union[TradingPredictor, MultiModelPredictor, Any]] = None
            self.delta_client: Optional[DeltaExchangeClient] = None
            self.risk_manager: Optional[RiskManager] = None
            self.is_trading_agent_running = False
            self.last_heartbeat = None
            self._initialized = True
    
    def set_trading_agent_components(
        self,
        trading_engine: PaperTradingEngine,
        predictor: Union[TradingPredictor, MultiModelPredictor, Any],
        delta_client: DeltaExchangeClient,
        risk_manager: RiskManager
    ):
        """Set components from trading agent."""
        with self._lock:
            self.trading_engine = trading_engine
            self.predictor = predictor
            self.delta_client = delta_client
            self.risk_manager = risk_manager
            self.is_trading_agent_running = True
            self.last_heartbeat = datetime.now(timezone.utc)
    
    def heartbeat(self):
        """Update heartbeat from trading agent."""
        with self._lock:
            self.last_heartbeat = datetime.now(timezone.utc)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        with self._lock:
            return {
                'is_trading_agent_running': self.is_trading_agent_running,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'has_trading_engine': self.trading_engine is not None,
                'has_predictor': self.predictor is not None,
                'has_delta_client': self.delta_client is not None,
                'has_risk_manager': self.risk_manager is not None
            }
    
    def clear(self):
        """Clear all components (when trading agent stops)."""
        with self._lock:
            self.trading_engine = None
            self.predictor = None
            self.delta_client = None
            self.risk_manager = None
            self.is_trading_agent_running = False
            self.last_heartbeat = None


# Global shared state instance
shared_state = SharedState()
