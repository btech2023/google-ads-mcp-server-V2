<#
.SYNOPSIS
    Generates a changelog for the Google Ads MCP Server project.
.DESCRIPTION
    This script compares the current state of the repository with the previous
    commit and generates a detailed changelog in Markdown format. It tracks modified,
    added, and deleted files, and provides code metrics.
.PARAMETER OutputPath
    Optional. The directory where the changelog should be saved.
    Defaults to logs/change-logs/ in the repository root.
.PARAMETER InstallGitHook
    Switch parameter. When specified, installs a post-commit Git hook to run this script automatically.
.EXAMPLE
    .\scripts\generate-changelog.ps1
    Generates a changelog in the default location.
.EXAMPLE
    .\scripts\generate-changelog.ps1 -InstallGitHook
    Installs a Git hook to run this script automatically after each commit.
#>

param(
    [string]$OutputPath,
    [switch]$InstallGitHook
)

# Define constants
$LINE_THRESHOLD = 300

# Ensure we're in the repository root
$repoRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Not in a git repository. Please run this script from a git repository."
    exit 1
}
cd $repoRoot

# Function to install Git hook
function Install-GitHook {
    $hookPath = Join-Path $repoRoot ".git\hooks\post-commit"
    $scriptPath = Resolve-Path (Join-Path $repoRoot "scripts\generate-changelog.ps1")
    
    $hookContent = @"
#!/bin/sh
# Post-commit hook to generate changelog
powershell.exe -ExecutionPolicy Bypass -File "$scriptPath"
echo "Changelog generated automatically post-commit"
"@
    
    Set-Content -Path $hookPath -Value $hookContent
    
    # Make the hook executable (more relevant on Unix systems, but good practice)
    if ($IsLinux -or $IsMacOS) {
        chmod +x $hookPath
    }
    
    Write-Host "Git post-commit hook installed successfully to run changelog generator" -ForegroundColor Green
}

# Install Git hook if requested
if ($InstallGitHook) {
    Install-GitHook
    exit 0
}

# Set default output path if not specified
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoRoot "logs\change-logs"
}

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    Write-Host "Created directory: $OutputPath"
}

# Determine the changelog filename with today's date
$date = Get-Date -Format "yyyy-MM-dd"
$changelogFilename = "changes-$date.md"
$changelogPath = Join-Path $OutputPath $changelogFilename

# Check if there are any git changes
$hasChanges = $false
git rev-parse HEAD > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    $hasChanges = $true
}

if (-not $hasChanges) {
    Write-Warning "No git history found. This might be a new repository."
    $modifiedFiles = @()
    $addedFiles = @()
    $deletedFiles = @()
} else {
    # Get modified files from git
    $modifiedFiles = git diff --name-status HEAD~1 HEAD | Where-Object { $_ -match '^M\s+(.+)$' } | ForEach-Object { $matches[1] }
    $addedFiles = git diff --name-status HEAD~1 HEAD | Where-Object { $_ -match '^A\s+(.+)$' } | ForEach-Object { $matches[1] }
    $deletedFiles = git diff --name-status HEAD~1 HEAD | Where-Object { $_ -match '^D\s+(.+)$' } | ForEach-Object { $matches[1] }
}

# Initialize metrics
$totalLinesAdded = 0
$totalLinesRemoved = 0
$largeFiles = @()

# Process modified files to gather line changes and identify large files
foreach ($file in $modifiedFiles) {
    if (Test-Path $file) {
        # Count lines in the file
        $lineCount = (Get-Content $file | Measure-Object -Line).Lines
        
        # Check if the file exceeds the line threshold
        if ($lineCount -gt $LINE_THRESHOLD) {
            $largeFiles += @{
                Path = $file
                Lines = $lineCount
            }
        }

        # Get line changes from git diff
        $diffStats = git diff --numstat HEAD~1 HEAD -- $file
        if ($diffStats -match "(\d+)\s+(\d+)\s+") {
            $linesAdded = [int]$matches[1]
            $linesRemoved = [int]$matches[2]
            $totalLinesAdded += $linesAdded
            $totalLinesRemoved += $linesRemoved
        }
    }
}

# Check new files for line count
foreach ($file in $addedFiles) {
    if (Test-Path $file) {
        # Count lines in the file
        $lineCount = (Get-Content $file | Measure-Object -Line).Lines
        $totalLinesAdded += $lineCount
        
        # Check if the file exceeds the line threshold
        if ($lineCount -gt $LINE_THRESHOLD) {
            $largeFiles += @{
                Path = $file
                Lines = $lineCount
            }
        }
    }
}

# Get commit messages
$commitMessages = git log --pretty=format:"- %s" -3

# Create changelog content
$changelog = @"
# Changes for $date

## Recent Commits
$($commitMessages -join "`n")

## Files Modified
$($modifiedFiles | ForEach-Object { "- $_ " } | Out-String)

## Files Added
$($addedFiles | ForEach-Object { "- $_ " } | Out-String)

## Files Deleted
$($deletedFiles | ForEach-Object { "- $_ " } | Out-String)

## Code Metrics
- Total lines added: $totalLinesAdded
- Total lines removed: $totalLinesRemoved

## Large Files (exceeding $LINE_THRESHOLD lines)
$($largeFiles | ForEach-Object { "- $($_.Path) ($($_.Lines) lines)" } | Out-String)

## Modularization Candidates
$($largeFiles | ForEach-Object { 
    "- $($_.Path) ($($_.Lines) lines) - Consider breaking this file down into smaller modules" 
} | Out-String)

## Review Notes
- Review the modularization candidates during the next status meeting
- Add any planned refactoring tasks to the project backlog
- Consider prioritizing files that exceed 500 lines
"@

# Save the changelog
Set-Content -Path $changelogPath -Value $changelog

Write-Host "Changelog generated: $changelogPath"

# Also create directory structure if it doesn't exist
$errorLogsPath = Join-Path $repoRoot "logs\error-logs"
$solutionLogsPath = Join-Path $repoRoot "logs\solution-logs"

if (-not (Test-Path $errorLogsPath)) {
    New-Item -ItemType Directory -Path $errorLogsPath -Force | Out-Null
    Write-Host "Created directory: $errorLogsPath"
}

if (-not (Test-Path $solutionLogsPath)) {
    New-Item -ItemType Directory -Path $solutionLogsPath -Force | Out-Null
    Write-Host "Created directory: $solutionLogsPath"
}

Write-Host "Log directory structure now conforms to project management rules."

# Show modularization candidates in the console for immediate awareness
if ($largeFiles.Count -gt 0) {
    Write-Host "`nModularization Candidates (files exceeding $LINE_THRESHOLD lines):" -ForegroundColor Yellow
    foreach ($file in $largeFiles) {
        Write-Host "- $($file.Path) ($($file.Lines) lines)" -ForegroundColor Yellow
    }
    Write-Host "Consider discussing these files in your next status meeting." -ForegroundColor Yellow
} 