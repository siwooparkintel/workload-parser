# PCIe-Only SocWatch Data Handling

## Overview

This document explains how the workload-parser handles PCIe-only SocWatch data, specifically for datasets like **UHX2_DC_006** and **UHX2_DC_007** where the `_osSession.etl` file is missing.

## Background

### Normal SocWatch Data Collection

A complete SocWatch data collection typically includes four ETL (Event Trace Log) files:

1. `{workload}_extraSession.etl` - Extra telemetry session
2. `{workload}_hwSession.etl` - Hardware monitoring session
3. `{workload}_infoSession.etl` - Information session
4. `{workload}_osSession.etl` - **Operating System session** (critical for full metrics)

When all four ETL files are present, SocWatch can generate comprehensive summaries including:
- CPU C-states and P-states
- OS wakeup events
- Core concurrency
- Package power states
- **And PCIe link states**

### PCIe-Only SocWatch Data

In some cases (like UHX2_DC_006 and UHX2_DC_007), the `_osSession.etl` file is missing. When this occurs:

- SocWatch can still process the hardware-level data
- The generated CSV summary contains **only PCIe-related metrics**
- OS-level metrics (C-states, wakeups, etc.) are unavailable

## Detection Logic

The `PCIeParser` class uses the following logic to detect PCIe-only data:

```python
def can_parse(self, file_path: Path) -> bool:
    # 1. Check file is CSV
    # 2. Verify 3 required ETL files exist (_extraSession, _hwSession, _infoSession)
    # 3. Confirm _osSession.etl is MISSING
    # 4. Verify CSV filename matches workload prefix
    
    if all_conditions_met:
        return True  # This is PCIe-only data
```

## PCIe Metrics Extracted

The parser extracts the following PCIe metrics based on the configuration in `config/pcie_targets_default.json`:

### 1. PCIe_LPM (Link Power Management)
- **Lookup**: "PCIe LPM Summary - Sampled: Approximated Residency (Percentage)"
- **Data**: Residency percentages for PCIe link power states (L0, L0s, L1, L2)
- **Devices**: NVM (NVMe storage)

### 2. PCIe_Active
- **Lookup**: "PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)"
- **Data**: Percentage of time PCIe link is actively transmitting data
- **Devices**: NVM (NVMe storage)

### 3. PCIe_LTRsnoop
- **Lookup**: "PCIe LTR Snoop Summary - Sampled: Histogram"
- **Data**: Latency Tolerance Reporting snoop latency histogram
- **Devices**: NVM (NVMe storage)

## Configuration

### PCIe Targets Configuration

Location: `config/pcie_targets_default.json`

```json
[
  {
    "key": "PCIe_LPM",
    "devices": ["NVM"],
    "lookup": "PCIe LPM Summary - Sampled: Approximated Residency (Percentage)"
  },
  {
    "key": "PCIe_Active",
    "devices": ["NVM"],
    "lookup": "PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)"
  },
  {
    "key": "PCIe_LTRsnoop",
    "devices": ["NVM"],
    "lookup": "PCIe LTR Snoop Summary - Sampled: Histogram"
  }
]
```

### Adding New Devices

To monitor additional PCIe devices (WiFi, Ethernet, GPU, etc.), add device names to the `devices` array:

```json
{
  "key": "PCIe_LPM",
  "devices": ["NVM", "WiFi", "Ethernet"],
  "lookup": "PCIe LPM Summary - Sampled: Approximated Residency (Percentage)"
}
```

## Data Structure

### Input CSV Structure

PCIe-only SocWatch CSV files contain sections like:

```
PCIe LPM Summary - Sampled: Approximated Residency (Percentage)
Device,L0 (%),L0s (%),L1 (%),L2 (%)
NVM Express Controller,95.2,2.1,1.5,1.2
WiFi Adapter,80.5,10.2,5.3,4.0

PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)
Device,Active (%)
NVM Express Controller,12.5
```

### Parsed Output Structure

The parser flattens the data for Excel reporting:

```python
{
    'L0 (%)_NVM        PCIe_LPM': '95.2',
    'L0s (%)_NVM        PCIe_LPM': '2.1',
    'L1 (%)_NVM        PCIe_LPM': '1.5',
    'L2 (%)_NVM        PCIe_LPM': '1.2',
    'Active (%)_NVM        PCIe_Active': '12.5',
    ...
}
```

## Integration with Main Parser

The `PCIeParser` is automatically detected and used by the main parsing framework:

1. **File Detection**: When processing a directory, the parser registry checks each CSV file
2. **Parser Selection**: If `PCIeParser.can_parse()` returns True, it handles the file
3. **Data Extraction**: PCIe metrics are extracted and added to the dataset
4. **Excel Export**: Data is included in the final Excel report with proper grouping

## Differences from Full SocWatch Data

| Feature | Full SocWatch | PCIe-Only |
|---------|--------------|-----------|
| OS Wakeups | ✅ Available | ❌ Not available |
| CPU C-states | ✅ Available | ❌ Not available |
| CPU P-states | ✅ Available | ❌ Not available |
| Temperature | ✅ Available | ❌ Not available |
| Bandwidth Metrics | ✅ Available | ❌ Not available |
| PCIe LPM | ✅ Available | ✅ Available |
| PCIe Active | ✅ Available | ✅ Available |
| PCIe LTR | ✅ Available | ✅ Available |

## Usage Example

### Command Line

```bash
# Parse directory containing PCIe-only data
python -m workload_parser.cli parse -i "path/to/UHX2_DC_006" -o "output.xlsx"
```

### Python API

```python
from pathlib import Path
from workload_parser.parsers.socwatch_parser import PCIeParser

# Initialize parser
parser = PCIeParser()

# Check if file can be parsed
file_path = Path("UHX2_DC_006/workload.csv")
if parser.can_parse(file_path):
    # Parse the file
    result = parser.parse(file_path)
    
    # Access PCIe data
    pcie_data = result['pcie_data']
    print(f"PCIe metrics extracted: {len(pcie_data)}")
```

## Troubleshooting

### Issue: PCIe data not detected

**Symptoms**: CSV file exists but parser doesn't recognize it as PCIe-only data

**Check**:
1. Verify 3 required ETL files exist (`_extraSession`, `_hwSession`, `_infoSession`)
2. Confirm `_osSession.etl` is truly missing
3. Ensure CSV filename matches ETL workload prefix
4. Check logs for parser detection messages

### Issue: Missing PCIe metrics

**Symptoms**: Parser runs but extracts no metrics or incomplete metrics

**Check**:
1. Verify `config/pcie_targets_default.json` exists
2. Confirm lookup strings match actual CSV section headers
3. Check device names match those in the CSV (case-sensitive)
4. Review parser logs for extraction warnings

### Issue: Wrong parser selected

**Symptoms**: Regular SocwatchParser processes PCIe-only file instead of PCIeParser

**Check**:
1. PCIeParser is registered in the parser registry
2. Parser priority/order in registry
3. File detection logic in both parsers

## Migration Notes

### From Old Code (`pcie_socwatch_summary_parser.py`)

The new implementation maintains compatibility with the old parser but with improvements:

**Old Code**:
```python
# Old: Global header dictionary
pcie_socwatch_header_dict = dict()

# Old: Separate header extraction
extractHeader(tTable)
```

**New Code**:
```python
# New: Integrated into parser class
class PCIeParser(BaseParser):
    def _extract_pcie_metrics(self, content: str):
        # Headers are automatically handled
        # Data is flattened for Excel reporting
```

**Benefits**:
- Object-oriented design
- Better error handling
- Consistent with other parsers
- Easier to extend and maintain

## Future Enhancements

Potential improvements for PCIe-only parsing:

1. **Multi-device Support**: Automatically detect and parse all PCIe devices (not just NVM)
2. **Advanced Histograms**: Better parsing of LTR snoop histograms
3. **Time-series Data**: Extract time-series PCIe activity if available
4. **Link Speed Detection**: Parse PCIe link speed (Gen3, Gen4, Gen5) information
5. **Bandwidth Calculations**: Calculate effective bandwidth from residency data

---

*Last Updated: October 3, 2025*
