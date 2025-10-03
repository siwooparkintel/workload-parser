# Integration Testing for Workload Parser

This directory contains integration tests that validate the workload parser against real data from multiple workload directories.

## Overview

The integration test suite processes all subfolders in a data directory and generates comprehensive reports about:
- Success/failure rates
- Processing time per folder
- Errors and warnings
- Output file generation
- Overall parser performance

## Quick Start

### Using PowerShell Script (Recommended)

```powershell
# Test all folders with auto-detection
.\run_integration_tests.ps1

# Test only first 5 folders (quick test)
.\run_integration_tests.ps1 -MaxFolders 5

# Test with DAQ configuration
.\run_integration_tests.ps1 -UseDaqConfig

# Custom data location
.\run_integration_tests.ps1 -DataRoot "D:\my\data\folder"
```

### Using Python Directly

```bash
# Test all folders
python tests/test_data_integration.py

# Test with DAQ config
python tests/test_data_integration.py -d config/daq_targets_default.json

# Test limited folders
python tests/test_data_integration.py --max-folders 5

# Custom data root
python tests/test_data_integration.py --data-root "D:/my/data/folder"

# Full options
python tests/test_data_integration.py --help
```

## Data Source

Default data location: `\\10.54.63.126\Pnpext\Siwoo\data`

The test suite will:
1. Scan all subdirectories in the data root
2. Identify folders containing workload data (CSV, ETL, TXT files)
3. Process each folder with the workload parser
4. Generate detailed reports

## Test Results

Results are saved to `test_results/` directory:

### Generated Files

1. **`test_results_YYYYMMDD_HHMMSS.json`** - Detailed JSON report
   - Complete test results for each folder
   - Timestamps, durations, errors
   - File statistics

2. **`test_summary_YYYYMMDD_HHMMSS.xlsx`** - Excel summary
   - Summary sheet with overall statistics
   - Detailed results sheet with per-folder data
   - Easy to review and share

3. **`[foldername]_report.xlsx`** - Individual workload reports
   - Parser output for each tested folder
   - Same format as regular wlparser.exe output

### Report Contents

#### Summary Statistics
- Total folders tested
- Success/failure/warning counts
- Success rate percentage
- Total and average processing time

#### Detailed Results
- Folder name and path
- Status (success/failed/warning)
- Processing time
- Error messages (if any)
- File counts and statistics
- Output file location and size

## Test Modes

### Auto-Detection Mode (Default)
Tests the parser's ability to automatically detect all P_* power rails from PACS summary files.

```powershell
.\run_integration_tests.ps1
```

### DAQ Configuration Mode
Tests using predefined power rail targets from DAQ configuration.

```powershell
.\run_integration_tests.ps1 -UseDaqConfig
```

## Troubleshooting

### Network Share Not Accessible

```
ERROR: Data root not found: \\10.54.63.126\Pnpext\Siwoo\data
```

**Solutions:**
1. Ensure network share is mounted
2. Check network connectivity
3. Verify permissions
4. Use mapped drive: `-DataRoot "Z:\data"`

### Permission Errors

Some folders may fail with permission errors:
```
⚠️ Cannot access folder_name: PermissionError
```

**Solutions:**
- Tests will continue with accessible folders
- Check folder permissions
- Run with appropriate credentials

### Python Not Found

```
ERROR: Python not found in PATH!
```

**Solutions:**
1. Install Python 3.8+
2. Activate virtual environment: `.venv\Scripts\activate`
3. Use full path to Python in script

## Advanced Usage

### Test Specific Folders

Modify `test_data_integration.py` to filter folders:

```python
# In find_workload_folders(), add filter:
if "pattern" in item.name:
    workload_folders.append(item)
```

### Custom Validation

Add custom validation in `test_single_folder()`:

```python
# After parsing, add custom checks
if output_file.exists():
    # Validate Excel content
    df = pd.read_excel(output_file)
    if len(df) < 10:
        result['warnings'].append("Low data row count")
```

### Parallel Testing

For faster testing of many folders:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(self.test_single_folder, f) for f in folders]
    results = [f.result() for f in futures]
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: python tests/test_data_integration.py --max-folders 5
```

## Performance Benchmarks

Expected performance on typical workload folders:

| Folder Size | Files | Processing Time | Output Size |
|------------|-------|----------------|-------------|
| Small      | < 10  | 5-10 sec       | 50-100 KB   |
| Medium     | 10-50 | 15-30 sec      | 100-500 KB  |
| Large      | 50+   | 30-60 sec      | 500 KB-2 MB |

## Test Coverage

The integration tests validate:

✅ **File Discovery**
- Recursive folder scanning
- File type detection
- Data file identification

✅ **Parsing Functionality**
- Power rail detection/configuration
- ETL file processing
- SocWatch data handling
- PACS summary parsing

✅ **Output Generation**
- Excel report creation
- Data formatting
- Multiple sheet creation
- File size optimization

✅ **Error Handling**
- Missing files
- Corrupted data
- Permission errors
- Invalid formats

✅ **Performance**
- Processing time
- Memory usage
- Output size

## Example Output

```
================================================================================
WORKLOAD PARSER INTEGRATION TEST SUITE
================================================================================

✅ Data root validated: \\10.54.63.126\Pnpext\Siwoo\data

🔍 Scanning for workload folders in: \\10.54.63.126\Pnpext\Siwoo\data
   ✓ Found: UHX2_DC_001
   ✓ Found: CataV3_Idle_002
   ✓ Found: WorkloadA_003

📊 Found 3 workload folders to test

🚀 Starting tests on 3 folders...

[1/3] ================================================================================
Testing: UHX2_DC_001
================================================================================
   Files in folder: 47
   Parsing with auto-detection mode...
   ✅ Output created: UHX2_DC_001_report.xlsx (234.5 KB)
   ⏱️  Duration: 23.45 seconds

[2/3] ================================================================================
Testing: CataV3_Idle_002
================================================================================
   Files in folder: 35
   Parsing with auto-detection mode...
   ✅ Output created: CataV3_Idle_002_report.xlsx (187.2 KB)
   ⏱️  Duration: 18.92 seconds

[3/3] ================================================================================
Testing: WorkloadA_003
================================================================================
   Files in folder: 52
   Parsing with auto-detection mode...
   ✅ Output created: WorkloadA_003_report.xlsx (298.7 KB)
   ⏱️  Duration: 28.33 seconds

================================================================================
TEST SUMMARY
================================================================================

📊 Overall Statistics:
   Total folders tested: 3
   ✅ Successful: 3 (100.0%)
   ❌ Failed: 0 (0.0%)
   ⚠️  Warnings: 0 (0.0%)
   ⏱️  Total time: 70.70 seconds
   ⏱️  Average time per folder: 23.57 seconds

📁 Results saved to: test_results
================================================================================
```

## See Also

- [Main README](../README.md) - Project overview
- [Distribution Guide](../README_DISTRIBUTION.md) - Standalone executable
- [Test Core](test_core.py) - Unit tests for core functionality
- [Test PCIe](test_pcie_parser.py) - PCIe parser tests
