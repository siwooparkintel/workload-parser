# Build script for wlparser.exe standalone executable
# Run this script to rebuild the executable after code changes

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "Building wlparser.exe standalone executable" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
Write-Host "Checking PyInstaller installation..." -ForegroundColor Yellow
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "ERROR: PyInstaller not found!" -ForegroundColor Red
    Write-Host "Install it with: pip install pyinstaller" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ PyInstaller found" -ForegroundColor Green
Write-Host ""

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Write-Host "✓ Cleaned build directories" -ForegroundColor Green
Write-Host ""

# Build the executable
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
Write-Host "(This may take 1-2 minutes...)" -ForegroundColor Gray
pyinstaller wlparser.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host "✓ Build successful!" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""
    
    # Show executable info
    $exePath = "dist\wlparser.exe"
    if (Test-Path $exePath) {
        $exeSize = (Get-Item $exePath).Length / 1MB
        Write-Host "Executable location: $exePath" -ForegroundColor Cyan
        Write-Host "File size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
        Write-Host ""
        
        # Test the executable
        Write-Host "Testing executable..." -ForegroundColor Yellow
        & $exePath --help | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Executable test passed" -ForegroundColor Green
        } else {
            Write-Host "⚠ Warning: Executable test failed" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Distribution files:" -ForegroundColor Cyan
    Write-Host "  - dist\wlparser.exe          (standalone executable)" -ForegroundColor White
    Write-Host "  - config\*.json              (configuration files)" -ForegroundColor White
    Write-Host "  - README_DISTRIBUTION.md     (distribution guide)" -ForegroundColor White
    Write-Host ""
    Write-Host "To distribute, zip these files together." -ForegroundColor Yellow
    
} else {
    Write-Host ""
    Write-Host "=======================================" -ForegroundColor Red
    Write-Host "✗ Build failed!" -ForegroundColor Red
    Write-Host "=======================================" -ForegroundColor Red
    Write-Host "Check the error messages above." -ForegroundColor Yellow
    exit 1
}
