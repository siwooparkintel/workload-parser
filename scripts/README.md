# Scripts Directory

This directory contains automation scripts for building and testing the workload parser.

## Scripts

### `build_executable.ps1`

Builds a standalone `wlparser.exe` executable using PyInstaller.

**Usage:**
```powershell
.\scripts\build_executable.ps1
```

**What it does:**
- Checks PyInstaller installation
- Cleans previous builds (`build/` and `dist/` folders)
- Builds executable from `config/wlparser.spec`
- Creates `dist/wlparser.exe` standalone executable
- Shows file size and location of the built executable

**Requirements:**
- PyInstaller: `pip install pyinstaller`

---

### `run_integration_tests.ps1`

Runs comprehensive integration tests on workload data folders.

**Usage:**
```powershell
# Test all folders with auto-detection
.\scripts\run_integration_tests.ps1

# Test only first 5 folders (quick test)
.\scripts\run_integration_tests.ps1 -MaxFolders 5

# Test with DAQ configuration
.\scripts\run_integration_tests.ps1 -UseDaqConfig

# Custom data location
.\scripts\run_integration_tests.ps1 -DataRoot "D:\my\data" -OutputDir "my_results"

# Show help
.\scripts\run_integration_tests.ps1 -Help
```

**Parameters:**
- `-DataRoot <path>` - Data root directory (default: `\\10.54.63.126\Pnpext\Siwoo\data`)
- `-OutputDir <path>` - Output directory for test results (default: `test_results`)
- `-MaxFolders <n>` - Limit test to first N folders (for quick testing)
- `-UseDaqConfig` - Use DAQ targets configuration from `config/daq_targets_default.json`
- `-Help` - Show help message

**What it does:**
- Scans data root for workload folders
- Runs parser on each folder with auto-detection
- Validates parsing results (file generation, warnings, errors)
- Generates JSON test report in `test_results/` directory
- Shows summary statistics (pass/fail counts, timing)

**Output:**
- JSON report: `test_results/test_results_YYYYMMDD_HHMMSS.json`
- Console summary with color-coded results

---

## Notes

- Both scripts should be run from the project root directory
- Scripts reference configuration files in `config/` directory
- Test outputs go to `test_results/` directory (gitignored)
