# Diagnostic Service

Standalone Node.js service for monitoring the AI Trading System.

## Features

- **Health Monitoring**: Checks all components every 30 seconds
- **Performance Tracking**: Collects system and application metrics
- **Log Aggregation**: Watches and parses log files
- **Alert Manager**: Multi-channel alert dispatching
- **REST API**: Comprehensive API for querying data
- **WebSocket**: Real-time updates
- **Prometheus Integration**: Metrics export for Grafana

## Quick Start

### Installation

```bash
npm install
```

### Configuration

1. Copy `.env.example` to `.env` and configure
2. Update `config/config.json` for monitoring settings
3. Update `config/alerts.json` for alert rules

### Initialize Database

```bash
npm run init-db
```

### Start Service

Development:
```bash
npm run dev
```

Production:
```bash
npm start
```

## API Endpoints

### Health & Status

- `GET /api/health` - System health
- `GET /api/status/summary` - Dashboard summary
- `GET /api/uptime` - Component uptime

### Metrics

- `GET /api/metrics` - Current metrics
- `GET /api/metrics/:component` - Component metrics
- `GET /api/history/health/:component` - Health history

### Logs

- `GET /api/logs` - System logs
  - Query params: `component`, `level`, `limit`

### Alerts

- `GET /api/alerts` - Recent alerts
- `POST /api/alerts/test` - Test channels
- `POST /api/alerts/rules` - Reload config

### Prometheus

- `GET /metrics` - Prometheus metrics

## WebSocket

Connect to `ws://localhost:8080` for real-time updates:

- `health` messages - Health status updates
- `metrics` messages - Performance metrics

## Configuration

### config.json

```json
{
  "monitoring": {
    "healthCheckInterval": 30000,
    "performanceCheckInterval": 60000
  },
  "thresholds": {
    "responseTime": { "warning": 1000, "critical": 2000 }
  }
}
```

### alerts.json

```json
{
  "channels": {
    "telegram": { "enabled": true },
    "slack": { "enabled": false },
    "email": { "enabled": false }
  },
  "rules": [...]
}
```

## Database

SQLite database at `data/diagnostic.db`

Tables:
- health_snapshots
- performance_metrics
- alerts_log
- system_logs
- component_uptime
- trade_metrics

## Alert Channels

### Telegram
Set in `.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Slack
Set in `.env`:
- `SLACK_WEBHOOK_URL`

### Email
Set in `.env`:
- `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`
- `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASSWORD`
- `EMAIL_FROM`, `EMAIL_TO`

## Development

### Project Structure

```
diagnostic_service/
├── config/           # Configuration files
├── data/             # SQLite database
├── src/
│   ├── api/          # REST API routes
│   ├── alerts/       # Alert manager & channels
│   ├── database/     # Database layer
│   ├── exporters/    # Prometheus exporter
│   ├── monitors/     # Health, performance, logs
│   ├── utils/        # Utilities
│   └── server.js     # Main server
└── package.json
```

### Adding New Monitors

1. Create monitor in `src/monitors/`
2. Initialize in `server.js`
3. Add routes in `src/api/routes.js`
4. Update WebSocket broadcasts if needed

### Adding Alert Channels

1. Create channel in `src/alerts/channels/`
2. Register in `alert-manager.js`
3. Add config to `config/alerts.json`

## Troubleshooting

**Port 8080 already in use:**
```bash
# Change port in .env
PORT=8081
```

**Database locked:**
```bash
# Delete and reinitialize
rm data/diagnostic.db
npm run init-db
```

**WebSocket not connecting:**
- Check firewall settings
- Verify service is running
- Check browser console for errors

## License

Same as main project

