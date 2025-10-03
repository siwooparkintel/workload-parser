# Workload Parser Documentation

Essential documentation for the workload-parser project.

##  Documentation Structure

```
docs/
 README.md                      # This file
 pcie/                          # PCIe-specific documentation
     README.md                  # PCIe docs index
     QUICK_REFERENCE.md         # Quick reference card
     SOCWATCH_HANDLING.md       # Technical guide
```

##  Documentation Files

### PCIe-Only SocWatch Data

- **[Quick Reference](pcie/QUICK_REFERENCE.md)** - Quick identification, commands, troubleshooting
- **[Technical Guide](pcie/SOCWATCH_HANDLING.md)** - Comprehensive technical details and configuration

### Root Documentation

- **[Main README](../README.md)** - Project overview and installation
- **[Terminology Guide](TERMINOLOGY_GUIDE.md)** - Definitions of all key terms

### Configuration Files

- [config/pcie_targets_default.json](../config/pcie_targets_default.json) - PCIe target metrics
- [config/socwatch_targets_default.json](../config/socwatch_targets_default.json) - SocWatch target metrics
- [config/daq_targets_default.json](../config/daq_targets_default.json) - DAQ power rail configuration
- [config/enhanced_parser_config.json](../config/enhanced_parser_config.json) - Enhanced parser configuration

### Examples

- [examples/basic_usage.py](../examples/basic_usage.py) - Basic parser usage
- [examples/pcie_parsing_example.py](../examples/pcie_parsing_example.py) - PCIe-specific examples

## Quick Start

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
