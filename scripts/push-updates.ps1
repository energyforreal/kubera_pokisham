# PowerShell script to push updates to GitHub with automatic changelog generation
# Compares local changes with remote repository

param(
    [string]$CommitMessage = "",
    [string]$Branch = "",
    [switch]$SkipChangelog = $false,
    [switch]$Force = $false,
    [string]$RemoteName = "origin"
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

# Change to project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     📤 PUSH UPDATES TO GITHUB 📤" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Invoke-GitCommand {
    param(
        [string[]]$Arguments,
        [switch]$ShowOutput = $false
    )
    
    if (-not (Test-Command "git")) {
        Write-Host "❌ Git is not installed or not in PATH" -ForegroundColor Red
        return $null
    }
    
    try {
        $output = git $Arguments 2>&1
        $exitCode = $LASTEXITCODE
        
        if ($ShowOutput) {
            $output | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        }
        
        return @{
            Output = $output
            ExitCode = $exitCode
            Success = $exitCode -eq 0
        }
    } catch {
        Write-Host "❌ Git command failed: $_" -ForegroundColor Red
        return $null
    }
}

function Initialize-GitRepository {
    Write-Host "🔧 Initializing git repository..." -ForegroundColor Blue
    
    $result = Invoke-GitCommand -Arguments @("init") -ShowOutput $true
    if (-not $result.Success) {
        Write-Host "❌ Failed to initialize git repository" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    
    # Create .gitignore if it doesn't exist
    if (-not (Test-Path ".gitignore")) {
        Write-Host "📝 Creating .gitignore file..." -ForegroundColor Blue
        # Use existing .gitignore as template if available
        Copy-Item -Path ".gitignore" -Destination ".gitignore.backup" -ErrorAction SilentlyContinue
        Write-Host "✅ .gitignore will be created" -ForegroundColor Green
    }
    
    # Create initial commit
    $result = Invoke-GitCommand -Arguments @("add", ".") -ShowOutput $false
    $result = Invoke-GitCommand -Arguments @("commit", "-m", "Initial commit") -ShowOutput $false
    
    if ($result.Success) {
        Write-Host "✅ Initial commit created" -ForegroundColor Green
        return $true
    } else {
        Write-Host "⚠️  Failed to create initial commit" -ForegroundColor Yellow
        return $true  # Still return true as repo is initialized
    }
}

function Get-GitStatus {
    $statusResult = Invoke-GitCommand -Arguments @("status", "--porcelain")
    if ($statusResult.Success) {
        $changedFiles = ($statusResult.Output | Where-Object { $_ -match "^\s*[AMDU?]{2}" })
        return @{
            HasChanges = $changedFiles.Count -gt 0
            ChangedFiles = $changedFiles
            StatusOutput = $statusResult.Output
        }
    }
    return @{
        HasChanges = $false
        ChangedFiles = @()
        StatusOutput = @()
    }
}

function Get-GitDiff {
    param([string]$BaseCommit = "HEAD")
    
    $diffResult = Invoke-GitCommand -Arguments @("diff", "--stat", $BaseCommit)
    if ($diffResult.Success) {
        return $diffResult.Output -join "`n"
    }
    return ""
}

function Get-GitCommits {
    param(
        [string]$BaseCommit = "HEAD",
        [int]$Limit = 20
    )
    
    # Try to get commits since remote branch
    $commitsResult = Invoke-GitCommand -Arguments @("log", "--oneline", "--pretty=format:%h|%s|%an|%ad", "--date=short", "-n", $Limit.ToString(), "$BaseCommit..HEAD")
    if ($commitsResult.Success) {
        $commits = @()
        foreach ($line in $commitsResult.Output) {
            if ($line -match "^([^|]+)\|([^|]+)\|([^|]+)\|(.+)$") {
                $commits += @{
                    Hash = $Matches[1]
                    Message = $Matches[2]
                    Author = $Matches[3]
                    Date = $Matches[4]
                }
            }
        }
        return $commits
    }
    return @()
}

function Generate-Changelog {
    param(
        [string]$Version = "",
        [string]$BaseCommit = ""
    )
    
    Write-Host "📝 Generating changelog..." -ForegroundColor Blue
    
    $changelogPath = Join-Path $projectRoot "CHANGELOG.md"
    $changelog = @()
    
    # Header
    $date = Get-Date -Format "yyyy-MM-dd"
    if ($Version) {
        $changelog += "## Version $Version - $date"
    } else {
        $changelog += "## Unreleased - $date"
    }
    $changelog += ""
    
    # Get file changes
    $status = Get-GitStatus
    $addedFiles = @()
    $modifiedFiles = @()
    $deletedFiles = @()
    
    foreach ($file in $status.ChangedFiles) {
        $statusCode = $file.Substring(0, 2)
        $fileName = $file.Substring(3).Trim()
        
        if ($statusCode -match "^A|^\?") {
            $addedFiles += $fileName
        } elseif ($statusCode -match "^M") {
            $modifiedFiles += $fileName
        } elseif ($statusCode -match "^D") {
            $deletedFiles += $fileName
        }
    }
    
    # Get commit messages if available
    $commits = @()
    if ($BaseCommit) {
        $commits = Get-GitCommits -BaseCommit $BaseCommit
    } else {
        # Try to find remote branch
        $remoteResult = Invoke-GitCommand -Arguments @("branch", "-r")
        if ($remoteResult.Success) {
            $remoteBranches = $remoteResult.Output | Where-Object { $_ -match "origin/" }
            if ($remoteBranches) {
                $remoteBranch = ($remoteBranches[0] -replace "^\s*origin/", "").Trim()
                $commits = Get-GitCommits -BaseCommit "origin/$remoteBranch"
            }
        }
    }
    
    # Organize changes by category
    $added = @()
    $changed = @()
    $fixed = @()
    $docs = @()
    
    foreach ($commit in $commits) {
        $msg = $commit.Message.ToLower()
        if ($msg -match "^(add|feat|new|implement)") {
            $added += $commit.Message
        } elseif ($msg -match "^(fix|bug|resolve)") {
            $fixed += $commit.Message
        } elseif ($msg -match "^(doc|readme|guide|changelog)") {
            $docs += $commit.Message
        } else {
            $changed += $commit.Message
        }
    }
    
    # Also categorize files
    foreach ($file in $addedFiles) {
        if ($file -match "\.(md|txt)$|docs/|README") {
            $docs += "Added $file"
        } elseif ($file -match "\.(py|ts|tsx|js|jsx)$") {
            $added += "Added $file"
        }
    }
    
    foreach ($file in $modifiedFiles) {
        if ($file -match "\.(md|txt)$|docs/|README|CHANGELOG") {
            $docs += "Updated $file"
        } elseif ($file -match "\.(py|ts|tsx|js|jsx)$") {
            $changed += "Updated $file"
        }
    }
    
    foreach ($file in $deletedFiles) {
        $changed += "Removed $file"
    }
    
    # Build changelog sections
    if ($added.Count -gt 0) {
        $changelog += "### Added"
        foreach ($item in $added) {
            $changelog += "- $item"
        }
        $changelog += ""
    }
    
    if ($changed.Count -gt 0) {
        $changelog += "### Changed"
        foreach ($item in $changed) {
            $changelog += "- $item"
        }
        $changelog += ""
    }
    
    if ($fixed.Count -gt 0) {
        $changelog += "### Fixed"
        foreach ($item in $fixed) {
            $changelog += "- $item"
        }
        $changelog += ""
    }
    
    if ($docs.Count -gt 0) {
        $changelog += "### Documentation"
        foreach ($item in $docs) {
            $changelog += "- $item"
        }
        $changelog += ""
    }
    
    # File statistics
    $changelog += "### File Changes"
    $changelog += "- Files added: $($addedFiles.Count)"
    $changelog += "- Files modified: $($modifiedFiles.Count)"
    $changelog += "- Files deleted: $($deletedFiles.Count)"
    $changelog += ""
    
    return $changelog -join "`n"
}

# ============================================================================
# CHECK GIT INSTALLATION
# ============================================================================

if (-not (Test-Command "git")) {
    Write-Host "❌ Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "   Please install Git from https://git-scm.com/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Git found: $(git --version)" -ForegroundColor Green
Write-Host ""

# ============================================================================
# CHECK/INITIALIZE GIT REPOSITORY
# ============================================================================

Write-Host "🔍 Checking git repository..." -ForegroundColor Blue

if (-not (Test-Path ".git")) {
    Write-Host "⚠️  Git repository not found in current directory" -ForegroundColor Yellow
    
    $initialize = Read-Host "Do you want to initialize a git repository? (yes/no)"
    if ($initialize -match "^yes$|^y$") {
        if (-not (Initialize-GitRepository)) {
            Write-Host "❌ Failed to initialize git repository" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Git repository initialization cancelled." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "✅ Git repository found" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# CHECK REMOTE REPOSITORY
# ============================================================================

$remoteResult = Invoke-GitCommand -Arguments @("remote", "-v")
$hasRemote = $false
$remoteUrl = ""

if ($remoteResult.Success) {
    $remotes = $remoteResult.Output
    foreach ($remote in $remotes) {
        if ($remote -match "^$RemoteName\s+(.+)\s+\(fetch\)$") {
            $hasRemote = $true
            $remoteUrl = $Matches[1]
            break
        }
    }
}

if (-not $hasRemote) {
    Write-Host "⚠️  No remote repository configured" -ForegroundColor Yellow
    Write-Host ""
    $addRemote = Read-Host "Do you want to add a remote repository? (yes/no)"
    
    if ($addRemote -match "^yes$|^y$") {
        $remoteUrl = Read-Host "Enter remote repository URL (e.g., https://github.com/user/repo.git)"
        if ($remoteUrl) {
            $result = Invoke-GitCommand -Arguments @("remote", "add", $RemoteName, $remoteUrl) -ShowOutput $true
            if ($result.Success) {
                Write-Host "✅ Remote repository added: $remoteUrl" -ForegroundColor Green
                $hasRemote = $true
            } else {
                Write-Host "❌ Failed to add remote repository" -ForegroundColor Red
                Read-Host "Press Enter to exit"
                exit 1
            }
        }
    }
    
    if (-not $hasRemote) {
        Write-Host "⚠️  No remote repository configured. Push will only create local commits." -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Remote repository found: $remoteUrl" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# CHECK CURRENT BRANCH
# ============================================================================

$branchResult = Invoke-GitCommand -Arguments @("branch", "--show-current")
$currentBranch = if ($branchResult.Success) { ($branchResult.Output -join "").Trim() } else { "main" }

if ($Branch) {
    # Switch to specified branch
    $checkoutResult = Invoke-GitCommand -Arguments @("checkout", "-b", $Branch) -ShowOutput $false
    if (-not $checkoutResult.Success) {
        # Branch might already exist
        $checkoutResult = Invoke-GitCommand -Arguments @("checkout", $Branch) -ShowOutput $false
    }
    if ($checkoutResult.Success) {
        $currentBranch = $Branch
    }
}

Write-Host " Branch: $currentBranch" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CHECK FOR CHANGES
# ============================================================================

Write-Host "🔍 Checking for changes..." -ForegroundColor Blue

$status = Get-GitStatus

if (-not $status.HasChanges) {
    Write-Host "✅ No changes detected. Repository is clean." -ForegroundColor Green
    
    # Still check if we need to push commits
    if ($hasRemote) {
        $aheadResult = Invoke-GitCommand -Arguments @("rev-list", "--count", "HEAD..origin/$currentBranch") -ShowOutput $false
        $ahead = 0
        if ($aheadResult.Success) {
            try {
                $ahead = [int]($aheadResult.Output -join "").Trim()
            } catch {}
        }
        
        if ($ahead -eq 0) {
            Write-Host "✅ Local branch is up to date with remote." -ForegroundColor Green
            Write-Host ""
            Read-Host "Press Enter to exit"
            exit 0
        } else {
            Write-Host "⚠️  Local branch is $ahead commits ahead of remote." -ForegroundColor Yellow
        }
    } else {
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 0
    }
} else {
    Write-Host "📋 Found changes:" -ForegroundColor Cyan
    $status.ChangedFiles | ForEach-Object {
        Write-Host "    • $_" -ForegroundColor Gray
    }
}
Write-Host ""

# ============================================================================
# GENERATE CHANGELOG
# ============================================================================

$changelogContent = ""
$changelogPath = Join-Path $projectRoot "CHANGELOG.md"

if (-not $SkipChangelog -and $status.HasChanges) {
    # Try to get version from package.json or README.md
    $version = ""
    
    # Read existing CHANGELOG if it exists
    $existingChangelog = ""
    if (Test-Path $changelogPath) {
        $existingChangelog = Get-Content $changelogPath -Raw -ErrorAction SilentlyContinue
    }
    
    # Determine base commit for comparison
    $baseCommit = ""
    if ($hasRemote) {
        # Fetch latest from remote
        Write-Host "📥 Fetching latest from remote..." -ForegroundColor Blue
        Invoke-GitCommand -Arguments @("fetch", $RemoteName) -ShowOutput $false | Out-Null
        $baseCommit = "origin/$currentBranch"
    }
    
    $changelogContent = Generate-Changelog -Version $version -BaseCommit $baseCommit
    
    # Prepend to existing changelog
    if ($existingChangelog) {
        $changelogContent = $changelogContent + "`n`n---`n`n" + $existingChangelog
    }
    
    # Write changelog
    try {
        Set-Content -Path $changelogPath -Value $changelogContent -Encoding UTF8
        Write-Host "✅ Changelog generated: CHANGELOG.md" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Failed to write changelog: $_" -ForegroundColor Yellow
    }
    
    # Stage changelog
    Invoke-GitCommand -Arguments @("add", $changelogPath) -ShowOutput $false | Out-Null
    Write-Host ""
}

# ============================================================================
# STAGE CHANGES
# ============================================================================

Write-Host "📦 Staging changes..." -ForegroundColor Blue

$addResult = Invoke-GitCommand -Arguments @("add", "-A") -ShowOutput $false

if ($addResult.Success) {
    Write-Host "✅ Changes staged" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to stage changes" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# ============================================================================
# CREATE COMMIT
# ============================================================================

if ($status.HasChanges -or $changelogContent) {
    if (-not $CommitMessage) {
        $CommitMessage = Read-Host "Enter commit message (or press Enter for auto-generated)"
        if (-not $CommitMessage) {
            # Auto-generate commit message
            $fileCount = $status.ChangedFiles.Count
            if ($fileCount -gt 0) {
                $CommitMessage = "Update: $fileCount file(s) changed"
            } else {
                $CommitMessage = "Update: Changelog and documentation updates"
            }
        }
    }
    
    Write-Host "💾 Creating commit..." -ForegroundColor Blue
    Write-Host "   Message: $CommitMessage" -ForegroundColor Gray
    
    $commitResult = Invoke-GitCommand -Arguments @("commit", "-m", $CommitMessage) -ShowOutput $true
    
    if ($commitResult.Success) {
        Write-Host "✅ Commit created" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create commit" -ForegroundColor Red
        Write-Host "   $($commitResult.Output -join '`n')" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
}

# ============================================================================
# PUSH TO REMOTE
# ============================================================================

if ($hasRemote) {
    Write-Host "📤 Pushing to remote repository..." -ForegroundColor Blue
    Write-Host "   Remote: $RemoteName" -ForegroundColor Gray
    Write-Host "   Branch: $currentBranch" -ForegroundColor Gray
    Write-Host ""
    
    $pushArgs = @("push", $RemoteName, $currentBranch)
    if ($Force) {
        $pushArgs += "--force"
        Write-Host "⚠️  Force push enabled" -ForegroundColor Yellow
    }
    
    $pushResult = Invoke-GitCommand -Arguments $pushArgs -ShowOutput $true
    
    if ($pushResult.Success) {
        Write-Host ""
        Write-Host "✅ Successfully pushed to remote!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Failed to push to remote" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Possible solutions:" -ForegroundColor Yellow
        Write-Host "   1. Check your authentication credentials" -ForegroundColor Gray
        Write-Host "   2. Ensure you have push permissions" -ForegroundColor Gray
        Write-Host "   3. Pull latest changes first: git pull origin $currentBranch" -ForegroundColor Gray
        Write-Host "   4. Check network connection" -ForegroundColor Gray
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "⚠️  No remote repository configured. Changes are committed locally only." -ForegroundColor Yellow
    Write-Host "   To push to a remote repository, add it with:" -ForegroundColor Gray
    Write-Host "   git remote add origin <repository-url>" -ForegroundColor Gray
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     ✅ PUSH COMPLETE ✅" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "📊 Summary:" -ForegroundColor Green
Write-Host "    Branch:      $currentBranch" -ForegroundColor White
if ($status.HasChanges) {
    Write-Host "    Files:       $($status.ChangedFiles.Count)" -ForegroundColor White
}
if ($hasRemote) {
    Write-Host "    Remote:      $remoteUrl" -ForegroundColor White
    Write-Host "    Status:      ✅ Pushed successfully" -ForegroundColor Green
} else {
    Write-Host "    Status:      ✅ Committed locally" -ForegroundColor Green
}

if (-not $SkipChangelog -and $changelogContent) {
    Write-Host "    Changelog:   ✅ Generated (CHANGELOG.md)" -ForegroundColor Green
}

Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "    • Review the changes in your repository" -ForegroundColor Gray
Write-Host "    • Check CHANGELOG.md for update documentation" -ForegroundColor Gray
if ($hasRemote) {
    Write-Host "    • View your repository online: $remoteUrl" -ForegroundColor Gray
}
Write-Host ""

Read-Host "Press Enter to exit"

