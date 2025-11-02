# PowerShell script to reorganize project files according to implemented rules
# Based on REORGANIZATION_SUMMARY.md

param(
    [switch]$DryRun = $false,
    [switch]$CreateBackup = $true,
    [switch]$Force = $false
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

# Change to project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     FILE REORGANIZATION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[!] DRY-RUN MODE: No files will be modified" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Get-FileAction {
    param(
        [string]$Action,
        [string]$File,
        [string]$Destination = $null
    )
    
    return @{
        Action = $Action
        File = $File
        Destination = $Destination
        FullPath = if ($Destination) { Join-Path $Destination (Split-Path -Leaf $File) } else { $null }
    }
}

function Log-Action {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $prefix = if ($DryRun) { "[DRY-RUN] " } else { "" }
    Write-Host "$prefix$Message" -ForegroundColor $Color
}

function Create-Directory {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
            Log-Action "    [OK] Created directory: $Path" "Green"
        } else {
            Log-Action "    [Would create] directory: $Path" "Gray"
        }
    }
}

function Move-File {
    param(
        [string]$Source,
        [string]$Destination
    )
    
    if (-not (Test-Path $Source)) {
        Log-Action "    [!] File not found: $Source" "Yellow"
        return $false
    }
    
    $destDir = Split-Path -Parent $Destination
    Create-Directory -Path $destDir
    
    if (-not $DryRun) {
        try {
            Move-Item -Path $Source -Destination $Destination -Force -ErrorAction Stop
            Log-Action "    [OK] Moved: $(Split-Path -Leaf $Source) -> $Destination" "Green"
            return $true
        } catch {
            Log-Action "    [FAIL] Failed to move: $Source - $_" "Red"
            return $false
        }
    } else {
        Log-Action "    [Would move] $(Split-Path -Leaf $Source) -> $Destination" "Gray"
        return $true
    }
}

function Remove-File {
    param([string]$Path)
    
    if (-not (Test-Path $Path)) {
        Log-Action "    [!] File not found: $Path" "Yellow"
        return $false
    }
    
    if (-not $DryRun) {
        try {
            Remove-Item -Path $Path -Force -ErrorAction Stop
            Log-Action "    [OK] Deleted: $Path" "Green"
            return $true
        } catch {
            Log-Action "    [FAIL] Failed to delete: $Path - $_" "Red"
            return $false
        }
    } else {
        Log-Action "    [Would delete] $Path" "Gray"
        return $true
    }
}

# ============================================================================
# FILE PATTERNS
# ============================================================================

# Files to remove from root directory
# Note: Patterns are converted from glob (**/*_SUMMARY.md) to PowerShell format (*_SUMMARY.md)
$filesToRemove = @(
    # Fix/Status Report patterns (MD files)
    @{
        Pattern = "*_SUMMARY.md"
        Description = "Summary reports"
    },
    @{
        Pattern = "*_REPORT.md"
        Description = "Status reports"
    },
    @{
        Pattern = "*_FIXES.md"
        Description = "Fix reports"
    },
    @{
        Pattern = "*_COMPLETE.md"
        Description = "Completion reports"
    },
    @{
        Pattern = "*_GUIDE.md"
        Description = "Guide files (should be in docs/)"
        Exclude = @("REORGANIZATION_SUMMARY.md", "ENHANCED_LAUNCHER_GUIDE.md", "LAUNCHER_COMPARISON.md", "ERROR_RESOLUTION_GUIDE.md", "TROUBLESHOOTING.md")
    },
    @{
        Pattern = "*_ANALYSIS*.md"
        Description = "Analysis reports"
    },
    @{
        Pattern = "*_VALIDATION*.md"
        Description = "Validation reports"
    },
    # Instruction TXT files
    @{
        Pattern = "DO_THIS_NOW.txt"
        Description = "Instruction files"
    },
    @{
        Pattern = "EXECUTE_THIS.txt"
        Description = "Instruction files"
    },
    @{
        Pattern = "QUICK_START*.txt"
        Description = "Quick start text files"
    },
    @{
        Pattern = "START_*.txt"
        Description = "Start instruction files"
    },
    @{
        Pattern = "*_STATUS.txt"
        Description = "Status text files"
    },
    # Database backups
    @{
        Pattern = "*.db.backup_*"
        Description = "Database backup files"
    },
    # Archives (unless in specific directories)
    @{
        Pattern = "*.zip"
        Description = "Archive files"
        Exclude = @("models/*.zip")
    }
)

# Files to move to docs/ structure
# Note: Patterns converted from glob (**/FILENAME.md) to PowerShell format (FILENAME.md)
$filesToMove = @{
    "setup" = @(
        @{Pattern = "CREDENTIALS_SETUP.md"; Destination = "docs/setup/credentials.md"},
        @{Pattern = "SIMPLE_START_GUIDE.md"; Destination = "docs/setup/simple-start.md"},
        @{Pattern = "START_INSTRUCTIONS.md"; Destination = "docs/setup/start-instructions.md"}
    );
    "deployment" = @(
        @{Pattern = "DEPLOYMENT_GUIDE.md"; Destination = "docs/deployment/deployment-guide.md"},
        @{Pattern = "DEPLOY.md"; Destination = "docs/deployment/docker-deploy.md"},
        @{Pattern = "DASHBOARD_SETUP_GUIDE.md"; Destination = "docs/deployment/dashboard-setup.md"},
        @{Pattern = "DIAGNOSTIC_SETUP_GUIDE.md"; Destination = "docs/deployment/diagnostic-setup.md"}
    );
    "architecture" = @(
        @{Pattern = "ai_trading_blueprint.md"; Destination = "docs/architecture/blueprint.md"},
        @{Pattern = "PROJECT_STRUCTURE.md"; Destination = "docs/architecture/project-structure.md"}
    );
    "guides" = @(
        @{Pattern = "QUICK_START.md"; Destination = "docs/guides/quick-start.md"},
        @{Pattern = "GUIDES.md"; Destination = "docs/guides/usage-guides.md"},
        @{Pattern = "DOCUMENTATION.md"; Destination = "docs/guides/documentation.md"},
        @{Pattern = "README_BAT_FILES.md"; Destination = "docs/guides/bat-files.md"},
        @{Pattern = "QUICK_START_HYBRID_UI.md"; Destination = "docs/guides/hybrid-ui.md"}
    )
}

# Files to preserve (essential files)
$filesToPreserve = @(
    "README.md",
    "requirements.txt",
    "requirements-backend.txt",
    "alembic.ini",
    ".gitignore",
    ".env.example",
    "env.template",
    "config/config.yaml",
    "config/env.example",
    "REORGANIZATION_SUMMARY.md",
    "ENHANCED_LAUNCHER_GUIDE.md",
    "ERROR_RESOLUTION_GUIDE.md",
    "TROUBLESHOOTING.md",
    "LAUNCHER_COMPARISON.md",
    "SIGNAL_HANDLING_FIXES.md",
    "FIX_RECOMMENDATIONS.md",
    "CURSORRULES_DEVIATIONS_REPORT.md"
)

# ============================================================================
# BACKUP FUNCTIONALITY
# ============================================================================

if ($CreateBackup -and -not $DryRun) {
    Write-Host "[*] Creating backup..." -ForegroundColor Blue
    $backupDir = Join-Path $projectRoot "backup_reorganization_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    try {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Log-Action "    [OK] Backup directory created: $backupDir" "Green"
    } catch {
        Log-Action "    [FAIL] Failed to create backup directory: $_" "Red"
        if (-not $Force) {
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
} else {
    $backupDir = $null
}

# ============================================================================
# SCAN FOR FILES TO REMOVE
# ============================================================================

Write-Host "[*] Scanning for files to remove..." -ForegroundColor Blue
Write-Host ""

$filesToDelete = @()

foreach ($rule in $filesToRemove) {
    # Get files from root directory only (not subdirectories)
    # Get all files from root, then filter by pattern using -like
    $files = Get-ChildItem -Path $projectRoot -File -ErrorAction SilentlyContinue | 
        Where-Object { 
            $file = $_
            # Only process files in root directory (parent directory must equal project root)
            $fileParent = Split-Path -Parent $file.FullName
            $isRootDir = ($fileParent -eq $projectRoot)
            
            if (-not $isRootDir) {
                return $false
            }
            
            # Match file name against pattern
            $matchesPattern = $file.Name -like $rule.Pattern
            if (-not $matchesPattern) {
                return $false
            }
            
            # Check if file should be excluded
            $shouldExclude = $false
            if ($rule.Exclude) {
                foreach ($exclude in $rule.Exclude) {
                    if ($file.Name -eq $exclude -or $file.FullName -like "*$exclude*") {
                        $shouldExclude = $true
                        break
                    }
                }
            }
            # Check if file is in preserve list
            $shouldPreserve = $false
            foreach ($preserve in $filesToPreserve) {
                if ($file.Name -eq $preserve -or $file.FullName -like "*$preserve*") {
                    $shouldPreserve = $true
                    break
                }
            }
            # Check if file is in node_modules, .git, or other system directories
            $isSystemDir = $file.FullName -match "(node_modules|\.git|__pycache__|\.next|dist|build|venv|env)"
            # Check if file is already in docs/ directory (already organized)
            $isInDocs = $file.FullName -like "*\docs\*"
            
            -not $shouldExclude -and -not $shouldPreserve -and -not $isSystemDir -and -not $isInDocs
        }
    
    if ($files) {
        Log-Action "  [*] Found $($files.Count) $($rule.Description):" "Cyan"
        foreach ($file in $files) {
            $relPath = $file.FullName.Replace($projectRoot + "\", "")
            $filesToDelete += $file.FullName
            Log-Action "    • $relPath" "Gray"
        }
        Write-Host ""
    }
}

# ============================================================================
# SCAN FOR FILES TO MOVE
# ============================================================================

Write-Host "[*] Scanning for files to move..." -ForegroundColor Blue
Write-Host ""

$filesToMoveList = @()

foreach ($category in $filesToMove.Keys) {
    foreach ($rule in $filesToMove[$category]) {
        # Get files from root directory only (not subdirectories)
        # Get all files from root, then filter by pattern using -like
        $files = Get-ChildItem -Path $projectRoot -File -ErrorAction SilentlyContinue |
            Where-Object {
                $file = $_
                # Only process files in root directory (parent directory must equal project root)
                $fileParent = Split-Path -Parent $file.FullName
                $isRootDir = ($fileParent -eq $projectRoot)
                
                if (-not $isRootDir) {
                    return $false
                }
                
                # Match file name against pattern (exact match for files to move)
                $matchesPattern = $file.Name -eq $rule.Pattern
                if (-not $matchesPattern) {
                    return $false
                }
                
                # Check if file is already in destination
                $destPath = Join-Path $projectRoot $rule.Destination
                $isAlreadyThere = $file.FullName -eq $destPath
                # Check if file is in system directories
                $isSystemDir = $file.FullName -match "(node_modules|\.git|__pycache__|\.next|dist|build|venv|env)"
                # Check if file is already in docs/ (might be duplicate)
                $isInDocs = $file.FullName -like "*\docs\*" -and -not $isAlreadyThere
                
                -not $isAlreadyThere -and -not $isSystemDir -and -not $isInDocs
            }
        
        if ($files) {
            foreach ($file in $files) {
                $destFullPath = Join-Path $projectRoot $rule.Destination
                $filesToMoveList += @{
                    Source = $file.FullName
                    Destination = $destFullPath
                    Category = $category
                }
            }
        }
    }
}

if ($filesToMoveList.Count -gt 0) {
    Log-Action "  [*] Found $($filesToMoveList.Count) files to move:" "Cyan"
    foreach ($item in $filesToMoveList) {
        $relSource = $item.Source.Replace($projectRoot + "\", "")
        $relDest = $item.Destination.Replace($projectRoot + "\", "")
        Log-Action "    • $relSource -> $relDest" "Gray"
    }
    Write-Host ""
}

# ============================================================================
# SUMMARY AND CONFIRMATION
# ============================================================================

$totalFiles = $filesToDelete.Count + $filesToMoveList.Count

if ($totalFiles -eq 0) {
    Write-Host "[OK] No files found that need reorganization!" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     REORGANIZATION SUMMARY" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files to delete:  $($filesToDelete.Count)" -ForegroundColor Yellow
Write-Host "Files to move:   $($filesToMoveList.Count)" -ForegroundColor Yellow
Write-Host "Total files:     $totalFiles" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "[!] This is a dry run. No files will be modified." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue"
} else {
    if ($CreateBackup) {
        Write-Host "[*] Backup will be created in: $backupDir" -ForegroundColor Cyan
        Write-Host ""
    }
    
    $confirmation = Read-Host "Do you want to proceed with reorganization? (yes/no)"
    if ($confirmation -notmatch "^yes$|^y$") {
        Write-Host "Reorganization cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# ============================================================================
# CREATE BACKUP
# ============================================================================

if ($CreateBackup -and -not $DryRun -and $backupDir) {
    Write-Host ""
    Write-Host "[*] Creating backup of files to be modified..." -ForegroundColor Blue
    
    foreach ($file in $filesToDelete) {
        if (Test-Path $file) {
            $relPath = $file.Replace($projectRoot + "\", "")
            $backupPath = Join-Path $backupDir $relPath
            $backupParent = Split-Path -Parent $backupPath
            if (-not (Test-Path $backupParent)) {
                New-Item -ItemType Directory -Path $backupParent -Force | Out-Null
            }
            Copy-Item -Path $file -Destination $backupPath -Force -ErrorAction SilentlyContinue
        }
    }
    
    foreach ($item in $filesToMoveList) {
        if (Test-Path $item.Source) {
            $relPath = $item.Source.Replace($projectRoot + "\", "")
            $backupPath = Join-Path $backupDir $relPath
            $backupParent = Split-Path -Parent $backupPath
            if (-not (Test-Path $backupParent)) {
                New-Item -ItemType Directory -Path $backupParent -Force | Out-Null
            }
            Copy-Item -Path $item.Source -Destination $backupPath -Force -ErrorAction SilentlyContinue
        }
    }
    
    Log-Action "    [OK] Backup completed" "Green"
    Write-Host ""
}

# ============================================================================
# EXECUTE REORGANIZATION
# ============================================================================

Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     EXECUTING REORGANIZATION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
$movedCount = 0
$failedCount = 0

# Delete files
if ($filesToDelete.Count -gt 0) {
    Write-Host "[*] Deleting files..." -ForegroundColor Red
    Write-Host ""
    
    foreach ($file in $filesToDelete) {
        if (Remove-File -Path $file) {
            $deletedCount++
        } else {
            $failedCount++
        }
    }
    Write-Host ""
}

# Move files
if ($filesToMoveList.Count -gt 0) {
    Write-Host "[*] Moving files..." -ForegroundColor Blue
    Write-Host ""
    
    foreach ($item in $filesToMoveList) {
        if (Move-File -Source $item.Source -Destination $item.Destination) {
            $movedCount++
        } else {
            $failedCount++
        }
    }
    Write-Host ""
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     REORGANIZATION COMPLETE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[*] Dry-run results:" -ForegroundColor Yellow
} else {
    Write-Host "[*] Reorganization results:" -ForegroundColor Green
}

Write-Host "    Files deleted:  $deletedCount / $($filesToDelete.Count)" -ForegroundColor $(if ($deletedCount -eq $filesToDelete.Count) { "Green" } else { "Yellow" })
Write-Host "    Files moved:   $movedCount / $($filesToMoveList.Count)" -ForegroundColor $(if ($movedCount -eq $filesToMoveList.Count) { "Green" } else { "Yellow" })
Write-Host "    Failed:        $failedCount" -ForegroundColor $(if ($failedCount -eq 0) { "Green" } else { "Red" })

if ($backupDir -and -not $DryRun) {
    Write-Host ""
    Write-Host "[*] Backup location: $backupDir" -ForegroundColor Cyan
    Write-Host "    You can restore files from the backup if needed." -ForegroundColor Gray
}

Write-Host ""
Write-Host "[*] Tips:" -ForegroundColor Yellow
Write-Host "    • Review the changes to ensure everything is correct" -ForegroundColor Gray
Write-Host "    • Update any references to moved files" -ForegroundColor Gray
Write-Host "    • Consider running git add to stage the reorganization" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"

