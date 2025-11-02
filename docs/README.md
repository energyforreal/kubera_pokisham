# 📖 AI Trading Agent - Documentation Index

Welcome to the comprehensive documentation for the Kubera Pokisham AI Trading Agent. This index will help you find the information you need quickly.

---

## 🚀 Getting Started

**New to the project?** Start here:

1. **[Getting Started Guide](guides/getting-started.md)** ⭐
   - Complete first-time setup
   - Installation and configuration
   - Quick start options
   - Troubleshooting

2. **[Quick Start Guide](guides/quick-start.md)**
   - Fast track to running the bot
   - Available commands
   - Access points

3. **[Credentials Setup](setup/credentials.md)**
   - Delta Exchange API configuration
   - Telegram bot setup
   - Security best practices

---

## 📋 Setup & Configuration

### Initial Setup
- **[Credentials Setup](setup/credentials.md)** - Get API keys and configure environment
- **[Simple Start Guide](setup/simple-start.md)** - Which BAT files to use
- **[Start Instructions](setup/start-instructions.md)** - Dashboard startup steps

### Configuration Files
- `.env` - Environment variables and API credentials
- `config/config.yaml` - Trading parameters and risk settings
- `frontend_web/.env.local` - Frontend dashboard configuration

---

## 🚢 Deployment

### Deployment Options

1. **[Deployment Guide](deployment/deployment-guide.md)** - Full production deployment
   - Prerequisites
   - Environment setup
   - Database configuration
   - Model training
   - Monitoring setup

2. **[Docker Deployment](deployment/docker-deploy.md)** - Containerized deployment
   - Docker setup
   - docker-compose configuration
   - Service orchestration

3. **[Dashboard Setup](deployment/dashboard-setup.md)** - Web interface setup
   - Frontend installation
   - Backend API configuration
   - Real-time features
   - Interactive controls

4. **[Diagnostic Setup](deployment/diagnostic-setup.md)** - Monitoring system
   - Diagnostic service installation
   - Alert configuration
   - Health monitoring

---

## 🏗️ Architecture & Design

### System Architecture
- **[System Blueprint](architecture/blueprint.md)** - Complete technical architecture
  - Infrastructure design
  - ML pipeline
  - Risk management system
  - API architecture
  - Monitoring stack

- **[Project Structure](architecture/project-structure.md)** - Codebase organization
  - Directory layout
  - Module descriptions
  - File organization

### Key Components
1. **Trading Engine** (`src/trading/`) - Core trading logic
2. **ML Models** (`ml_pipeline/`) - Machine learning models
3. **Risk Management** (`src/risk/`) - Circuit breakers and position sizing
4. **Backend API** (`backend/api/`) - FastAPI REST API
5. **Frontend Dashboard** (`frontend_web/`) - Next.js web interface
6. **Telegram Bot** (`src/telegram/`) - Notifications and control

---

## 📖 User Guides

### Comprehensive Guides
- **[Usage Guides](guides/usage-guides.md)** - Complete usage documentation
  - Training models
  - Colab training
  - Production deployment
  - Live trading preparation

- **[Documentation Index](guides/documentation.md)** - Project status
  - Implementation status
  - What's working
  - What's planned
  - Recent accomplishments

- **[BAT Files Guide](guides/bat-files.md)** - Windows batch scripts
  - Available scripts
  - Usage instructions
  - Troubleshooting

- **[Hybrid UI Guide](guides/hybrid-ui.md)** - Dashboard features
  - Interface overview
  - Interactive features
  - Real-time updates

---

## 🔌 API Documentation

### REST API
- **Interactive Docs:** http://localhost:8000/docs (when running)
- **OpenAPI Spec:** http://localhost:8000/openapi.json
- **WebSocket:** ws://localhost:8000/ws

### Key Endpoints
- **Trading:** `/api/v1/predict`, `/api/v1/trade`
- **Portfolio:** `/api/v1/portfolio/status`
- **Positions:** `/api/v1/positions`
- **Market Data:** `/api/v1/market/ticker/{symbol}`
- **Health:** `/api/v1/health`
- **Metrics:** `/metrics` (Prometheus)

---

## 🎓 How-To Guides

### Common Tasks

#### Starting the System
```bash
# Bot only
start_bot.bat

# Full system (bot + dashboard)
start_all.bat

# Dashboard only
start_dashboard.bat
```

#### Checking Status
```bash
# System health
check_status.bat

# Telegram
/status
/positions
/balance
```

#### Training Models
```bash
# Train all models
./scripts/train_all_models.sh

# Train specific model
python scripts/train_model.py --model xgboost --symbol BTCUSD --timeframe 4h
```

#### Monitoring
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Logs:** `logs/kubera_pokisham.log`
- **Prometheus:** http://localhost:9090 (Docker only)
- **Grafana:** http://localhost:3000 (Docker only)

---

## 🛠️ Troubleshooting

### Common Issues

**Bot Won't Start**
- See [Getting Started - Troubleshooting](guides/getting-started.md#troubleshooting)
- Check `.env` file exists
- Verify API credentials
- Install dependencies

**Dashboard Issues**
- See [Dashboard Setup](deployment/dashboard-setup.md)
- Ensure backend is running
- Check CORS configuration
- Verify frontend dependencies

**Telegram Bot Not Responding**
- See [Credentials Setup](setup/credentials.md)
- Verify bot token
- Check chat ID
- Restart bot

**Import Errors**
- See [Simple Start Guide](setup/simple-start.md)
- Install requirements: `pip install -r requirements.txt`
- Check Python version (3.10+)

---

## 📚 Reference

### Configuration Reference

**Environment Variables** (`.env`):
- `DELTA_API_KEY` - Delta Exchange API key
- `DELTA_API_SECRET` - Delta Exchange API secret
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID
- `TRADING_MODE` - `paper` or `live` (use paper for testing)

**Trading Config** (`config/config.yaml`):
- Risk management settings
- Position sizing methods
- Circuit breaker thresholds
- Model weights and timeframes

### Directory Structure

```
Trading Agent/
├── backend/              # FastAPI backend API
├── config/               # Configuration files
├── docs/                 # Documentation (you are here)
│   ├── setup/           # Setup guides
│   ├── deployment/      # Deployment guides
│   ├── architecture/    # Architecture docs
│   └── guides/          # User guides
├── frontend_web/         # Next.js dashboard
├── logs/                 # Log files
├── ml_pipeline/          # ML models and training
├── models/               # Trained model files
├── src/                  # Core trading logic
└── scripts/              # Utility scripts
```

---

## 🔍 Finding What You Need

### By Task

| I want to... | See this guide |
|--------------|----------------|
| Set up for the first time | [Getting Started](guides/getting-started.md) |
| Configure API keys | [Credentials Setup](setup/credentials.md) |
| Start the trading bot | [Simple Start](setup/simple-start.md) |
| Deploy to production | [Deployment Guide](deployment/deployment-guide.md) |
| Use the web dashboard | [Dashboard Setup](deployment/dashboard-setup.md) |
| Train ML models | [Usage Guides](guides/usage-guides.md) |
| Understand the architecture | [System Blueprint](architecture/blueprint.md) |
| Troubleshoot issues | [Getting Started - Troubleshooting](guides/getting-started.md#troubleshooting) |

### By User Type

**First-Time User:**
1. [Getting Started](guides/getting-started.md)
2. [Credentials Setup](setup/credentials.md)
3. [Simple Start](setup/simple-start.md)

**Developer:**
1. [System Blueprint](architecture/blueprint.md)
2. [Project Structure](architecture/project-structure.md)
3. [Usage Guides](guides/usage-guides.md)

**Deployer:**
1. [Deployment Guide](deployment/deployment-guide.md)
2. [Docker Deployment](deployment/docker-deploy.md)
3. [Diagnostic Setup](deployment/diagnostic-setup.md)

---

## 📞 Getting Help

### Support Resources
- **Documentation:** You're reading it!
- **Logs:** Check `logs/kubera_pokisham.log`
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

### Debugging Steps
1. Check logs for error messages
2. Verify configuration files
3. Ensure all dependencies are installed
4. Test API endpoints
5. Review relevant documentation section

---

## 🔄 Documentation Updates

This documentation is actively maintained. Last major reorganization: October 22, 2025

**Recent Changes:**
- Reorganized documentation into categorized directories
- Created comprehensive getting-started guide
- Added this central index for easy navigation
- Updated all file references and links

---

## 📝 Contributing to Docs

If you find errors or want to improve the documentation:
1. Note the issue or improvement
2. Check if it's already documented
3. Suggest updates or corrections
4. Keep documentation clear and concise

---

**Navigation:**
- **[↑ Back to Main README](../README.md)**
- **[→ Getting Started](guides/getting-started.md)**
- **[→ API Documentation](http://localhost:8000/docs)**

---

*Happy Trading! 📈🤖*

*Last Updated: October 22, 2025*  
*Documentation Version: 2.0*
