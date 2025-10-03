# Terminology Guide - Workload Parser

## Project Overview Terms

### **Workload Parser**
A comprehensive Python library for parsing and analyzing various performance monitoring and telemetry data formats from Intel tools and Windows tracing utilities.

---

## Core Components

### **Parser**
A module responsible for reading, interpreting, and extracting structured data from specific file formats. Each parser handles one or more related data formats.

### **ETL Parser**
Parses Windows Event Trace Log (ETL) files, which contain performance and diagnostic data captured by Windows Performance Analyzer and similar tools.

### **HOBL Parser**
Handles HOBL (Hardware Observability) data files, which contain low-level hardware telemetry and performance metrics.

### **SocWatch Parser**
Processes SocWatch log files - Intel's power and performance analysis tool data that monitors SoC (System on Chip) power states, frequencies, and other metrics.

### **PCIe Parser (PCIe-only SocWatch)**
Specialized parser for SocWatch data that contains only PCIe (Peripheral Component Interconnect Express) metrics. This occurs when the `_osSession.etl` file is missing but other SocWatch ETL files are present. Common in datasets like UHX2_DC_006 and UHX2_DC_007.

### **Power Parser**
Parses power-related telemetry data, including voltage, current, power consumption, and thermal measurements.

### **Intel Parsers**
A collection of parsers for various Intel-specific data formats and tools including DAQ (Data Acquisition) and PCIe telemetry data.

---

## Configuration Terms

### **Parser Configuration**
JSON-based configuration files that define parsing rules, target metrics, column mappings, and data transformation logic for each parser type.

### **Target Metrics**
Specific data points or measurements that the parser is configured to extract from input files (e.g., CPU frequency, power consumption, temperature).

### **DAQ Targets**
Data Acquisition target metrics configuration, specifying which hardware counters and signals to extract from DAQ data files.

### **PCIe Targets**
PCIe (Peripheral Component Interconnect Express) bus telemetry targets, defining which PCIe traffic, bandwidth, and link state metrics to capture. This includes:
- **PCIe_LPM**: PCIe Link Power Management state residency
- **PCIe_Active**: PCIe link active state residency
- **PCIe_LTRsnoop**: PCIe Latency Tolerance Reporting (LTR) snoop histogram

### **SocWatch Targets**
Configuration defining which SoC metrics to extract from SocWatch logs (e.g., C-states, P-states, package power, residency times).

---

## Data Processing Terms

### **Enhanced Parser**
An extended version of the base parser with additional features like advanced filtering, data transformation, and aggregation capabilities.

### **Core Module**
The foundational parsing engine that provides base classes, common utilities, and shared functionality used by all specific parsers.

### **Workload Analyzer**
A higher-level analysis tool that uses multiple parsers to provide comprehensive workload characterization and performance insights.

---

## File Format Terms

### **ETL (Event Trace Log)**
Binary file format used by Windows for recording system events, performance counters, and trace data.

### **CSV (Comma-Separated Values)**
Common output format for parsed data, making it easy to import into analysis tools like Excel or Pandas.

### **JSON Configuration**
Human-readable configuration files using JSON format to define parser behavior and target metrics.

---

## Performance Monitoring Terms

### **C-States**
CPU idle power states - deeper C-states save more power but have higher exit latency.

### **P-States**
CPU performance states - different frequency and voltage operating points for active CPU cores.

### **Residency**
The amount of time (usually percentage) that a CPU or component spends in a particular state.

### **Telemetry**
Automated measurement and data collection from hardware components, transmitted for monitoring and analysis.

### **Hardware Counter**
Special registers in processors that count hardware events like cache misses, branch mispredictions, or instruction counts.

---

## Tool Integration Terms

### **CLI (Command-Line Interface)**
The command-line tool provided by workload-parser for parsing files and running analysis from the terminal.

### **Logger/Logging**
Utility module for recording parser operations, errors, warnings, and debug information during execution.

### **Exception Handling**
Custom exception classes for graceful error handling and informative error messages during parsing operations.

---

## Development Terms

### **Module**
A Python file or package containing related functionality, following the project's hierarchical structure.

### **Parser Factory**
Design pattern for creating appropriate parser instances based on file type or format detection.

### **Config Loader**
Utility for reading and validating JSON configuration files before parser initialization.

---

## Output and Results Terms

### **Parsed Data**
Structured data extracted from input files, typically in DataFrame or dictionary format.

### **Data Frame**
Pandas DataFrame structure commonly used for storing and manipulating parsed tabular data.

### **Aggregation**
Process of combining multiple data points or time series into summary statistics or reduced datasets.

### **Time Series**
Sequential data points indexed by timestamp, common output format for performance metrics over time.

---

## Use Case Terms

### **Performance Analysis**
The process of examining parsed data to identify bottlenecks, optimize workloads, or characterize system behavior.

### **Power Profiling**
Analyzing power consumption patterns to optimize energy efficiency or identify power anomalies.

### **Workload Characterization**
Systematic analysis of workload behavior, resource utilization, and performance characteristics.

---

## PCIe-Specific Terms

### **PCIe LPM (Link Power Management)**
PCIe power-saving mechanism that allows links to enter low-power states (L0s, L1, L2) when inactive. Residency data shows time spent in each power state.

### **PCIe Link Active**
Percentage of time the PCIe link is actively transferring data vs. in power-saving or idle states.

### **PCIe LTR (Latency Tolerance Reporting)**
Mechanism allowing PCIe devices to communicate their latency tolerance requirements to the system, enabling better power management decisions.

### **PCIe LTR Snoop**
Histogram showing the distribution of snoop latency values reported by PCIe devices, important for memory coherency and power optimization.

### **NVM (Non-Volatile Memory)**
Refers to PCIe-connected storage devices (typically NVMe SSDs) that are monitored for link power states and activity.

### **osSession.etl**
A key SocWatch ETL file containing OS-level telemetry. When this file is missing, only PCIe hardware-level data is available, resulting in "PCIe-only" SocWatch datasets.

---

## Additional Technical Terms

### **Schema**
The structure and format definition of input data or configuration files.

### **Validation**
Process of checking input data or configuration for correctness and completeness before parsing.

### **Sanitization**
Cleaning and normalizing input data to handle edge cases and ensure consistent parsing results.

---

*Last Updated: October 3, 2025*
