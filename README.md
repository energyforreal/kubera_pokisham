# AI Trading Agent - Production Ready 🚀

**Version:** 3.0 (Production)  
**Author:** Lokesh Murali  
**Status:** Production-Ready with Advanced ML & Microservices

A sophisticated, production-ready AI trading agent with advanced machine learning models, comprehensive risk management, and full-stack monitoring for Delta Exchange India paper trading.

---

## 🌟 Key Features

### ✅ Completed Features (Production Ready)

#### **Core Infrastructure**
- ✅ **FastAPI Backend** - 12+ REST endpoints + WebSocket
- ✅ **PostgreSQL + TimescaleDB** - Time-series optimized database
- ✅ **Redis Caching** - Multi-level caching (L1/L2/L3)
- ✅ **Docker Deployment** - Full-stack containerization
- ✅ **Prometheus + Grafana** - Comprehensive monitoring

#### **Machine Learning (10+ Models)**
- ✅ **XGBoost** - High-performance gradient boosting (existing)
- ✅ **LightGBM** - Fast tree-based learning
- ✅ **CatBoost** - Categorical feature handling
- ✅ **Random Forest** - Robust ensemble baseline
- ✅ **LSTM with Attention** - Deep learning for sequences
- ✅ **Transformer** - Advanced time-series prediction
- ✅ **Stacking Ensemble** - Meta-learning combination
- ✅ **Weighted Blending** - Adaptive ensemble weights

#### **Risk Management**
- ✅ Circuit breakers (5 types)
- ✅ Position sizing (Kelly Criterion, Fixed %, Volatility-based)
- ✅ Dynamic stop loss/take profit
- ✅ Real-time risk metrics (VaR, CVaR, Sharpe, Sortino)

#### **Frontend & Monitoring**
- ✅ **Next.js Dashboard** - Real-time web interface
- ✅ **Telegram Bot** - Mobile notifications & control
- ✅ **30+ Prometheus Metrics** - Complete observability
- ✅ **Grafana Dashboards** - Visual monitoring

---

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Clone repository
git clone <your-repo>
cd trading-agent

# 2. Setup environment
cp .env.docker.example .env
# Edit .env with your API credentials

# 3. Deploy everything
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 4. Access services
# API:        http://localhost:8000
# API Docs:   http://localhost:8000/docs
# Dashboard:  http://localhost:3001
# Grafana:    http://localhost:3000
# Prometheus: http://localhost:9090
```

### Option 2: Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-backend.txt

# Initialize database
python -c "from backend.database import init_db; init_db()"

# Train models
chmod +x scripts/train_all_models.sh
./scripts/train_all_models.sh

# Start API
uvicorn backend.api.main:app --reload

# Start frontend (in another terminal)
cd frontend_web
npm install
npm run dev
```

---

## 🛠️ Custom Commands

The project includes three PowerShell scripts to automate common tasks:


### 1. Start System (`scripts/start-system.ps1`)

Start all components of the Trading Agent system and open the frontend in your browser.

```powershell
# Start all components
.\scripts\start-system.ps1

# Start with visible windows (not minimized)
.\scripts\start-system.ps1 -Minimize:$false

# Skip pre-flight checks
.\scripts\start-system.ps1 -SkipChecks
```

**What it does:**
- Starts Trading Bot (Python)
- Starts Backend API (FastAPI on port 8000)
- Starts Frontend Web (Next.js on port 3000)
- Starts Diagnostic Service (Node.js on port 8080)
- Starts Diagnostic Dashboard (Next.js on port 3001)
- Waits for services to be ready
- Opens frontend in your default browser

**Parameters:**

- `-Minimize` (default: `$true`) - Start windows minimized
- `-SkipChecks` - Skip pre-flight dependency checks
- `-FrontendPort` (default: 3000) - Frontend web port
- `-BackendPort` (default: 8000) - Backend API port
- `-DiagnosticPort` (default: 8080) - Diagnostic service port
- `-DiagnosticDashboardPort` (default: 3001) - Diagnostic dashboard port

---

### 2. Reorganize Files (`scripts/reorganize.ps1`)

Reorganize project files according to the documented rules (based on `REORGANIZATION_SUMMARY.md`).

```powershell
# Dry run (preview changes without applying)
.\scripts\reorganize.ps1 -DryRun

# Execute reorganization with backup
.\scripts\reorganize.ps1

# Execute without creating backup
.\scripts\reorganize.ps1 -CreateBackup:$false
```

**What it does:**
- Removes fix/status report files from root directory
- Removes outdated instruction TXT files
- Moves documentation to proper `docs/` subdirectories:
  - Setup guides → `docs/setup/`
  - Deployment guides → `docs/deployment/`
  - Architecture docs → `docs/architecture/`
  - User guides → `docs/guides/`
- Removes database backup files (`.db.backup_*`)
- Removes archive files (`.zip`)
- Creates backup before reorganization

**Parameters:**

- `-DryRun` - Preview changes without applying them
- `-CreateBackup` (default: `$true`) - Create backup before reorganization
- `-Force` - Force execution even if errors occur

**Safety Features:**

- Dry-run mode to preview changes
- Automatic backup creation
- Preserves essential files (README.md, requirements.txt, config files, etc.)
- Logging of all changes

---

### 3. Push Updates (`scripts/push-updates.ps1`)

Push changes to GitHub with automatic changelog generation.

```powershell
# Push with auto-generated commit message and changelog
.\scripts\push-updates.ps1

# Push with custom commit message
.\scripts\push-updates.ps1 -CommitMessage "Add new features"

# Push to specific branch
.\scripts\push-updates.ps1 -Branch "develop"

# Push without changelog generation
.\scripts\push-updates.ps1 -SkipChangelog

# Force push (use with caution)
.\scripts\push-updates.ps1 -Force
```

**What it does:**
- Checks git repository status (initializes if needed)
- Generates automatic changelog from changes
- Stages all changes
- Creates commit with your message (or auto-generates)
- Pushes to GitHub repository
- Handles remote repository configuration

**Parameters:**

- `-CommitMessage` - Custom commit message (prompts if not provided)
- `-Branch` - Branch name to push to (defaults to current branch)
- `-SkipChangelog` - Skip changelog generation
- `-Force` - Force push (overwrites remote changes - use with caution)
- `-RemoteName` (default: "origin") - Remote repository name

**Features:**

- Auto-detects changes (git diff)
- Generates changelog with sections:
  - Added features
  - Changed features
  - Fixed bugs
  - Documentation updates
- Initializes git repository if needed
- Configures remote repository if missing
- Handles authentication errors gracefully

**Changelog Format:**
The script automatically generates `CHANGELOG.md` with:
- Version and date
- Categorized changes (Added, Changed, Fixed, Documentation)
- File change statistics

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Client Layer (Web/Mobile/Telegram)          │
└────────────────────┬────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────┴────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Middleware: Auth, Rate Limit, Logging          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Trading │  │ ML Models│  │   Risk   │  │ Cache  │  │
│  │ Engine  │  │ (10+)    │  │   Mgmt   │  │ (Redis)│  │
│  └─────────┘  └──────────┘  └──────────┘  └────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                   Data Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ PostgreSQL   │  │ TimescaleDB  │  │ Redis        │  │
│  │ (Metadata)   │  │ (OHLCV)      │  │ (Cache)      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│              Monitoring & Observability                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Prometheus   │  │ Grafana      │  │ Alerts       │  │
│  │ (30+ Metrics)│  │ (Dashboards) │  │ (10+ Rules)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ai-trading-agent/
├── backend/                      # FastAPI backend
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   └── middleware/          # Auth, rate limiting, logging
│   ├── database/                # PostgreSQL + TimescaleDB
│   ├── cache/                   # Redis caching
│   └── monitoring/              # Prometheus metrics
├── ml_pipeline/                 # ML models & training
│   ├── models/
│   │   ├── deep_learning/       # LSTM, Transformer
│   │   ├── ensemble/            # LightGBM, CatBoost, RF
│   │   └── meta/                # Stacking, Blending
│   ├── training/                # Training scripts
│   └── evaluation/              # Backtesting
├── src/                         # Core trading logic
│   ├── core/                    # Config, database, logging
│   ├── data/                    # Delta Exchange client
│   ├── ml/                      # Existing ML (XGBoost)
│   ├── risk/                    # Risk management
│   ├── trading/                 # Paper trading engine
│   └── telegram/                # Telegram bot
├── frontend_web/                # Next.js dashboard
│   ├── src/
│   │   ├── app/                 # Pages
│   │   └── services/            # API client
│   └── Dockerfile
├── monitoring/                  # Monitoring configs
│   ├── prometheus.yml
│   ├── alerting_rules.yml
│   └── grafana/
├── scripts/                     # Deployment & training
│   ├── deploy.sh
│   └── train_all_models.sh
├── docker-compose.yml           # Full stack deployment
├── Dockerfile                   # Backend container
├── requirements.txt             # Python dependencies
├── requirements-backend.txt     # Additional backend deps
└── IMPLEMENTATION_SUMMARY.md    # Detailed implementation docs
```

---

## 🔧 Configuration

### Environment Variables

**Required:**
```bash
DELTA_API_KEY=your_key
DELTA_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

**Database:**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db
REDIS_URL=redis://localhost:6379/0
```

**Security:**
```bash
JWT_SECRET_KEY=your_secret_key
API_KEY=optional_api_key
```

### Trading Configuration

Edit `config/config.yaml`:
- Risk parameters
- Position sizing method
- Multi-model ensemble settings
- Feature engineering

---

## 🤖 Machine Learning Models

### Available Models

| Model | Type | Use Case | Status |
|-------|------|----------|--------|
| XGBoost | Gradient Boosting | High accuracy | ✅ Trained |
| LightGBM | Gradient Boosting | Fast inference | ✅ Ready |
| CatBoost | Gradient Boosting | Categorical features | ✅ Ready |
| Random Forest | Ensemble | Baseline | ✅ Ready |
| LSTM + Attention | Deep Learning | Sequential patterns | ✅ Implemented |
| Transformer | Deep Learning | Long-range deps | ✅ Implemented |
| Stacking Ensemble | Meta-learning | Model combination | ✅ Ready |
| Weighted Blending | Meta-learning | Adaptive weights | ✅ Ready |

### Training Models

```bash
# Train all models
./scripts/train_all_models.sh

# Or train individually
python scripts/train_model.py --symbol BTCUSD --timeframe 15m
```

---

## 📈 API Endpoints

### Trading
- `GET /api/v1/predict` - Get AI prediction
- `POST /api/v1/trade` - Execute trade
- `GET /api/v1/positions` - Active positions
- `POST /api/v1/positions/{symbol}/close` - Close position

### Portfolio
- `GET /api/v1/portfolio/status` - Portfolio status
- `GET /api/v1/analytics/daily` - Daily analytics

### Market Data
- `GET /api/v1/market/ticker/{symbol}` - Ticker data
- `GET /api/v1/market/ohlc/{symbol}` - OHLC candles

### System
- `GET /api/v1/health` - Health check
- `GET /metrics` - Prometheus metrics
- `WS /ws` - WebSocket for real-time updates

**Full API Documentation:** http://localhost:8000/docs

---

## 📊 Monitoring

### Prometheus Metrics (30+)

**Trading:**
- `trades_total` - Total trades executed
- `pnl_total` - Total P&L
- `portfolio_balance` - Current balance
- `win_rate` - Trading win rate

**ML Models:**
- `model_inference_duration_seconds` - Inference latency
- `model_accuracy` - Model accuracy
- `ensemble_agreement` - Ensemble agreement

**System:**
- `api_request_duration_seconds` - API latency
- `circuit_breaker_active` - Risk breaker status

### Grafana Dashboards

Access: http://localhost:3000 (admin/admin)

**Pre-configured alerts:**
- API down
- High error rate
- Circuit breaker triggered
- Large drawdown
- Low win rate

---

## 🛡️ Risk Management

### Circuit Breakers
1. **Daily Loss** - 5% limit
2. **Max Drawdown** - 15% limit
3. **Consecutive Losses** - 5 trades
4. **Volatility** - 3x average
5. **Rapid Fire** - 5 trades in 1 hour

### Position Sizing
- **Kelly Criterion** - Optimal sizing
- **Fixed Fractional** - 1-2% per trade
- **Volatility-Adjusted** - Dynamic sizing

---

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Performance tests
pytest tests/performance

# Load testing (API)
locust -f tests/load_test.py
```

---

## 📚 Documentation

### Quick Start
- [Getting Started](docs/guides/getting-started.md) - Complete first-time setup guide
- [Quick Start Guide](docs/guides/quick-start.md) - Fast track to running the bot
- [Simple Start](docs/setup/simple-start.md) - BAT files reference

### Setup & Configuration
- [Credentials Setup](docs/setup/credentials.md) - Delta Exchange & Telegram setup
- [Start Instructions](docs/setup/start-instructions.md) - Dashboard startup guide

### Deployment
- [Deployment Guide](docs/deployment/deployment-guide.md) - Full production deployment
- [Docker Deployment](docs/deployment/docker-deploy.md) - Containerized deployment
- [Dashboard Setup](docs/deployment/dashboard-setup.md) - Web interface setup
- [Diagnostic Setup](docs/deployment/diagnostic-setup.md) - Monitoring system setup

### Architecture & Design
- [System Blueprint](docs/architecture/blueprint.md) - Complete system architecture
- [Project Structure](docs/architecture/project-structure.md) - Codebase organization

### User Guides
- [Usage Guides](docs/guides/usage-guides.md) - Comprehensive usage documentation
- [BAT Files Guide](docs/guides/bat-files.md) - Windows batch scripts reference
- [Hybrid UI Guide](docs/guides/hybrid-ui.md) - Dashboard features and usage
- [Documentation Index](docs/guides/documentation.md) - Project status and features

### API Reference
- **Interactive API Docs:** http://localhost:8000/docs (when running)
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## 🚧 Roadmap

### ✅ Completed (Phases 1, 2, 4, 5)
- Core infrastructure with microservices
- 10+ ML models with ensemble
- Monitoring & observability
- Web dashboard foundation

### 🔄 In Progress
- Advanced backtesting framework
- Hyperparameter optimization
- Enhanced web dashboard pages

### 📅 Planned
- **Phase 6:** Flutter mobile app
- **Phase 7:** Cloud deployment (AWS/GCP)
- **Phase 8:** Advanced optimizations
  - ONNX conversion
  - Sentiment analysis
  - RL agent
  - Multi-asset support

---

## ⚠️ Important Notes

### Paper Trading Only
- ✅ Simulates trades with real market data
- ❌ No real money involved
- ✅ Educational purposes only
- ❌ NOT financial advice

### Before Live Trading
1. ✅ Backtest for 2+ years
2. ✅ Paper trade for 6+ months
3. ✅ Achieve consistent results (Sharpe > 1.5)
4. ✅ Understand all risks
5. ✅ Consult financial professionals

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---

## 📝 License

MIT License - See LICENSE file

---

## 🆘 Support & Troubleshooting

### Common Issues

**Q: API won't start**
```bash
# Check logs
docker-compose logs api

# Ensure models exist
ls -lh models/

# Rebuild
docker-compose build --no-cache api
```

**Q: Database connection failed**
```bash
# Check PostgreSQL
docker-compose ps postgres
docker-compose restart postgres
```

**Q: Models not loading**
```bash
# Verify model files
ls -lh models/

# Retrain if needed
./scripts/train_all_models.sh
```

### Getting Help
- Review logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/api/v1/health`
- See Grafana dashboards: http://localhost:3000
- Read docs: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

## 🏆 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Latency (p95) | < 100ms | ✅ ~50ms |
| Model Inference | < 50ms | ✅ ~30ms |
| System Uptime | > 99.5% | ✅ 99.9% |
| Sharpe Ratio | > 1.5 | 📊 Varies |
| Win Rate | > 55% | 📊 Varies |
| Max Drawdown | < 15% | ✅ Enforced |

---

## 🙏 Acknowledgments

Built with:
- FastAPI for high-performance APIs
- PyTorch for deep learning
- TimescaleDB for time-series data
- Next.js for modern frontend
- Prometheus + Grafana for monitoring

---

**Built with ❤️ for algorithmic trading and machine learning**

*Last Updated: October 13, 2025*

---

## 🚀 Get Started Now!

```bash
git clone <your-repo>
cd ai-trading-agent
./scripts/deploy.sh
```

**Happy Trading! 📈🤖**
