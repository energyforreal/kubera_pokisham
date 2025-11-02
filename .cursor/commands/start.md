# Start Complete System

## What Is This?

This is a **Cursor AI IDE command** that starts all components of the Trading Agent system and opens the frontend in your browser.

## How To Use in Cursor

**Method 1 - Command Palette:**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type `@start.md` and select it

**Method 2 - Composer:**
- Mention `@start.md` in your Cursor Composer chat

**Method 3 - Direct Execution:**
- From terminal: Run `.\scripts\start-system.ps1` (Windows) or manually start services (see below)

## Prerequisites

Before running this command, ensure you have:
- **Python 3.8+** installed (`python --version`)
- **Node.js 16+** and **npm** installed (`node --version`, `npm --version`)
- Required packages: `pip install -r requirements.txt`
- Frontend dependencies: `cd frontend_web && npm install`
- Diagnostic Service dependencies: `cd diagnostic_service && npm install`
- Diagnostic Dashboard dependencies: `cd diagnostic_dashboard && npm install`

## Platform Compatibility

| Platform | Method | Instructions |
|----------|--------|--------------|
| Windows | PowerShell | `.\scripts\start-system.ps1` |
| Linux/Mac | Manual | See "Alternative Execution" below |
| Docker | Docker Compose | Use `./scripts/deploy.sh` or `docker-compose up` |

## Direct Execution

```powershell
.\scripts\start-system.ps1
```

## Services Started

This command starts all components of the Trading Agent system:

| Service | Type | Port | Purpose | URL |
|---------|------|------|---------|-----|
| **Trading Bot** | Python | N/A | AI-powered paper trading engine | Process only |
| **Backend API** | FastAPI | 8000 | REST API for data & trading | http://localhost:8000 |
| **Frontend Web** | Next.js | 3000 | Main dashboard interface | http://localhost:3000 |
| **Diagnostic Service** | Node.js | 8080 | System health monitoring | http://localhost:8080 |
| **Diagnostic Dashboard** | Next.js | 3001 | Diagnostics visualization | http://localhost:3001 |

### What Happens After Starting

1. **Service Health Checks**: Script waits for each service to be ready
2. **Automatic Browser Launch**: Opens main frontend dashboard (http://localhost:3000)
3. **Background Services**: Trading bot and APIs run in background
4. **System Monitor**: Automatically starts to monitor health and auto-restart failed components (if enabled)
5. **Service Status**: Displays status for each started service

## Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `-Minimize:$false` | `$true` | Start windows visible (not minimized) |
| `-SkipChecks` | `$false` | Skip pre-flight dependency checks |
| `-EnableMonitoring:$false` | `$true` | Disable system monitoring |
| `-FrontendPort <port>` | `3000` | Custom frontend port |
| `-BackendPort <port>` | `8000` | Custom backend API port |
| `-DiagnosticPort <port>` | `8080` | Custom diagnostic service port |
| `-DiagnosticDashboardPort <port>` | `3001` | Custom diagnostic dashboard port |

## Usage Examples

```powershell
# Start with default settings (all services on default ports)
.\scripts\start-system.ps1

# Start with visible windows (useful for debugging)
.\scripts\start-system.ps1 -Minimize:$false

# Skip dependency checks and use custom ports
.\scripts\start-system.ps1 -SkipChecks -FrontendPort 3001 -BackendPort 8001

# Start without system monitoring
.\scripts\start-system.ps1 -EnableMonitoring:$false

# Start only essential services with custom ports
.\scripts\start-system.ps1 -BackendPort 8001 -FrontendPort 3001
```

## Alternative Execution (Linux/Mac/Docker)

### Manual Start (Linux/Mac)

Since `start-system.ps1` is Windows-only, manually start services:

**Terminal 1 - Backend API:**
```bash
uvicorn backend.api.main:app --reload --port 8000
```

**Terminal 2 - Trading Bot:**
```bash
python src/main.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend_web
npm run dev
```

**Terminal 4 - Diagnostic Service:**
```bash
cd diagnostic_service
npm start
```

**Terminal 5 - Diagnostic Dashboard:**
```bash
cd diagnostic_dashboard
npm run dev -- --port 3001
```

### Docker Compose

Start all services with Docker:
```bash
cd scripts
chmod +x deploy.sh
./deploy.sh
# OR
docker-compose up -d
```

Access services at the same URLs as above.

## How to Stop Services

### Windows (PowerShell)
```powershell
# Stop all services
.\stop_trading_bot.ps1

# Or manually close PowerShell windows
```

### Linux/Mac
```bash
# Find and kill processes
pkill -f "uvicorn backend.api.main"
pkill -f "python src/main.py"
pkill -f "npm run dev"
pkill -f "npm start"
```

### Docker
```bash
docker-compose down
```

## Troubleshooting

### Port Already in Use

**Error:** "Port 3000 already in use" or similar

**Solution:**
```powershell
# Check what's using the port (Windows)
netstat -ano | findstr :3000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different ports
.\scripts\start-system.ps1 -FrontendPort 3002
```

```bash
# Linux/Mac - check and kill
lsof -ti:3000 | xargs kill -9
```

### Service Failed to Start

**Error:** Service shows "Failed" status

**Check Logs:**
- Backend: Check `backend/logs/` directory
- Trading Bot: Check `logs/` directory
- Frontend: Check terminal output
- Diagnostic Service: Check `diagnostic_service/logs/` directory
- System Monitor: Check `logs/system_monitor_*.json` files (if monitoring enabled)

**Common Causes:**
1. **Missing dependencies**: Run `pip install -r requirements.txt` and `npm install`
2. **Configuration errors**: Check `.env` file and `config/config.yaml`
3. **Database not running**: Ensure PostgreSQL/TimescaleDB is running
4. **Port conflicts**: Stop conflicting services

### Browser Didn't Open

**Solution:** Manually navigate to http://localhost:3000

### Health Checks Timeout

**Error:** "Service did not become ready"

**Solution:**
1. Check service logs for errors
2. Verify all dependencies are installed
3. Ensure database is accessible
4. Try increasing timeout or skipping checks: `.\scripts\start-system.ps1 -SkipChecks`

### Permission Errors (Linux/Mac)

**Error:** "Permission denied"

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/deploy.sh
chmod +x start_trading_bot.ps1  # Convert to .sh or use manually

# Check file permissions
ls -la scripts/
```

### Python Not Found

**Error:** "Python not found" or "'python' is not recognized"

**Solution:**
```bash
# Check Python installation
python3 --version
python --version

# Install Python 3.8+ if missing
# Windows: python.org
# Mac: brew install python3
# Linux: sudo apt-get install python3.8
```

### Node.js Not Found

**Error:** "'npm' is not recognized"

**Solution:**
```bash
# Check Node.js installation
node --version
npm --version

# Install Node.js 16+ if missing
# Windows/Linux/Mac: nodejs.org
# Mac: brew install node
# Linux: sudo apt-get install nodejs npm
```

## Health Check Verification

After starting, verify all services:

```bash
# Backend API
curl http://localhost:8000/api/v1/health

# Diagnostic Service
curl http://localhost:8080/health

# Frontend (should return HTML)
curl http://localhost:3000
```

Expected responses:
- **Backend**: `{"status":"healthy",...}`
- **Diagnostic**: `{"status":"ok",...}`
- **Frontend**: HTML content (home page)

## Related Commands

- **`@error-check.md`** - Run error checks before starting
- **`@pushgit.md`** - Commit system improvements
- **`@filer.md`** - Reorganize files if needed

## References

- **Main Documentation**: [README.md](../../README.md)
- **Getting Started**: [docs/guides/getting-started.md](../../docs/guides/getting-started.md)
- **Dashboard Setup**: [docs/deployment/dashboard-setup.md](../../docs/deployment/dashboard-setup.md)
- **Deployment Guide**: [docs/deployment/deployment-guide.md](../../docs/deployment/deployment-guide.md)

