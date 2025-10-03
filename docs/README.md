# Workload Parser Documentation

Essential documentation for the workload-parser project.

## 🚀 Quick Start Options

### Standalone Executable (No Python Required)
- **[Distribution Guide](../README_DISTRIBUTION.md)** - Complete guide for using wlparser.exe
- Download and run wlparser.exe - no installation needed!

### Python Development
- **[Main README](../README.md)** - Project overview and installation
- Install with: `pip install -r requirements.txt`

##  Documentation Structure

```
docs/
 README.md                      # This file - documentation index
 TERMINOLOGY_GUIDE.md           # Key terms and definitions
 pcie/                          # PCIe-specific documentation
     README.md                  # PCIe docs index
     QUICK_REFERENCE.md         # Quick reference card
     SOCWATCH_HANDLING.md       # Technical guide
```

##  Documentation Files

### Getting Started

- **[Distribution Guide](../README_DISTRIBUTION.md)** - Standalone executable usage (wlparser.exe)
- **[Main README](../README.md)** - Project overview, features, installation
- **[Terminology Guide](TERMINOLOGY_GUIDE.md)** - Definitions of all key terms

### PCIe-Only SocWatch Data

- **[Quick Reference](pcie/QUICK_REFERENCE.md)** - Quick identification, commands, troubleshooting
- **[Technical Guide](pcie/SOCWATCH_HANDLING.md)** - Comprehensive technical details and configuration

### Configuration Files

- [config/daq_targets_default.json](../config/daq_targets_default.json) - **DAQ power rail configuration**
- [config/pcie_targets_default.json](../config/pcie_targets_default.json) - PCIe target metrics
- [config/socwatch_targets_default.json](../config/socwatch_targets_default.json) - SocWatch target metrics
- [config/parser_config.json](../config/parser_config.json) - Parser configuration
- [config/enhanced_parser_config.json](../config/enhanced_parser_config.json) - Enhanced parser configuration

### Examples

- [examples/basic_usage.py](../examples/basic_usage.py) - Basic parser usage with auto-detection and DAQ config
- [examples/pcie_parsing_example.py](../examples/pcie_parsing_example.py) - PCIe-specific examples

## Quick Start

### Using Standalone Executable

```powershell
# GUI mode - interactive folder browser
wlparser.exe

# Auto-detect all P_* power rails
wlparser.exe -i "path/to/workload/data"

# Use DAQ config for specific power rails
wlparser.exe -i "path/to/data" -d config/daq_targets_default.json

# Custom output location
wlparser.exe -i "path/to/data" -o "custom_report.xlsx"
```

See [README_DISTRIBUTION.md](../README_DISTRIBUTION.md) for complete standalone guide.

### Using Python API

```python
# Auto-detection mode (default)
from workload_parser import WorkloadParser
parser = WorkloadParser()
results = parser.parse_directory("path/to/workload/data")

# With DAQ configuration
parser = WorkloadParser(config_path="config/daq_config.json")
results = parser.parse_directory("path/to/data")
```

### Parsing PCIe-Only Data

```bash
# Command line
python -m workload_parser.cli parse -i "path/to/data" -o "output.xlsx"

# Python API
from workload_parser.parsers import PCIeParser
parser = PCIeParser()
result = parser.parse(file_path)
```

See [PCIe Quick Reference](pcie/QUICK_REFERENCE.md) for more examples.

---

*For questions, check the relevant documentation or troubleshooting sections.*
