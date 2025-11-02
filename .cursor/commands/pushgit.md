# Push to GitHub with Changelog

## What Is This?

This is a **Cursor AI IDE command** that pushes changes to GitHub with automatic changelog generation comparing the current version with the previous version on GitHub.

## How To Use in Cursor

**Method 1 - Command Palette:**
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type `@pushgit.md` and select it

**Method 2 - Composer:**
- Mention `@pushgit.md` in your Cursor Composer chat

**Method 3 - Direct Execution:**
- From terminal: Run `.\scripts\push-updates.ps1` (Windows) or use standard git commands (see below)

## Prerequisites

Before running this command, ensure you have:
- **Git** installed and configured (`git --version`)
- **GitHub account** with repository access
- **Authentication** set up (SSH keys or GitHub CLI)
- Changes committed locally (or the script will stage everything)
- Push access to the remote repository

## Platform Compatibility

| Platform | Method | Instructions |
|----------|--------|--------------|
| Windows | PowerShell | `.\scripts\push-updates.ps1` |
| Linux/Mac | Git CLI | See "Alternative Execution" below |
| All | Manual | Use standard `git add/commit/push` commands |

## Direct Execution

```powershell
.\scripts\push-updates.ps1
```

## Description

Pushes changes to GitHub with automatic changelog generation:
- Checks git repository status (initializes if needed)
- Generates automatic changelog comparing current changes with remote repository
- Stages all changes
- Creates commit with your message (or auto-generates)
- Pushes to GitHub repository
- Handles remote repository configuration

## Changelog Generation

The script automatically generates `CHANGELOG.md` with:
- **Version and date**: Tracks when changes were made
- **Categorized changes**:
  - **Added**: New features, files, or functionality
  - **Changed**: Modified features or files
  - **Fixed**: Bug fixes and resolutions
  - **Documentation**: Documentation updates
- **File statistics**: Count of files added, modified, and deleted
- **Comparison**: Compares local changes with the previous version on GitHub

## Options

- `-CommitMessage "<message>"` - Custom commit message (prompts if not provided)
- `-Branch "<branch>"` - Branch name to push to (defaults to current branch)
- `-SkipChangelog` - Skip changelog generation (not recommended)
- `-Force` - Force push (overwrites remote changes - use with caution)
- `-RemoteName "<name>"` - Remote repository name (default: "origin")

## Usage Examples

```powershell
# Push with auto-generated commit message and changelog
.\scripts\push-updates.ps1

# Push with custom commit message
.\scripts\push-updates.ps1 -CommitMessage "Add new features and improve UI"

# Push to specific branch
.\scripts\push-updates.ps1 -Branch "develop"

# Push without changelog (not recommended)
.\scripts\push-updates.ps1 -SkipChangelog

# Force push (use with extreme caution)
.\scripts\push-updates.ps1 -Force
```

## Workflow

1. **Make changes**: Edit files in your project
2. **Run script**: Execute `push-updates.ps1`
3. **Review changelog**: Check the generated `CHANGELOG.md`
4. **Customize commit**: Provide custom commit message if needed
5. **Push**: Script automatically pushes to GitHub

## Features

- **Auto-detection**: Detects changes using git diff
- **Smart categorization**: Automatically categorizes changes (Added, Changed, Fixed, Docs)
- **Repository initialization**: Initializes git repository if needed
- **Remote configuration**: Configures remote repository if missing
- **Error handling**: Gracefully handles authentication and network errors
- **Version comparison**: Compares with previous version on GitHub

## Important Notes

- The changelog compares your local changes with the remote repository
- Previous version is determined by comparing with `origin/<branch>`
- Changelog is automatically staged and committed
- Authentication errors will prompt for credentials
- Network issues will be reported with helpful suggestions

## ⚠️ CRITICAL WARNING: Force Push

**The `-Force` flag is DANGEROUS and should be avoided!**

### Why Force Push Is Risky

Force push (`-Force` or `git push --force`) overwrites the remote branch history:
- **Destroys remote commits** that others may depend on
- **Cannot be undone** easily without backups
- **Breaks other developers'** local repositories
- **Causes data loss** for unrecovered commits

### When Force Push Might Be Acceptable

1. **Personal fork/branch** (no collaborators)
2. **Feature branch** (after approval from team)
3. **Historical cleanup** (squashing commits on branch)
4. **Emergency fix** (only with team awareness)

### Better Alternatives

Instead of force push:
1. **Pull and merge**: `git pull origin <branch>`
2. **Rebase carefully**: `git pull --rebase origin <branch>`
3. **Create new commit**: Amend and push to new commit
4. **Communicate**: Discuss changes with team before pushing

### How to Force Push Safely

If you MUST force push:
```powershell
# 1. Backup your branch first
git branch backup-$(Get-Date -Format "yyyyMMdd-HHmmss")

# 2. Warn your team
# Message in team chat about force push

# 3. Force push with lease (safer)
.\scripts\push-updates.ps1 -Force -Branch your-branch
```

## Example Changelog Output

Here's what `CHANGELOG.md` looks like:

```markdown
# Changelog

## Version 2.3.1 - 2025-01-15

### Added
- New ML model training scripts
- Enhanced dashboard analytics
- Real-time performance monitoring

### Changed
- Updated frontend API client configuration
- Improved error handling in trading engine
- Optimized database queries

### Fixed
- Fixed memory leak in long-running sessions
- Resolved CORS configuration issues
- Corrected chart rendering bug

### Documentation
- Added comprehensive API documentation
- Updated deployment guides
- Improved code comments

### Statistics
- Files Added: 12
- Files Modified: 45
- Files Deleted: 3

### Changes Since Last Version
- Comparison with origin/main (commit abc123)
- Detected 60 total file changes
- Net addition: 450 lines of code
```

## Alternative Execution (Linux/Mac)

### Standard Git Workflow

If you don't have PowerShell, use standard git commands:

```bash
# 1. Check status
git status

# 2. Generate your own changelog (optional)
# Review changes and create CHANGELOG.md manually

# 3. Stage changes
git add .

# 4. Commit with message
git commit -m "Your commit message here"

# 5. Push to remote
git push origin <branch-name>

# 6. If conflicts exist, pull first
git pull origin <branch-name>
git push origin <branch-name>
```

### Manual Changelog Creation

Create `CHANGELOG.md` manually based on your git diff:

```bash
# See what changed
git diff origin/main

# Get summary
git log origin/main..HEAD --oneline

# Generate basic changelog
echo "## Version X.X.X - $(date +%Y-%m-%d)" >> CHANGELOG.md
git diff origin/main --name-status | sort >> CHANGELOG.md
```

## Troubleshooting

### Authentication Failed

**Error:** "Authentication failed" or "permission denied"

**Solutions:**

1. **Check SSH keys** (recommended):
```bash
# Test SSH connection
ssh -T git@github.com

# If not set up, create SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add ~/.ssh/id_ed25519.pub to GitHub Settings → SSH Keys
```

2. **Use GitHub CLI**:
```bash
# Install GitHub CLI
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: apt install gh

# Authenticate
gh auth login
```

3. **Personal Access Token**:
```bash
# Create token on GitHub: Settings → Developer settings → Personal access tokens
# Use token as password when prompted
git remote set-url origin https://<token>@github.com/username/repo.git
```

### Repository Not Found

**Error:** "repository not found" or "remote does not exist"

**Solutions:**

1. **Check remote URL**:
```bash
git remote -v

# If wrong, set correct remote
git remote set-url origin https://github.com/username/repo.git
# OR
git remote add origin https://github.com/username/repo.git
```

2. **Initialize repository**:
```bash
# If no git repo exists
git init
git remote add origin https://github.com/username/repo.git
```

### Push Rejected (Non-Fast-Forward)

**Error:** "Updates were rejected because the tip of your current branch is behind"

**Solutions:**

1. **Pull and merge** (recommended):
```bash
git pull origin <branch>
# Resolve any conflicts
git push origin <branch>
```

2. **Pull with rebase**:
```bash
git pull --rebase origin <branch>
# Resolve conflicts if any
git push origin <branch>
```

3. **Force push** (⚠️ use with caution):
```powershell
.\scripts\push-updates.ps1 -Force
```

### Changelog Generation Failed

**Error:** "Failed to generate changelog"

**Causes:**
1. No remote repository configured
2. No previous commits to compare against
3. Script execution errors

**Solutions:**
```bash
# Skip changelog if issues persist
.\scripts\push-updates.ps1 -SkipChangelog

# Or generate manually
# Create CHANGELOG.md yourself based on git log
```

### Git Not Found

**Error:** "'git' is not recognized"

**Solution:**
```bash
# Check git installation
git --version

# Install git if missing
# Windows: git-scm.com
# Mac: brew install git
# Linux: sudo apt-get install git
```

### Large Files Rejected

**Error:** "File too large" or "push rejected due to file size"

**Solutions:**

1. **Use Git LFS** for large files:
```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.pkl"
git lfs track "models/*"
git add .gitattributes
```

2. **Add to .gitignore**:
```bash
# Add large files to .gitignore
echo "large-file.bin" >> .gitignore
git add .gitignore
git commit -m "Ignore large files"
```

## Git Configuration Best Practices

### Set Up Identity
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Configure Editor
```bash
# Windows
git config --global core.editor notepad

# Mac/Linux
git config --global core.editor nano
```

### Set Default Branch
```bash
git config --global init.defaultBranch main
```

### Configure .gitignore

Ensure `.gitignore` includes:
```gitignore
# Environment
.env
.env.local
*.env

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Node
node_modules/
npm-debug.log
yarn-error.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Database
*.db
*.db-journal

# Model files
models/*.pkl
*.h5
*.model

# Temporary files
*.tmp
*.temp
```

## Related Commands

- **`@error-check.md`** - Run error checks before pushing
- **`@filer.md`** - Reorganize files before committing
- **`@start.md`** - Start services after pulling updates

## References

- **Main Documentation**: [README.md](../../README.md)
- **Getting Started**: [docs/guides/getting-started.md](../../docs/guides/getting-started.md)
- **Git Documentation**: [git-scm.com/doc](https://git-scm.com/doc)
- **GitHub Help**: [docs.github.com](https://docs.github.com)

