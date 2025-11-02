-- Diagnostic System Database Schema

-- Health snapshots for tracking component health over time
CREATE TABLE IF NOT EXISTS health_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    status TEXT NOT NULL, -- 'healthy', 'warning', 'critical', 'unknown'
    response_time INTEGER, -- milliseconds
    details TEXT, -- JSON string with additional details
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_health_component ON health_snapshots(component);
CREATE INDEX idx_health_timestamp ON health_snapshots(timestamp);

-- Performance metrics for tracking system performance
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT, -- 'ms', 'percent', 'count', 'bytes'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_perf_component ON performance_metrics(component);
CREATE INDEX idx_perf_metric ON performance_metrics(metric_name);
CREATE INDEX idx_perf_timestamp ON performance_metrics(timestamp);

-- Alerts log for tracking all alerts sent
CREATE TABLE IF NOT EXISTS alerts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    component TEXT,
    details TEXT, -- JSON string
    channels_sent TEXT, -- JSON array of channels
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alerts_severity ON alerts_log(severity);
CREATE INDEX idx_alerts_timestamp ON alerts_log(timestamp);
CREATE INDEX idx_alerts_component ON alerts_log(component);

-- System logs aggregated from all components
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    level TEXT NOT NULL, -- 'debug', 'info', 'warning', 'error', 'critical'
    message TEXT NOT NULL,
    context TEXT, -- JSON string with additional context
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_timestamp ON system_logs(timestamp);

-- Component uptime tracking
CREATE TABLE IF NOT EXISTS component_uptime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL UNIQUE,
    total_uptime_seconds INTEGER DEFAULT 0,
    last_online DATETIME,
    last_offline DATETIME,
    downtime_count INTEGER DEFAULT 0
);

-- Trade execution metrics
CREATE TABLE IF NOT EXISTS trade_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT,
    symbol TEXT,
    side TEXT,
    status TEXT,
    execution_time_ms INTEGER,
    confidence REAL,
    pnl REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trade_timestamp ON trade_metrics(timestamp);
CREATE INDEX idx_trade_symbol ON trade_metrics(symbol);

