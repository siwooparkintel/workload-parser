# Run Integration Tests on Workload Data
# 
# This script runs comprehensive integration tests on all workload data subfolders
# Usage:
#   .\run_integration_tests.ps1                    # Test all folders with auto-detection
#   .\run_integration_tests.ps1 -MaxFolders 5      # Test only first 5 folders
#   .\run_integration_tests.ps1 -UseDaqConfig      # Test with DAQ configuration

param(
    [string]$DataRoot = "\\10.54.63.126\Pnpext\Siwoo\data",
    [string]$OutputDir = "test_results",
    [int]$MaxFolders = 0,
    [switch]$UseDaqConfig,
    [switch]$Help
)

# Show help
if ($Help) {
    Write-Host @"
Run Integration Tests on Workload Data
======================================

This script tests the workload parser on all subfolders in the data directory.

Usage:
  .\run_integration_tests.ps1 [options]

Options:
  -DataRoot <path>      Data root directory (default: \\10.54.63.126\Pnpext\Siwoo\data)
  -OutputDir <path>     Output directory for results (default: test_results)
  -MaxFolders <number>  Maximum number of folders to test (0 = all, default: 0)
  -UseDaqConfig         Use DAQ configuration instead of auto-detection
  -Help                 Show this help message

Examples:
  # Test all folders with auto-detection
  .\run_integration_tests.ps1

  # Test only first 5 folders
  .\run_integration_tests.ps1 -MaxFolders 5

  # Test with DAQ configuration
  .\run_integration_tests.ps1 -UseDaqConfig

  # Custom data location
  .\run_integration_tests.ps1 -DataRoot "D:\my\data\folder"

Results:
  - JSON report: test_results/test_results_YYYYMMDD_HHMMSS.json
  - Excel summary: test_results/test_summary_YYYYMMDD_HHMMSS.xlsx
  - Individual reports: test_results/*_report.xlsx
"@
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Workload Parser Integration Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if data root exists
Write-Host "Checking data root: $DataRoot" -ForegroundColor Yellow
if (-not (Test-Path $DataRoot)) {
    Write-Host "ERROR: Data root not found!" -ForegroundColor Red
    Write-Host "Please ensure the network share is mounted and accessible." -ForegroundColor Red
    Write-Host "Path: $DataRoot" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Data root accessible" -ForegroundColor Green

# Check Python environment
Write-Host "`nChecking Python environment..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "✓ Using virtual environment: .venv" -ForegroundColor Green
    $pythonCmd = ".venv\Scripts\python.exe"
} else {
    Write-Host "⚠ Virtual environment not found, using system Python" -ForegroundColor Yellow
    $pythonCmd = "python"
}

# Build command arguments
$testScript = "tests\test_data_integration.py"
$testArgs = @("--data-root", $DataRoot, "--output-dir", $OutputDir)

if ($MaxFolders -gt 0) {
    $testArgs += @("--max-folders", $MaxFolders)
    Write-Host "⚠ Testing limited to first $MaxFolders folders" -ForegroundColor Yellow
}

if ($UseDaqConfig) {
    $daqConfigPath = "config\daq_targets_default.json"
    if (Test-Path $daqConfigPath) {
        $testArgs += @("--daq-config", $daqConfigPath)
        Write-Host "✓ Using DAQ configuration: $daqConfigPath" -ForegroundColor Green
    } else {
        Write-Host "⚠ DAQ config not found: $daqConfigPath" -ForegroundColor Yellow
        Write-Host "  Continuing with auto-detection mode" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ Using auto-detection mode" -ForegroundColor Green
}

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "✓ Created output directory: $OutputDir" -ForegroundColor Green
}

# Run the tests
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Running Integration Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

try {
    & $pythonCmd $testScript @testArgs
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "`nERROR: Test execution failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total execution time: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
Write-Host ""

# Open results folder
if ($exitCode -eq 0 -or $exitCode -eq $null) {
    Write-Host "Opening results folder..." -ForegroundColor Green
    Start-Process explorer.exe $OutputDir
} else {
    Write-Host "Tests completed with errors. Exit code: $exitCode" -ForegroundColor Yellow
}

exit $exitCode
