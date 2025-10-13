"""Configuration management for Kubera Pokisham."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Delta Exchange API
    delta_api_key: str = Field(default="", alias="DELTA_API_KEY")
    delta_api_secret: str = Field(default="", alias="DELTA_API_SECRET")
    delta_api_url: str = Field(default="https://api.india.delta.exchange", alias="DELTA_API_URL")
    
    # Telegram Bot
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    
    # Trading Configuration
    initial_balance: float = Field(default=10000.0, alias="INITIAL_BALANCE")
    trading_mode: str = Field(default="paper", alias="TRADING_MODE")
    trading_symbol: str = Field(default="BTCUSD", alias="TRADING_SYMBOL")
    
    # Database
    database_url: str = Field(default="sqlite:///./kubera_pokisham.db", alias="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="logs/kubera_pokisham.log", alias="LOG_FILE")
    
    # Risk Management
    max_position_size: float = Field(default=0.25, alias="MAX_POSITION_SIZE")
    risk_per_trade: float = Field(default=0.02, alias="RISK_PER_TRADE")
    max_daily_loss: float = Field(default=0.05, alias="MAX_DAILY_LOSS")
    max_drawdown: float = Field(default=0.15, alias="MAX_DRAWDOWN")
    max_consecutive_losses: int = Field(default=5, alias="MAX_CONSECUTIVE_LOSSES")
    min_time_between_trades: int = Field(default=300, alias="MIN_TIME_BETWEEN_TRADES")
    
    # Model Configuration
    model_path: str = Field(default="models/xgboost_model.pkl", alias="MODEL_PATH")
    min_confidence_threshold: float = Field(default=0.65, alias="MIN_CONFIDENCE_THRESHOLD")
    
    # Market Data
    update_interval: int = Field(default=900, alias="UPDATE_INTERVAL")
    timeframes: str = Field(default="15m,1h,4h", alias="TIMEFRAMES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True


class TradingConfig:
    """Trading configuration loaded from YAML."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @property
    def trading(self) -> dict:
        return self.config.get('trading', {})
    
    @property
    def position_sizing(self) -> dict:
        return self.config.get('position_sizing', {})
    
    @property
    def risk_management(self) -> dict:
        return self.config.get('risk_management', {})
    
    @property
    def signal_filters(self) -> dict:
        return self.config.get('signal_filters', {})
    
    @property
    def execution(self) -> dict:
        return self.config.get('execution', {})
    
    @property
    def model(self) -> dict:
        return self.config.get('model', {})
    
    @property
    def features(self) -> dict:
        return self.config.get('features', {})
    
    @property
    def alerts(self) -> dict:
        return self.config.get('alerts', {})
    
    def get_timeframes(self) -> List[str]:
        """Get list of timeframes to analyze."""
        return self.trading.get('timeframes', ['15m', '1h', '4h'])
    
    def get_sma_periods(self) -> List[int]:
        """Get SMA periods for feature engineering."""
        return self.features.get('sma_periods', [10, 20, 50, 100, 200])
    
    def get_ema_periods(self) -> List[int]:
        """Get EMA periods for feature engineering."""
        return self.features.get('ema_periods', [9, 12, 26, 50])


# Global settings instance
settings = Settings()
trading_config = TradingConfig()

