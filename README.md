# Workload Parser

A modern Python application for parsing and analyzing workload data including power consumption, ETL processes, and socwatch metrics.

## 🚀 Quick Start - Standalone Executable

**No Python installation needed!** Download the standalone executable:

1. Download `wlparser.exe` (~46 MB)
2. Double-click to run (GUI mode) or use command line
3. See [README_DISTRIBUTION.md](README_DISTRIBUTION.md) for distribution guide

```powershell
# Auto-detect all P_* power rails
wlparser.exe -i "C:\path\to\workload\data"

# Use specific DAQ config
wlparser.exe -i "C:\path\to\data" -d config\daq_targets_default.json
```

## Features

- **Standalone Executable**: Single-file distribution, no dependencies
- **GUI Folder Browser**: Easy navigation to workload directories
- **Flexible Parser Framework**: Extensible architecture for adding new data parsers
- **Auto-Detection**: Automatically finds all P_* power rails from power summary
- **DAQ Config Mode**: Use predefined power rail targets
- **Configuration Management**: JSON-based configuration system with validation
- **Comprehensive Logging**: Structured logging with multiple output formats
- **Error Handling**: Robust error recovery and reporting
- **Testing**: Full test coverage with unit and integration tests

## Project Structure

```
workload_parser/
├── workload_parser/          # Main package
│   ├── __init__.py
│   ├── core/                 # Core framework components
│   ├── parsers/              # Parser implementations
│   ├── config/               # Configuration management
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── docs/                     # Documentation
├── examples/                 # Usage examples
└── requirements.txt          # Dependencies
```

## Installation

**For developers** (end users can use the standalone executable above):

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`

### Building Standalone Executable

To build your own executable:

```powershell
# Automated build
.\build_executable.ps1

# Or manual build
pip install pyinstaller
pyinstaller wlparser.spec --clean
```

The executable will be in the `dist/` folder.

## Usage

```python
from workload_parser import WorkloadParser

parser = WorkloadParser(config_path="config/parser_config.json")
results = parser.parse_directory("path/to/workload/data")
```

## Documentation

Essential documentation is available:

- **[Documentation Index](docs/README.md)** - Overview of all documentation
- **[Terminology Guide](docs/TERMINOLOGY_GUIDE.md)** - Key terms and definitions
- **[PCIe Documentation](docs/pcie/)** - PCIe-only SocWatch data handling
  - [Quick Reference](docs/pcie/QUICK_REFERENCE.md) - Fast lookups and commands
  - [Technical Guide](docs/pcie/SOCWATCH_HANDLING.md) - Detailed implementation
- **[Examples](examples/)** - Usage examples and code samples

## Development

Run tests: `python -m pytest`
Check code style: `python -m flake8`
Type checking: `python -m mypy workload_parser`

## License

MIT License