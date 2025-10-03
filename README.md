# Workload Parser

A modern Python application for parsing and analyzing workload data including power consumption, ETL processes, and socwatch metrics.

## Features

- **Flexible Parser Framework**: Extensible architecture for adding new data parsers
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

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`

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