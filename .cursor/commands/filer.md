# Reorganize Files

## What Is This?

This is a **Cursor AI IDE command** that reorganizes project files according to the documented rules (based on `REORGANIZATION_SUMMARY.md`).

## How To Use in Cursor

**Method 1 - Command Palette:**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type `@filer.md` and select it

**Method 2 - Composer:**
- Mention `@filer.md` in your Cursor Composer chat

**Method 3 - Direct Execution:**
- From terminal: Run `.\scripts\reorganize.ps1` (Windows) or manually organize files (see below)

## Prerequisites

Before running this command, ensure you have:
- All changes committed to git (reorganization may modify files)
- Backup space available (automatic backup created by default)
- Write permissions for the project directory
- Review of `REORGANIZATION_SUMMARY.md` to understand what will be moved/deleted

## Platform Compatibility

| Platform | Method | Instructions |
|----------|--------|--------------|
| Windows | PowerShell | `.\scripts\reorganize.ps1` |
| Linux/Mac | Manual | Use file system commands or adapt PowerShell script |

## Direct Execution

```powershell
.\scripts\reorganize.ps1
```

> **📋 Reorganization Details:** See [REORGANIZATION_SUMMARY.md](../../REORGANIZATION_SUMMARY.md) for complete file movement rules and examples.

## Description

Reorganizes project files by:
- Removing fix/status report files from root directory
- Removing outdated instruction TXT files
- Moving documentation to proper `docs/` subdirectories:
  - Setup guides → `docs/setup/`
  - Deployment guides → `docs/deployment/`
  - Architecture docs → `docs/architecture/`
  - User guides → `docs/guides/`
- Removing database backup files (`.db.backup_*`)
- Removing archive files (`.zip`)
- Creating backup before reorganization

## Safety Features

- **Dry-run mode**: Preview changes without applying them
- **Automatic backup**: Creates backup before reorganization
- **File preservation**: Preserves essential files (README.md, requirements.txt, config files, etc.)
- **Detailed logging**: Logs all changes for review

## Options

- `-DryRun` - Preview changes without applying them (recommended first)
- `-CreateBackup:$false` - Skip backup creation (not recommended)
- `-Force` - Force execution even if errors occur

## Usage Examples

```powershell
# Dry run first (preview changes)
.\scripts\reorganize.ps1 -DryRun

# Execute reorganization with backup (default)
.\scripts\reorganize.ps1

# Execute without backup (not recommended)
.\scripts\reorganize.ps1 -CreateBackup:$false
```

## Visual Example: Before and After

### Before Reorganization
```
Trading Agent/
├── README.md
├── requirements.txt
├── ARCHITECTURE_VERIFICATION_REPORT.md        ❌ Will be deleted
├── COMPLETE_INTEGRATION_SUMMARY.md            ❌ Will be deleted
├── ERROR_CHECK_REPORT.md                      ❌ Will be deleted
├── IMPLEMENTATION_SUMMARY.md                  ❌ Will be deleted
├── DASHBOARD_ISSUES_DIAGNOSTIC_REPORT.md      ❌ Will be deleted
├── DO_THIS_NOW.txt                            ❌ Will be deleted
├── EXECUTE_THIS.txt                           ❌ Will be deleted
├── START_HERE.txt                             ❌ Will be deleted
├── kubera_pokisham.db.backup_20251019_163745  ❌ Will be deleted
├── scripts.zip                                ❌ Will be deleted
├── CREDENTIALS_SETUP.md                       📁 Will move to docs/setup/
├── DEPLOYMENT_GUIDE.md                        📁 Will move to docs/deployment/
├── QUICK_START.md                             📁 Will move to docs/guides/
├── ai_trading_blueprint.md                    📁 Will move to docs/architecture/
└── frontend_web/
    ├── UI_IMPROVEMENTS_COMPLETE.md            ❌ Will be deleted
    ├── FINAL_STATUS.md                        ❌ Will be deleted
    └── QUICK_START.txt                        ❌ Will be deleted
```

### After Reorganization
```
Trading Agent/
├── README.md                                  ✅ Preserved
├── requirements.txt                           ✅ Preserved
├── docs/
│   ├── setup/
│   │   └── credentials.md                     ✅ Moved here
│   ├── deployment/
│   │   └── deployment-guide.md                ✅ Moved here
│   ├── architecture/
│   │   └── blueprint.md                       ✅ Moved here
│   └── guides/
│       └── quick-start.md                     ✅ Moved here
└── frontend_web/
    └── (all fix/status files removed)         ✅ Cleaned
```

## Recommended Workflow

1. **Commit current changes**: `git add . && git commit -m "Pre-reorganization"`
2. **Preview first**: Run with `-DryRun` to see what will change
3. **Review changes**: Check the dry-run output carefully
4. **Execute**: Run without `-DryRun` to apply changes
5. **Verify**: Check that essential files are preserved
6. **Restore if needed**: Use the backup directory if needed

## Backup and Restoration

### Automatic Backup Creation

By default, the script creates a timestamped backup:
```
backup/reorganize_20250115_143022/
├── (all files as they were before reorganization)
```

### Manual Restore from Backup

If you need to restore files from backup:

**Windows (PowerShell):**
```powershell
# View available backups
dir backup\

# Copy specific files back
Copy-Item "backup\reorganize_20250115_143022\ORIGINAL_FILE.md" -Destination "."

# Restore entire backup
Copy-Item "backup\reorganize_20250115_143022\*" -Destination "." -Recurse -Force
```

**Linux/Mac (Bash):**
```bash
# View available backups
ls backup/

# Copy specific files back
cp "backup/reorganize_20250115_143022/ORIGINAL_FILE.md" .

# Restore entire backup
cp -r "backup/reorganize_20250115_143022/"* .
```

### Git-Based Restore

If you committed before reorganizing:
```bash
# View recent commits
git log --oneline

# Restore specific files
git checkout <commit-hash> -- path/to/file

# Or restore entire state
git reset --hard <commit-hash>
```

## Troubleshooting

### Permission Errors

**Error:** "Access is denied" or "Permission denied"

**Solutions:**

**Windows:**
```powershell
# Run PowerShell as Administrator
Right-click PowerShell → Run as Administrator

# Check file permissions
Get-Acl -Path "file.txt"
```

**Linux/Mac:**
```bash
# Check file permissions
ls -la

# Fix permissions if needed
chmod 644 *.md
chmod 755 docs/
```

### Files Not Moving

**Error:** Files remain in original location

**Causes:**
1. Files are locked (being used by another process)
2. Path too long (Windows 260 char limit)
3. Insufficient permissions

**Solutions:**
```powershell
# Check for locked files
Handle.exe | findstr /i "filename"

# Kill the process using the file (replace PID)
taskkill /PID <PID> /F

# Try force mode
.\scripts\reorganize.ps1 -Force
```

### Backup Directory Full

**Error:** "Cannot create backup" or "Disk full"

**Solution:**
```powershell
# Check disk space
Get-PSDrive C | Select-Object Used,Free

# Clean old backups
Remove-Item "backup\reorganize_20250101_*" -Recurse

# Or skip backup (not recommended)
.\scripts\reorganize.ps1 -CreateBackup:$false
```

### Script Not Found

**Error:** "Cannot find path 'scripts\reorganize.ps1'"

**Solution:**
```powershell
# Ensure you're in project root
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"

# Check if script exists
Test-Path "scripts\reorganize.ps1"

# Use full path
.\scripts\reorganize.ps1
```

### PowerShell Execution Policy

**Error:** "Execution of scripts is disabled on this system"

**Solution:**
```powershell
# Check current policy
Get-ExecutionPolicy

# Change policy for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# OR bypass for just this script
powershell -ExecutionPolicy Bypass -File .\scripts\reorganize.ps1
```

### Accidental Deletion

**If you accidentally deleted important files:**

1. **Check backup directory**: `dir backup\`
2. **Restore from backup**: See "Manual Restore from Backup" above
3. **Use git**: `git checkout HEAD -- path/to/file`
4. **Check Recycle Bin**: (Windows) files may still be there

## Files Preserved (Never Deleted)

These files are **ALWAYS preserved**:
- `README.md` - Main project documentation
- `requirements.txt` - Python dependencies
- `*.py`, `*.tsx`, `*.js` - Source code files
- `config/` directory - Configuration files
- `.env`, `.env.example` - Environment files
- `package.json`, `package-lock.json` - Node.js dependencies
- `docker-compose.yml`, `Dockerfile` - Container configurations
- `*.yaml`, `*.yml` - Configuration files
- `.git/` - Git repository data
- Essential project data files

## Files That Will Be Deleted

- **Fix/Status Reports**: `*_REPORT.md`, `*_SUMMARY.md`, `*_STATUS.md`, `*_COMPLETE.md`
- **Instruction Files**: `DO_THIS_NOW.txt`, `EXECUTE_THIS.txt`, `START_HERE.txt`
- **Database Backups**: `*.db.backup_*`
- **Archive Files**: `*.zip` (unless in specific protected locations)
- **Temporary Files**: `*.tmp`, `*.temp`, `*.log` (old logs)

## Files That Will Be Moved

| From | To | Example |
|------|-----|---------|
| Root `*_SETUP*.md` | `docs/setup/` | `CREDENTIALS_SETUP.md` → `docs/setup/credentials.md` |
| Root `*_DEPLOY*.md` | `docs/deployment/` | `DEPLOYMENT_GUIDE.md` → `docs/deployment/deployment-guide.md` |
| Root `*_GUIDE.md` | `docs/guides/` | `QUICK_START.md` → `docs/guides/quick-start.md` |
| Root `*_ARCHITECTURE*.md` | `docs/architecture/` | `BLUEPRINT.md` → `docs/architecture/blueprint.md` |
| `frontend_web/*_STATUS*.md` | Delete | Various UI status files |

## Related Commands

- **`@error-check.md`** - Check for issues before reorganizing
- **`@pushgit.md`** - Commit reorganization changes
- **`@start.md`** - Restart services if needed after reorganization

## References

- **Reorganization Summary**: [REORGANIZATION_SUMMARY.md](../../REORGANIZATION_SUMMARY.md)
- **Main Documentation**: [README.md](../../README.md)
- **Getting Started**: [docs/guides/getting-started.md](../../docs/guides/getting-started.md)
- **Project Structure**: [docs/architecture/project-structure.md](../../docs/architecture/project-structure.md)

