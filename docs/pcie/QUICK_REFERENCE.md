# PCIe-Only SocWatch - Quick Reference Card

## 🎯 Quick Identification

**Is this PCIe-only data?**

✅ YES if:
- Has `_extraSession.etl`, `_hwSession.etl`, `_infoSession.etl`
- **Missing** `_osSession.etl` ← KEY INDICATOR
- CSV only has PCIe sections (no C-states, P-states, etc.)

❌ NO if:
- Has `_osSession.etl` (full SocWatch data)
- Missing any of the 3 required ETL files
- Not a CSV file

**Common PCIe-Only Datasets:**
- UHX2_DC_006
- UHX2_DC_007

---

## 📊 Available Metrics

| Metric Type | Description | Example Keys |
|------------|-------------|--------------|
| **PCIe_LPM** | Link Power Management states | L0 (%), L0s (%), L1 (%), L2 (%) |
| **PCIe_Active** | Link active time | Active (%) |
| **PCIe_LTRsnoop** | Latency Tolerance Reporting | <1us, 1-10us, 10-100us, >100us |

**Devices Monitored:**
- NVM (NVMe Storage) - default
- WiFi, Ethernet, GPU - configurable

---

## 🚀 Quick Usage

### Command Line
```bash
# Parse single dataset
python -m workload_parser.cli parse -i "path/to/UHX2_DC_006" -o "output.xlsx"

# Parse multiple datasets
python -m workload_parser.cli parse -i "path/to/parent_folder" -o "all_results.xlsx"
```

### Python API
```python
from pathlib import Path
from workload_parser.parsers import PCIeParser

# Quick parse
parser = PCIeParser()
result = parser.parse(Path("UHX2_DC_006/workload.csv"))
pcie_data = result['pcie_data']

# Check if file is PCIe-only
if parser.can_parse(file_path):
    print("This is PCIe-only data!")
```

---

## 🔧 Configuration

**Location:** `config/pcie_targets_default.json`

**Default Targets:**
```json
[
  {"key": "PCIe_LPM", "devices": ["NVM"], 
   "lookup": "PCIe LPM Summary - Sampled: Approximated Residency (Percentage)"},
  
  {"key": "PCIe_Active", "devices": ["NVM"],
   "lookup": "PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)"},
  
  {"key": "PCIe_LTRsnoop", "devices": ["NVM"],
   "lookup": "PCIe LTR Snoop Summary - Sampled: Histogram"}
]
```

**Add More Devices:**
Change `"devices": ["NVM"]` to `"devices": ["NVM", "WiFi", "Ethernet"]`

---

## 🐛 Troubleshooting

### File Not Detected

**Problem:** Parser doesn't recognize PCIe-only file

**Check:**
1. ✅ All 3 ETL files exist? (`_extraSession`, `_hwSession`, `_infoSession`)
2. ✅ `_osSession.etl` is truly missing?
3. ✅ CSV filename matches ETL prefix?
4. ✅ File extension is `.csv`?

**Debug:**
```python
parser = PCIeParser()
print(f"Can parse: {parser.can_parse(file_path)}")
```

### No Metrics Extracted

**Problem:** Parser runs but finds no data

**Check:**
1. ✅ CSV contains PCIe sections?
2. ✅ Lookup strings match CSV headers exactly?
3. ✅ Device names match (case-sensitive)?
4. ✅ Config file loaded correctly?

**Debug:**
```python
targets = parser._load_pcie_targets()
print(f"Targets: {targets}")
```

### Wrong Parser Used

**Problem:** SocwatchParser used instead of PCIeParser

**Check:**
1. ✅ PCIeParser registered in parser registry?
2. ✅ `_osSession.etl` truly missing?
3. ✅ Parser priority/order correct?

**Fix:**
Ensure `_osSession.etl` doesn't exist in directory

---

## 📈 Expected Output

### Console
```
INFO     Parsing PCIe Socwatch file: workload.csv
INFO     Successfully parsed PCIe data: 9 metrics extracted
```

### Python Dict
```python
{
  'pcie_data': {
    'L0 (%)_NVM        PCIe_LPM': '95.2',
    'L0s (%)_NVM        PCIe_LPM': '2.1',
    'L1 (%)_NVM        PCIe_LPM': '1.5',
    'L2 (%)_NVM        PCIe_LPM': '1.2',
    'Active (%)_NVM        PCIe_Active': '12.5',
    '<1us_NVM        PCIe_LTRsnoop': '80.0',
    '1-10us_NVM        PCIe_LTRsnoop': '15.0',
    '10-100us_NVM        PCIe_LTRsnoop': '4.0',
    '>100us_NVM        PCIe_LTRsnoop': '1.0'
  },
  'file_info': {
    'path': '/path/to/workload.csv'
  }
}
```

### Excel Output
Metrics grouped by PCIe type (LPM, Active, LTRsnoop)

---

## 📚 Documentation Links

**Detailed Guides:**
- [PCIE_SOCWATCH_HANDLING.md](PCIE_SOCWATCH_HANDLING.md) - Technical details
- [PCIE_IMPLEMENTATION_SUMMARY.md](PCIE_IMPLEMENTATION_SUMMARY.md) - Implementation overview
- [PCIE_WORKFLOW_DIAGRAMS.md](PCIE_WORKFLOW_DIAGRAMS.md) - Visual diagrams

**Examples:**
- [examples/pcie_parsing_example.py](../examples/pcie_parsing_example.py) - Usage examples

**Tests:**
- [tests/test_pcie_parser.py](../tests/test_pcie_parser.py) - Test suite

**Terminology:**
- [TERMINOLOGY_GUIDE.md](../TERMINOLOGY_GUIDE.md) - Key terms

---

## ⚡ Common Commands

```bash
# Run tests
python -m pytest tests/test_pcie_parser.py -v

# View help
python -m workload_parser.cli parse --help

# Check installation
python -c "from workload_parser.parsers import PCIeParser; print('✅ Installed')"

# Example parsing
python examples/pcie_parsing_example.py
```

---

## 🎓 Key Concepts

**PCIe LPM States:**
- **L0**: Active, full power
- **L0s**: Active, low power (short recovery)
- **L1**: Standby (medium recovery)
- **L2**: Deeper sleep (long recovery)

**LTR Snoop:**
Histogram of PCIe device latency tolerance reporting for memory coherency

**Device Types:**
- **NVM**: NVMe storage (default monitored)
- **WiFi**: Wireless network adapter
- **Ethernet**: Wired network adapter

---

## 📞 Getting Help

1. **Check documentation** in `docs/` folder
2. **Run examples** in `examples/pcie_parsing_example.py`
3. **View test cases** in `tests/test_pcie_parser.py`
4. **Check terminology** in `TERMINOLOGY_GUIDE.md`

---

**Version:** 1.0  
**Last Updated:** October 3, 2025  
**Status:** Production Ready ✅
