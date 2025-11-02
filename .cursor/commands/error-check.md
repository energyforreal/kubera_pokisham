# Error Check Command

## What Is This?

This is a **Cursor AI IDE command** that performs comprehensive system-wide error checking, validation, and automated fixing for the Trading Agent project.

## How To Use in Cursor

**Method 1 - Command Palette:**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type `@error-check.md` and select it

**Method 2 - Composer:**
- Mention `@error-check.md` in your Cursor Composer chat

**Method 3 - Direct Execution:**
- From terminal: Run `.\scripts\error-check.ps1` (Windows) or `python scripts/error-check.py` (any platform)

## Prerequisites

Before running this command, ensure you have:
- **Python 3.8+** installed (`python --version`)
- Required packages installed: `pip install -r requirements.txt`
- **Optional:** Backend API running for full integration tests (will skip if unavailable)

## Platform Compatibility

| Platform | Method | Script |
|----------|--------|--------|
| Windows | PowerShell | `scripts/error-check.ps1` |
| Linux/Mac | Python | `python scripts/error-check.py` |
| All | Manual | Follow instructions below |

## What This Command Does

This command performs a complete analysis of all project components and their integrations:

1. **Static Analysis**
   - Validates critical files exist (backend, frontend, config, models)
   - Checks configuration files (config.yaml, .env)
   - Analyzes API endpoint definitions
   - Verifies frontend-backend integration points

2. **Integration Testing**
   - Tests backend API connectivity
   - Verifies health endpoints
   - Tests critical API endpoints
   - Validates service integration

3. **Error Detection & Fixing**
   - Identifies missing files and configurations
   - Detects API connectivity issues
   - Finds integration mismatches
   - Applies automated fixes where safe

4. **Iterative Resolution**
   - Runs checks and fixes in iterations
   - Re-tests after each fix
   - Continues until all errors resolved or max iterations reached

### Execution Options

**Windows PowerShell:**
```powershell
.\scripts\error-check.ps1
.\scripts\error-check.ps1 -MaxIterations 10 -ApiUrl "http://localhost:8000" -Verbose
```

**Cross-Platform Python:**
```bash
python scripts/error-check.py
```

## What Gets Checked

### File Structure
- Backend API (`backend/api/main.py`)
- Trading Bot (`src/main.py`)
- Frontend (`frontend_web/`)
- Configuration files (`config/config.yaml`)
- Model files (`models/*.pkl`)
- Environment files (`.env`)

### Configuration
- YAML syntax validation
- Required configuration sections
- Model configurations
- Environment variable setup

### API Integration
- Backend API endpoints
- Frontend API client configuration
- WebSocket connections
- CORS configuration

### Service Connectivity
- Backend API health checks
- Trading bot registration
- Frontend-backend connection
- Diagnostic service endpoints

## Automated vs Manual Fixes

### Automatically Fixed (Safe Changes)

The system can automatically fix these issues without human intervention:
- **Missing `.env` file**: Creates from `config/env.example` template
- **Incorrect frontend API URLs**: Updates API endpoint URLs in frontend config
- **CORS configuration issues**: Adds missing CORS headers to backend config
- **Configuration file mismatches**: Syncs configuration values between files

> **Safety:** All automatic fixes create backups before modification. Files are never overwritten without a backup copy.

### Manual Fixes Required

These issues require manual intervention:
- **Missing Python packages**: Install via `pip install -r requirements.txt`
- **Missing model files**: Train models using `python scripts/train_model.py`
- **Database connection errors**: Check PostgreSQL/TimescaleDB setup
- **API authentication failures**: Verify API keys in `.env` file
- **Business logic errors**: Code-level issues in trading algorithms
- **Port conflicts**: Stop conflicting services or change ports
- **Missing Node.js dependencies**: Run `npm install` in respective directories

## Output

The command generates:
- Real-time progress updates in console
- Detailed error report (`error_check_results.json`)
- Summary of errors found and fixes applied
- Final status report

## Results File

Results are saved to `error_check_results.json` with:
- All errors found (categorized)
- All fixes applied
- Iteration details
- Final status

## Example Output

```
═══════════════════════════════════════════════════════════════════════════════
🔍 TRADING AGENT ERROR CHECK SYSTEM
═══════════════════════════════════════════════════════════════════════════════

[10:30:15] [INFO] Validating file structure...
[10:30:15] [INFO] ✓ Found: backend/api/main.py
[10:30:15] [INFO] ✓ Found: src/main.py
...

═══════════════════════════════════════════════════════════════════════════════
PHASE 1: STATIC ANALYSIS
═══════════════════════════════════════════════════════════════════════════════
[10:30:16] [INFO] Validating file structure...
[10:30:16] [INFO] Validating model files...
[10:30:16] [INFO] Validating configuration...
[10:30:16] [INFO] Analyzing API endpoints...
[10:30:16] [INFO] Analyzing frontend integration...

═══════════════════════════════════════════════════════════════════════════════
PHASE 2: INTEGRATION TESTING
═══════════════════════════════════════════════════════════════════════════════
[10:30:17] [INFO] Testing API connectivity...
[10:30:17] [INFO] Testing health endpoint...
[10:30:18] [INFO] Testing critical API endpoints...
```

## Notes

- The system runs up to 5 iterations by default (configurable via `-MaxIterations`)
- Only safe, automated fixes are applied (configuration files, not business logic)
- Configuration files are backed up before modification
- Requires Python 3.8+ and necessary dependencies
- Backend API should be running for full integration tests (optional - skips if unavailable)

## Integration with Existing Scripts

This command integrates with:
- **`scripts/integration_test.py`** - Full integration test suite
- **`validate_integration.py`** - Configuration validation
- **`check_health.py`** - Health status checks
- **`@start.md`** - Run before starting services to verify setup

## Troubleshooting

### Common Issues

**Issue: "Python not found"**
```bash
# Check Python installation
python --version
# If not found, install Python 3.8+ from python.org
```

**Issue: "Module not found" errors**
```bash
# Install required packages
pip install -r requirements.txt
pip install -r requirements-backend.txt  # if exists
```

**Issue: "No such file or directory: scripts/error-check.py"**
```bash
# Ensure you're running from project root
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"
# Or use relative path to scripts directory
```

**Issue: "Connection refused" during API tests**
- This is normal if the backend API isn't running
- Integration tests will be skipped automatically
- Start the backend with `@start.md` command for full testing

**Issue: Errors persist after automatic fixes**
1. Check `error_check_results.json` for detailed error information
2. Review specific error categories (Static Analysis, Integration Testing, etc.)
3. Apply manual fixes as needed (see "Manual Fixes Required" above)
4. Re-run the command to verify fixes worked
5. Check file backups if automatic fixes caused issues

**Issue: "Permission denied" errors (Linux/Mac)**
```bash
# Make Python script executable
chmod +x scripts/error-check.py
```

### Getting Help

If errors persist after troubleshooting:
1. Review `error_check_results.json` for complete error details
2. Check logs in `logs/` directory
3. Run related validation: `python integration_test.py`
4. See main documentation: [README.md](../../README.md#custom-commands)
5. Consult docs: [docs/guides/getting-started.md](../../docs/guides/getting-started.md)

## Related Commands

- **`@start.md`** - Start all services (run after error-check passes)
- **`@filer.md`** - Reorganize files if structure issues found
- **`@pushgit.md`** - Commit and push improvements

## References

- **Main Documentation**: [README.md](../../README.md)
- **Getting Started**: [docs/guides/getting-started.md](../../docs/guides/getting-started.md)
- **Configuration Setup**: [docs/setup/credentials.md](../../docs/setup/credentials.md)

