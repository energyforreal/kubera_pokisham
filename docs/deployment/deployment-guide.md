

# AI Trading Agent - Production Deployment Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Model Training](#model-training)
6. [Docker Deployment](#docker-deployment)
7. [Manual Deployment](#manual-deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker** (v20.10+) and **Docker Compose** (v2.0+)
- **Python** 3.10+ (for local development)
- **PostgreSQL** 15+ with TimescaleDB (if not using Docker)
- **Redis** 7+ (if not using Docker)

### API Credentials
- Delta Exchange API key and secret
- Telegram bot token and chat ID

---

## Quick Start

### 1. Automated Deployment (Docker - Recommended)

```bash
# Clone repository
git clone <your-repo>
cd trading-agent

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Script will:
# - Check prerequisites
# - Setup environment
# - Build Docker images
# - Start all services
# - Verify health
```

### 2. Access Services

Once deployed:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## Environment Setup

### 1. Create Environment File

```bash
cp .env.docker.example .env
```

### 2. Configure Required Variables

Edit `.env`:

```bash
# Delta Exchange
DELTA_API_KEY=your_api_key_here
DELTA_API_SECRET=your_api_secret_here

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Database (auto-configured for Docker)
POSTGRES_PASSWORD=change_this_password

# Redis
REDIS_PASSWORD=change_this_redis_password

# Security
JWT_SECRET_KEY=generate_a_secure_random_key_here
```

---

## Database Setup

### Option 1: Docker (Automatic)

Database is automatically initialized when using Docker Compose.

### Option 2: Manual PostgreSQL Setup

```bash
# Install PostgreSQL + TimescaleDB
# Ubuntu/Debian:
sudo apt-get install postgresql-15 postgresql-15-timescaledb

# Create database
sudo -u postgres psql
CREATE DATABASE trading_db;
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

# Enable TimescaleDB
\c trading_db
CREATE EXTENSION timescaledb;

# Initialize tables
python -c "from backend.database import init_db; init_db()"
```

---

## Model Training

### Option 1: Train All Models

```bash
# Automated training script
chmod +x scripts/train_all_models.sh
./scripts/train_all_models.sh
```

This will train:
- XGBoost (15m, 1h)
- LightGBM
- CatBoost
- Random Forest

### Option 2: Manual Training

```bash
# Download data
python scripts/download_data.py --symbol BTCUSD --days 365

# Train specific model
python scripts/train_model.py --symbol BTCUSD --timeframe 15m
```

### Option 3: Use Pre-trained Models

If you have pre-trained models, place them in `models/` directory:
```
models/
├── xgboost_BTCUSD_15m.pkl
├── xgboost_BTCUSD_1h.pkl
├── lightgbm_BTCUSD_15m.txt
├── catboost_BTCUSD_15m.cbm
└── random_forest_BTCUSD_15m.pkl
```

---

## Docker Deployment

### Full Stack Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Stop services
docker-compose down

# Restart specific service
docker-compose restart api
```

### Individual Service Management

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Rebuild after code changes
docker-compose build api
docker-compose up -d api

# Access container shell
docker-compose exec api bash
```

### Data Persistence

Data is persisted in Docker volumes:
- `postgres_data` - Database
- `redis_data` - Cache
- `prometheus_data` - Metrics
- `grafana_data` - Dashboards

To backup:
```bash
docker-compose exec postgres pg_dump -U trading_user trading_db > backup.sql
```

---

## Manual Deployment

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
pip install -r requirements-backend.txt
```

### 2. Configure Environment

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/trading_db"
export REDIS_URL="redis://localhost:6379/0"
export DELTA_API_KEY="your_key"
export DELTA_API_SECRET="your_secret"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Initialize Database

```bash
python -c "from backend.database import init_db; init_db()"
```

### 4. Start Services

```bash
# Terminal 1: API Server
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Telegram Bot (optional)
python src/telegram/bot.py

# Terminal 3: Prometheus (if not using Docker)
prometheus --config.file=monitoring/prometheus.yml
```

---

## Monitoring

### Prometheus Metrics

Access: http://localhost:9090

**Key Metrics:**
```
# Trading
trades_total
pnl_total
portfolio_balance
win_rate

# Models
model_inference_duration_seconds
model_accuracy
ensemble_agreement

# API
api_requests_total
api_request_duration_seconds

# Risk
circuit_breaker_active
var_95
sharpe_ratio
```

### Grafana Dashboards

Access: http://localhost:3000

**Default Credentials:** admin/admin

**Dashboards to Create:**
1. Trading Overview
2. Model Performance
3. Risk Monitoring
4. System Health

Import dashboard templates from `monitoring/grafana/dashboards/`

### Alerting

Configure alerts in `monitoring/alerting_rules.yml`

**Pre-configured Alerts:**
- API down
- High error rate
- Circuit breaker triggered
- Large drawdown
- High latency
- Low win rate

---

## Troubleshooting

### Common Issues

#### 1. API Won't Start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing models: Ensure models/ directory has trained models
# - Database connection: Check DATABASE_URL
# - Redis connection: Check REDIS_URL

# Solution: Rebuild and restart
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL
docker-compose ps postgres
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U trading_user -d trading_db -c "SELECT 1;"

# Restart database
docker-compose restart postgres
```

#### 3. Redis Connection Failed

```bash
# Check Redis
docker-compose ps redis
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

#### 4. Model Loading Errors

```bash
# Verify models exist
ls -lh models/

# Check model paths in config/config.yaml
cat config/config.yaml | grep -A 5 "multi_model"

# Retrain if needed
python scripts/train_model.py --symbol BTCUSD --timeframe 15m
```

#### 5. High Memory Usage

```bash
# Check container stats
docker stats

# Reduce memory usage:
# 1. Limit Docker memory in docker-compose.yml
# 2. Reduce batch size in training
# 3. Use ONNX models (smaller, faster)
# 4. Clear cache: docker system prune
```

### Performance Optimization

#### 1. Enable ONNX Models

```python
# Convert PyTorch to ONNX
from ml_pipeline.deployment.model_server import convert_to_onnx

convert_to_onnx(
    model_path='models/lstm_attention.pth',
    output_path='models/lstm_attention.onnx',
    input_shape=(1, 60, 50)
)
```

#### 2. Optimize Database Queries

```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_trades_timestamp 
ON trades(timestamp DESC);

-- Analyze tables
ANALYZE trades;
ANALYZE ohlcv_data;
```

#### 3. Cache Tuning

Edit `backend/cache/redis_cache.py`:
```python
# Adjust TTL values
TTL_LIVE_PRICE = 5      # Increase for less frequent updates
TTL_FEATURES = 60       # Increase for longer cache
TTL_PREDICTIONS = 300   # Adjust based on signal frequency
```

---

## Production Checklist

### Before Going Live

- [ ] Environment variables configured
- [ ] Database initialized and backed up
- [ ] All models trained and validated
- [ ] Backtesting completed (6+ months)
- [ ] Paper trading tested (3+ months)
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Security review completed
- [ ] SSL/TLS certificates installed
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented

### Security

1. **Change Default Passwords**
   - Grafana admin password
   - PostgreSQL password
   - Redis password

2. **Enable Authentication**
   - Set JWT_SECRET_KEY
   - Enable API key authentication
   - Use HTTPS in production

3. **Network Security**
   - Configure firewall rules
   - Use VPN for remote access
   - Enable rate limiting

4. **Data Security**
   - Encrypt sensitive data
   - Regular database backups
   - Secure API credentials

---

## Maintenance

### Regular Tasks

**Daily:**
- Check system health
- Review trading performance
- Monitor error logs

**Weekly:**
- Analyze model performance
- Review risk metrics
- Update models if needed

**Monthly:**
- Full system backup
- Security updates
- Performance optimization

### Backup & Recovery

```bash
# Backup everything
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backup_2025_10_13.tar.gz
```

---

## Support

### Logs

```bash
# API logs
docker-compose logs -f api

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Debug Mode

Edit `docker-compose.yml`:
```yaml
api:
  environment:
    - DEBUG=true
    - LOG_LEVEL=DEBUG
```

---

## Next Steps

1. **Phase 3**: Implement advanced backtesting
2. **Phase 5**: Build web dashboard
3. **Phase 6**: Develop mobile app
4. **Phase 7**: Cloud deployment
5. **Phase 8**: Advanced optimizations

---

**Happy Trading! 🚀📈**

*Last Updated: October 13, 2025*


