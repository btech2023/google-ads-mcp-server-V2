# Run Performance Baseline Tests
# Project NOVA ULTRA - Phase 2: Performance Optimization
# This script runs the performance baseline tests and generates performance reports

param(
    [string]$CustomerID = "1234567890", # Replace with your test account ID
    [int]$RunsPerTest = 3,
    [switch]$FullSuite = $false
)

# Script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BaselineScript = Join-Path $ProjectRoot "scripts\performance_baseline.py"
$ProfilesDir = Join-Path $ProjectRoot "performance_profiles"

# Create profiles directory if it doesn't exist
if (-not (Test-Path $ProfilesDir)) {
    New-Item -Path $ProfilesDir -ItemType Directory -Force | Out-Null
    Write-Host "Created performance profiles directory: $ProfilesDir"
}

Write-Host "=====================================================`n"
Write-Host "Google Ads MCP Server - Performance Baseline Tests"
Write-Host "Project NOVA ULTRA - Phase 2: Performance Optimization"
Write-Host "`n====================================================="

Write-Host "`nRunning performance baseline tests with the following parameters:"
Write-Host "  - Customer ID: $CustomerID"
Write-Host "  - Runs per test: $RunsPerTest"
Write-Host "  - Full suite: $FullSuite"
Write-Host "`nResults will be saved to: $ProfilesDir"

# Change to project root directory
Push-Location $ProjectRoot

try {
    # Check if Python is available
    $PythonVersion = python --version
    Write-Host "`nPython version: $PythonVersion"
    
    # Run the performance baseline script
    Write-Host "`nStarting baseline tests..."
    if ($FullSuite) {
        # Run the full test suite
        python $BaselineScript $CustomerID $RunsPerTest --full
    } else {
        # Run the standard test suite
        python $BaselineScript $CustomerID $RunsPerTest
    }
    
    Write-Host "`nBaseline tests completed successfully!"
    Write-Host "Check the performance_profiles directory for results."
    
} catch {
    Write-Host "`nError running performance tests: $_" -ForegroundColor Red
} finally {
    # Return to original directory
    Pop-Location
}

Write-Host "`n====================================================="
Write-Host "Test run completed at: $(Get-Date)"
Write-Host "=====================================================`n" 