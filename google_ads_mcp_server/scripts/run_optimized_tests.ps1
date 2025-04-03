# Run Optimized Tests PowerShell Script
# This script runs optimization tests and cache functionality tests

# Get the project root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerRoot = Split-Path -Parent $ScriptDir # This is the server root
$ProjectRoot = Split-Path -Parent $ServerRoot # This is the actual project root

# Set Python command based on environment
$PythonCmd = "python"
if (Test-Path env:PYTHON_CMD) {
    $PythonCmd = $env:PYTHON_CMD
}

# Create performance profiles directory if it doesn't exist
$ProfilesDir = Join-Path $ServerRoot "performance_profiles"
if (-Not (Test-Path $ProfilesDir)) {
    New-Item -ItemType Directory -Path $ProfilesDir -Force | Out-Null
    Write-Host "Created directory: $ProfilesDir"
}

# Get customer ID from command line or use default
$CustomerID = $args[0]
if ([string]::IsNullOrEmpty($CustomerID)) {
    $CustomerID = "7788990011"  # Default test customer ID
}

# Print banner
Write-Host "===================================================="
Write-Host "   Running Optimization Tests for Project NOVA ULTRA   "
Write-Host "===================================================="
Write-Host ""

# Run the database abstraction cache functionality tests from the server root
Write-Host "Running database abstraction cache functionality tests..."
Push-Location $ServerRoot  # Change to the server root directory
# Use python -m unittest to run the tests as a module
& $PythonCmd -m unittest tests.db.test_cache_functionality
if ($LASTEXITCODE -ne 0) {
    Write-Host "Cache functionality tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    # Pop location even on failure to ensure proper cleanup
    Pop-Location
    exit $LASTEXITCODE
}
Write-Host "Cache functionality tests completed successfully." -ForegroundColor Green
Write-Host ""
Pop-Location  # Return to original directory

# Run the optimized performance test (this script likely expects to run from its own dir)
Write-Host "Running optimized performance test comparison..."
Push-Location $ScriptDir # Change to the scripts directory
$TestScript = Join-Path $ScriptDir "run_optimized_performance_test.py"
& $PythonCmd $TestScript $CustomerID
if ($LASTEXITCODE -ne 0) {
    Write-Host "Optimized performance test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    # Pop location even on failure to ensure proper cleanup
    Pop-Location
    exit $LASTEXITCODE
}
Write-Host "Optimized performance test completed successfully." -ForegroundColor Green
Write-Host ""
Pop-Location  # Return to original directory

# Generate the summary
Write-Host "===================================================="
Write-Host "              Test Summary                           "
Write-Host "===================================================="
Write-Host "All tests completed successfully!" -ForegroundColor Green
Write-Host "Check the performance_profiles directory for the optimization report."
Write-Host "" 