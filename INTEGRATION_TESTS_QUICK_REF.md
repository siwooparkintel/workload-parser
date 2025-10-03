# 🧪 Integration Testing Quick Reference

## Network Data Location
```
\\10.54.63.126\Pnpext\Siwoo\data
```

## Quick Commands

### Test Everything (Recommended First Run)
```powershell
# Test first 5 folders to validate setup
.\run_integration_tests.ps1 -MaxFolders 5
```

### Test All Folders
```powershell
# Auto-detection mode (finds all P_* power rails)
.\run_integration_tests.ps1

# With DAQ configuration (uses predefined targets)
.\run_integration_tests.ps1 -UseDaqConfig
```

### Custom Options
```powershell
# Custom data location
.\run_integration_tests.ps1 -DataRoot "D:\my\data"

# Test specific number of folders
.\run_integration_tests.ps1 -MaxFolders 10

# Custom output directory
.\run_integration_tests.ps1 -OutputDir "my_test_results"
```

### Get Help
```powershell
.\run_integration_tests.ps1 -Help
```

## What Gets Tested

✅ **Each Subfolder** in data directory containing workload files
✅ **Parser Functionality** - All file types (CSV, ETL, TXT, etc.)
✅ **Auto-Detection** - P_* power rail discovery from PACS
✅ **DAQ Configuration** - Predefined power rail targets
✅ **Excel Output** - Report generation and validation
✅ **Error Handling** - Permission errors, missing files, etc.
✅ **Performance** - Processing time per folder

## Results Location

```
test_results/
├── test_results_YYYYMMDD_HHMMSS.json    # Detailed JSON report
├── test_summary_YYYYMMDD_HHMMSS.xlsx    # Excel summary
└── [foldername]_report.xlsx             # Individual folder reports
```

## Expected Output

```
================================================================================
WORKLOAD PARSER INTEGRATION TEST SUITE
================================================================================

✅ Data root validated: \\10.54.63.126\Pnpext\Siwoo\data

🔍 Scanning for workload folders...
   ✓ Found: UHX2_DC_001
   ✓ Found: CataV3_Idle_002
   ...

📊 Found X workload folders to test

🚀 Starting tests...

[1/X] Testing: UHX2_DC_001
      Files in folder: 47
      Parsing with auto-detection mode...
      ✅ Output created: UHX2_DC_001_report.xlsx (234.5 KB)
      ⏱️  Duration: 23.45 seconds

...

================================================================================
TEST SUMMARY
================================================================================

📊 Overall Statistics:
   Total folders tested: X
   ✅ Successful: Y (Z%)
   ❌ Failed: A (B%)
   ⏱️  Total time: XX.XX seconds
   ⏱️  Average time per folder: XX.XX seconds

📁 Results saved to: test_results
```

## Interpreting Results

### Success ✅
- Parser completed successfully
- Excel output file created
- No errors encountered

### Warning ⚠️
- Parser completed but with issues
- Output may be incomplete
- Check warnings in JSON report

### Failed ❌
- Parser could not process folder
- No output created
- Check error message in report

## Common Issues & Solutions

### "Data root not found"
**Solution:** Ensure network share is mounted
```powershell
# Map network drive
net use Z: \\10.54.63.126\Pnpext\Siwoo\data
.\run_integration_tests.ps1 -DataRoot "Z:\data"
```

### "Permission denied"
**Solution:** Check folder access rights or skip those folders
- Tests continue with accessible folders
- Permission errors are logged in report

### Python not found
**Solution:** Activate virtual environment
```powershell
.venv\Scripts\activate
.\run_integration_tests.ps1
```

## Performance Tips

### Quick Validation (Fast)
```powershell
# Test only 3-5 folders for quick validation
.\run_integration_tests.ps1 -MaxFolders 3
```

### Full Test Suite (Comprehensive)
```powershell
# Test all folders for complete coverage
# This may take 30-60+ minutes depending on data size
.\run_integration_tests.ps1
```

### Parallel Testing (Advanced)
Edit `test_data_integration.py` to enable parallel processing for faster execution on multi-core systems.

## Automated Testing

### Daily Tests
Create a scheduled task to run tests automatically:
```powershell
# Create scheduled task (run as admin)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\path\to\run_integration_tests.ps1 -MaxFolders 10"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "WorkloadParserTests" -Action $action -Trigger $trigger
```

### CI/CD Integration
Add to GitHub Actions or other CI/CD pipelines:
```yaml
- name: Run Integration Tests
  run: |
    python tests/test_data_integration.py --max-folders 5
```

## Review Results

### Open Results Folder
```powershell
# Automatically opens after test completion
# Or manually:
explorer test_results
```

### View Summary Excel
```powershell
# Open latest summary
$latest = Get-ChildItem test_results\test_summary_*.xlsx | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Start-Process excel.exe $latest.FullName
```

### Check JSON Details
```powershell
# View JSON report
$latest = Get-ChildItem test_results\test_results_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName | ConvertFrom-Json | Format-List
```

## Next Steps

1. **Initial Validation**: Run with `-MaxFolders 5` to test setup
2. **Full Test**: Run complete test suite on all folders
3. **Review Results**: Check summary Excel for success rates
4. **Fix Issues**: Address any failed folders
5. **Regression Testing**: Re-run after code changes
6. **Documentation**: Update with any new findings

## More Information

- Full documentation: [tests/TEST_INTEGRATION_README.md](tests/TEST_INTEGRATION_README.md)
- Test script: [tests/test_data_integration.py](tests/test_data_integration.py)
- Main README: [README.md](README.md)
