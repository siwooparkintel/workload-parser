# PCIe-Only SocWatch Documentation

Documentation for parsing PCIe-only SocWatch data (datasets like UHX2_DC_006, UHX2_DC_007).

## 📚 Documentation Files

### ⚡ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Quick reference card** - Start here for quick answers!

- Quick identification checklist
- Available metrics summary
- Command-line examples
- Troubleshooting guide
- Common commands

**Best for:** Quick lookups, troubleshooting, command-line usage

---

### 📋 [SOCWATCH_HANDLING.md](SOCWATCH_HANDLING.md)
**Comprehensive technical guide** - Deep dive into PCIe parsing

- Background on SocWatch data collection
- Detection logic and file structure
- PCIe metrics detailed explanation
- Configuration and customization
- Usage examples (CLI and Python API)
- Troubleshooting and debugging
- Migration notes from old code

**Best for:** Understanding implementation, customizing behavior, detailed reference

---

## 🚀 Quick Start

### Identify PCIe-Only Data

✅ Has these files:
- `workload_extraSession.etl`
- `workload_hwSession.etl`
- `workload_infoSession.etl`

❌ Missing this file:
- `workload_osSession.etl` ← KEY!

### Parse It

```bash
python -m workload_parser.cli parse -i "path/to/UHX2_DC_006" -o "output.xlsx"
```

### Python API

```python
from workload_parser.parsers import PCIeParser

parser = PCIeParser()
result = parser.parse(file_path)
```

---

## 📖 Reading Guide

**New users:** Start with [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Developers:** Read [SOCWATCH_HANDLING.md](SOCWATCH_HANDLING.md) and [WORKFLOW_DIAGRAMS.md](WORKFLOW_DIAGRAMS.md)

**Visual learners:** Check out [WORKFLOW_DIAGRAMS.md](WORKFLOW_DIAGRAMS.md)

**Troubleshooting:** See [QUICK_REFERENCE.md](QUICK_REFERENCE.md#-troubleshooting)

---

## 🔗 Related Documentation

- [Main Documentation Index](../README.md)
- [Quick Navigation](../QUICK_NAVIGATION.md)
- [Project Terminology Guide](../TERMINOLOGY_GUIDE.md)
- [Usage Examples](../../examples/pcie_parsing_example.py)
- [Test Suite](../../tests/test_pcie_parser.py)

---

*Last Updated: October 3, 2025*
