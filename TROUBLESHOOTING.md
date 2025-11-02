# KUBERA POKISHAM - Troubleshooting Guide

## Overview
This guide helps you resolve common errors when running the Kubera Pokisham Enhanced.bat launcher and trading system.

## Quick Diagnostics

### Run System Check
```bash
# Check all components
python scripts/check_ports.py
python scripts/validate_config.py
python scripts/detect_models.py
python scripts/install_dependencies.py
python scripts/check_integrations.py --skip-deps
```

## Common Errors & Solutions

### 1. Python/Node.js Detection Issues

**Error**: `❌ Python not found!` or `❌ Node.js not found!`

**Causes**:
- Python/Node.js not installed
- Not added to PATH environment variable
- Multiple versions installed causing conflicts

**Solutions**:
1. **Install Python 3.10+**:
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
   - Verify: `python --version`

2. **Install Node.js 18+**:
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version`

3. **Fix PATH issues**:
   ```cmd
   # Add to PATH manually
   setx PATH "%PATH%;C:\Python310;C:\Python310\Scripts"
   setx PATH "%PATH%;C:\Program Files\nodejs"
   ```

4. **Multiple versions**:
   ```cmd
   # Use specific version
   py -3.10 --version
   py -3.11 --version
   ```

### 2. Dependency Installation Failures

**Error**: `❌ Failed to install Python dependencies`

**Causes**:
- Network connectivity issues
- Antivirus blocking pip
- Permission errors
- Corrupted pip cache

**Solutions**:
1. **Run dependency installer**:
   ```bash
   python scripts/install_dependencies.py
   ```

2. **Manual installation**:
   ```bash
   pip install --upgrade pip
   pip install pandas numpy scikit-learn xgboost lightgbm fastapi uvicorn aiohttp websockets pyyaml sqlalchemy requests
   ```

3. **Fix permission issues**:
   ```bash
   # Run as administrator
   pip install --user --upgrade pip
   pip install --user -r requirements.txt
   ```

4. **Clear pip cache**:
   ```bash
   pip cache purge
   pip install --no-cache-dir -r requirements.txt
   ```

5. **Use virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 3. Model File Not Found

**Error**: `❌ RandomForest model not found!` or similar

**Causes**:
- Model files missing from models/ directory
- Models retrained with new timestamps
- Incorrect file paths in config

**Solutions**:
1. **Check available models**:
   ```bash
   python scripts/detect_models.py
   ```

2. **Train new models**:
   ```bash
   python scripts/train_models.py
   ```

3. **Download pre-trained models**:
   - Check if models exist in `models/` directory
   - Ensure filenames match expected patterns

4. **Update config.yaml**:
   ```yaml
   model:
     path: "models/your_model_file.pkl"
   ```

### 4. Port Conflicts

**Error**: `❌ Port 8000 is already in use` or similar

**Causes**:
- Previous services still running
- Other applications using same ports
- Services crashed without cleanup

**Solutions**:
1. **Check port usage**:
   ```bash
   python scripts/check_ports.py
   ```

2. **Stop KUBERA services**:
   ```cmd
   taskkill /F /FI "WINDOWTITLE eq KUBERA*"
   taskkill /F /IM python.exe
   taskkill /F /IM node.exe
   ```

3. **Find process using port**:
   ```cmd
   netstat -ano | findstr :8000
   tasklist /FI "PID eq <PID_NUMBER>"
   ```

4. **Change ports in config**:
   ```yaml
   # Update backend/api/main.py
   uvicorn.run(app, host="0.0.0.0", port=8001)  # Change port
   ```

### 5. Configuration File Errors

**Error**: `❌ Configuration file not found!` or YAML syntax errors

**Causes**:
- config.yaml missing or corrupted
- Invalid YAML syntax
- Missing required fields

**Solutions**:
1. **Validate configuration**:
   ```bash
   python scripts/validate_config.py
   ```

2. **Check YAML syntax**:
   - Use spaces, not tabs for indentation
   - Ensure proper nesting
   - Check for missing quotes

3. **Restore from backup**:
   ```bash
   copy config\env.example config\config.yaml
   ```

4. **Required fields**:
   ```yaml
   trading:
     symbol: "BTCUSD"
     initial_balance: 10000.0
     mode: "paper"
   model:
     path: "models/your_model.pkl"
   risk_management:
     max_daily_loss_percent: 5
   ```

### 6. Database Lock Issues

**Error**: `database is locked` or SQLite errors

**Causes**:
- Multiple processes accessing same database
- Database file corruption
- Incomplete transactions

**Solutions**:
1. **Stop all services**:
   ```cmd
   taskkill /F /IM python.exe
   ```

2. **Check database file**:
   ```bash
   # Verify database exists and is accessible
   python -c "import sqlite3; conn = sqlite3.connect('kubera_pokisham.db'); print('OK')"
   ```

3. **Backup and recreate**:
   ```cmd
   copy kubera_pokisham.db kubera_pokisham.db.backup
   del kubera_pokisham.db
   ```

4. **Use connection pooling**:
   - Add to config: `database: {pool_size: 5}`

### 7. Service Startup Failures

**Error**: Services fail to start or timeout

**Causes**:
- Insufficient system resources
- Antivirus interference
- Firewall blocking ports
- Slow system performance

**Solutions**:
1. **Use health check polling**:
   ```bash
   python scripts/check_service_health.py --wait
   ```

2. **Check system resources**:
   - Ensure sufficient RAM (4GB+ recommended)
   - Close unnecessary applications
   - Check CPU usage

3. **Antivirus exceptions**:
   - Add project folder to antivirus exclusions
   - Allow Python and Node.js through firewall

4. **Increase timeouts**:
   - Modify batch file timeout values
   - Use `--wait` flag for health checks

### 8. Integration Check Failures

**Error**: `❌ Some integrations failed`

**Causes**:
- Services not running when checks run
- Network connectivity issues
- WebSocket compatibility problems

**Solutions**:
1. **Run pre-startup checks**:
   ```bash
   python scripts/check_integrations.py --skip-deps
   ```

2. **Run post-startup checks**:
   ```bash
   python scripts/check_integrations.py
   ```

3. **Check individual services**:
   ```bash
   python scripts/check_service_health.py --service backend_api
   ```

4. **WebSocket issues**:
   - Update websockets library: `pip install --upgrade websockets`
   - Check Windows asyncio compatibility

### 9. Graceful Shutdown Issues

**Error**: Services don't stop properly or data loss

**Causes**:
- Force kill without graceful shutdown
- Database transactions not committed
- WebSocket connections not closed

**Solutions**:
1. **Use Ctrl+C**:
   - Press Ctrl+C in service windows
   - Wait for graceful shutdown messages

2. **Stop services properly**:
   ```cmd
   # Send SIGTERM first, then force if needed
   taskkill /IM python.exe
   timeout /t 10
   taskkill /F /IM python.exe
   ```

3. **Check for hanging processes**:
   ```cmd
   tasklist | findstr python
   tasklist | findstr node
   ```

### 10. Environment Variable Conflicts

**Error**: Import errors or module not found

**Causes**:
- PYTHONPATH conflicts
- Virtual environment issues
- Multiple Python installations

**Solutions**:
1. **Clear PYTHONPATH**:
   ```cmd
   set PYTHONPATH=
   ```

2. **Use virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Check Python installation**:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

## Advanced Troubleshooting

### Enable Verbose Logging
```bash
# Run with debug output
python src/main.py --verbose
python backend/api/main.py --log-level debug
```

### Check System Logs
```bash
# View recent logs
type logs\kubera_pokisham.log
type logs\activity_log.json
```

### Network Diagnostics
```bash
# Test connectivity
ping google.com
telnet localhost 8000
curl http://localhost:8000/api/v1/health
```

### Performance Monitoring
```bash
# Check resource usage
tasklist /FI "IMAGENAME eq python.exe"
tasklist /FI "IMAGENAME eq node.exe"
```

## Recovery Procedures

### Complete System Reset
1. Stop all services
2. Clear logs: `del logs\*.log`
3. Backup database: `copy kubera_pokisham.db kubera_pokisham.db.backup`
4. Reinstall dependencies: `python scripts/install_dependencies.py`
5. Validate configuration: `python scripts/validate_config.py`
6. Restart services

### Partial Recovery
1. Stop problematic service only
2. Check logs for specific errors
3. Fix configuration issues
4. Restart individual service

### Emergency Stop
```cmd
# Force stop all KUBERA processes
taskkill /F /FI "WINDOWTITLE eq KUBERA*"
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

## Getting Help

### Log Files to Check
- `logs/kubera_pokisham.log` - Main trading bot logs
- `logs/activity_log.json` - Activity tracking
- `integration_health_results.json` - Integration check results
- `bot_health.json` - Bot health status

### Diagnostic Commands
```bash
# Full system check
python scripts/check_ports.py && python scripts/validate_config.py && python scripts/detect_models.py

# Service health check
python scripts/check_service_health.py --all

# Integration validation
python scripts/check_integrations.py --skip-deps
```

### Common File Locations
- Configuration: `config/config.yaml`
- Models: `models/*.pkl`
- Database: `kubera_pokisham.db`
- Logs: `logs/`
- Scripts: `scripts/`

## Prevention Tips

1. **Regular Maintenance**:
   - Run health checks weekly
   - Monitor log files for errors
   - Keep dependencies updated

2. **Backup Strategy**:
   - Backup database regularly
   - Keep config.yaml backups
   - Document custom configurations

3. **System Requirements**:
   - Windows 10/11
   - Python 3.10+
   - Node.js 18+
   - 4GB+ RAM
   - Stable internet connection

4. **Best Practices**:
   - Use virtual environments
   - Run as administrator when needed
   - Keep antivirus exclusions updated
   - Monitor system resources

---

**Last Updated**: January 2025  
**Version**: Enhanced Edition  
**For additional support**: Check the project documentation or create an issue in the repository.
