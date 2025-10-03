# Workload Parser - Standalone Executable Distribution

## Quick Start

1. **Download `wlparser.exe`** (single file, ~46 MB)
2. **Run it!** No installation needed, no Python required

## Usage

### Option 1: GUI Mode (Easiest)
Just double-click `wlparser.exe` - a folder browser will open automatically!

### Option 2: Command Line
Open PowerShell or Command Prompt:

```powershell
# Auto-detect all P_* power rails (default mode)
wlparser.exe -i "C:\path\to\workload\data"

# Use specific DAQ targets config
wlparser.exe -i "C:\path\to\workload\data" -d config\daq_targets_default.json

# Specify output directory
wlparser.exe -i "\\server\share\data" -o "C:\Reports"
```

### Command Line Options

- `-i` / `--input`: Path to workload data directory
- `-o` / `--output`: Output directory for Excel report (default: same as input)
- `-d` / `--daq-config`: Path to DAQ targets config file
- `-h` / `--help`: Show help message

## Configuration Files (Optional)

If you want to use DAQ config mode, include the `config` folder with:
- `daq_targets_default.json` - Default DAQ power rail targets
- `enhanced_parser_config.json` - Enhanced parser configuration
- `pcie_targets_default.json` - PCIe targets
- `socwatch_targets_default.json` - Socwatch targets

Place the `config` folder in the same directory as `wlparser.exe`.

## Output

The tool generates an Excel report: `workload_analysis_YYYYMMDD_HHMMSS.xlsx`

### Auto-Detection Mode (default, no `-d` flag)
- Automatically detects all P_* power rails from power summary files
- Excludes V_* (voltage) and I_* (current) rails to reduce clutter
- Includes Socwatch and PCIe data if available

### DAQ Config Mode (with `-d` flag)
- Uses ONLY the metrics specified in the config file
- Includes V_*, I_*, and P_* rails as defined in config

## Folder Structure for Distribution

```
wlparser-standalone/
├── wlparser.exe          ← The standalone executable
├── README_DISTRIBUTION.md ← This file
└── config/               ← Optional config files
    ├── daq_targets_default.json
    ├── enhanced_parser_config.json
    ├── pcie_targets_default.json
    └── socwatch_targets_default.json
```

## Features

✅ No installation required  
✅ No Python needed  
✅ Single executable file  
✅ GUI folder browser  
✅ Automatic power rail detection  
✅ Supports network paths (UNC paths)  
✅ Handles Power, Socwatch, PCIe, ETL data  
✅ Generates formatted Excel reports  

## System Requirements

- Windows 10 or later (64-bit)
- ~100 MB free disk space
- Network access (if parsing from network shares)

## Troubleshooting

### "Windows protected your PC" message
This is normal for unsigned executables. Click "More info" → "Run anyway"

### Slow startup
First run might be slower (~10-15 seconds) as Windows unpacks the executable

### Antivirus warnings
Some antivirus software may flag PyInstaller executables. You can:
- Add an exception for `wlparser.exe`
- Build from source if your organization requires it

### Config files not found
Place the `config` folder in the same directory as `wlparser.exe`

## Building From Source

If you need to build the executable yourself:

```powershell
# Clone the repository
git clone https://github.com/siwooparkintel/workload-parser.git
cd workload-parser

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

# Build the executable
pyinstaller wlparser.spec --clean

# Find the executable in dist\wlparser.exe
```

## Version Information

- **Project**: workload-parser
- **Repository**: https://github.com/siwooparkintel/workload-parser
- **Build Tool**: PyInstaller
- **Python Version**: 3.11.6

## Support

For issues or questions:
1. Check the main repository README
2. Review the GitHub Issues page
3. Contact the development team

---

**Note**: This is a standalone executable distribution. All dependencies are bundled within the executable file.
