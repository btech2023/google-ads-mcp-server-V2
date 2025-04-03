param(
    [string]$CustomerID = "7788990011" # Default Customer ID if not provided
)

# Run All Tests for Project NOVA ULTRA
# This script runs all the different types of tests for the project

# Get the project root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set Python command based on environment
$PythonCmd = "python"
if (Test-Path env:PYTHON_CMD) {
    $PythonCmd = $env:PYTHON_CMD
}

# Print banner
Write-Host "===================================================="
Write-Host "   Running All Tests for Project NOVA ULTRA   "
Write-Host "===================================================="
Write-Host ""

# Run the unit tests for database abstraction layer
Write-Host "Running database abstraction layer tests..."
& $PythonCmd -m unittest tests.db.test_cache_functionality
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database abstraction layer tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Database abstraction layer tests completed successfully." -ForegroundColor Green
Write-Host ""

# Run the batch processing tests
Write-Host "Running batch processing tests..."
& $PythonCmd .\scripts\test_batch_processing.py $CustomerID
if ($LASTEXITCODE -ne 0) {
    Write-Host "Batch processing tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Batch processing tests completed successfully." -ForegroundColor Green
Write-Host ""

# Run the query optimization tests
Write-Host "Running query optimization tests..."
& $PythonCmd .\scripts\test_query_optimization.py $CustomerID
if ($LASTEXITCODE -ne 0) {
    Write-Host "Query optimization tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Query optimization tests completed successfully." -ForegroundColor Green
Write-Host ""

# Run caching tests
Write-Host "Running cache implementation tests..."
& $PythonCmd .\scripts\test_cache.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Cache implementation tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Cache implementation tests completed successfully." -ForegroundColor Green
Write-Host ""

# Run the optimized performance tests
Write-Host "Running optimized performance tests..."
& $PythonCmd .\scripts\run_optimized_performance_test.py $CustomerID
if ($LASTEXITCODE -ne 0) {
    Write-Host "Performance tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Performance tests completed successfully." -ForegroundColor Green
Write-Host ""

# Generate the summary
Write-Host "===================================================="
Write-Host "              Test Summary                           "
Write-Host "===================================================="
Write-Host "All tests completed successfully!" -ForegroundColor Green
Write-Host "Check the performance_profiles directory for detailed reports."
Write-Host "" 