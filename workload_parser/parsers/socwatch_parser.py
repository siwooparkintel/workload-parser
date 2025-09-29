"""
SocWatch data parser implementation.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class SocwatchParser(BaseParser):
    """Parser for SocWatch monitoring data files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = self.config.get('delimiter', ',')
        self.skip_rows = self.config.get('skip_rows', 0)
        self.encoding = self.config.get('encoding', 'utf-8')
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file using folder-based detection."""
        # Check file extension
        if file_path.suffix.lower() != '.csv':
            return False
        
        # Get the parent folder
        parent_folder = file_path.parent
        filename = file_path.name
        
        # Skip WakeupAnalysis files for now (as per user request)
        if 'wakeupanalysis' in filename.lower():
            return False
        
        # Check for Socwatch ETL files in the same folder
        required_etl_files = [
            '_extraSession.etl',
            '_hwSession.etl', 
            '_infoSession.etl'
        ]
        
        # Check if all required ETL files exist
        etl_files_found = []
        workload_prefix = None
        
        for etl_file in parent_folder.glob('*.etl'):
            etl_name = etl_file.name
            for required_suffix in required_etl_files:
                if etl_name.endswith(required_suffix):
                    etl_files_found.append(required_suffix)
                    # Extract workload prefix (everything before the _xxxSession.etl)
                    workload_prefix = etl_name.replace(required_suffix, '')
                    break
        
        # Must have all 3 required ETL files
        if len(set(etl_files_found)) < 3:
            return False
        
        # Check if this CSV file matches the workload prefix
        if workload_prefix and filename.startswith(workload_prefix) and filename.endswith('.csv'):
            return True
        
        return False
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse SocWatch data file to extract all summary tables in config order."""
        try:
            self.logger.info(f"Parsing Socwatch file: {file_path}")
            
            # Read the file as text to extract specific sections
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Extract all tables as a list of dictionaries in config order
            socwatch_tables = self._parse_socwatch_content(content)
            
            # Flatten the tables for Excel reporting while maintaining grouping and order
            target_metrics = self._extract_target_metrics(socwatch_tables)
            
            # Prepare result
            result = {
                'data_type': 'socwatch',
                'parser': 'SocwatchParser',
                'socwatch_data': target_metrics,
                'file_info': {
                    'path': str(file_path),
                    'content_size': len(content)
                },
                'metadata': {
                    'tables_found': len(socwatch_tables),
                    'targets_found': len(target_metrics)
                }
            }
            
            self.logger.info(f"Successfully parsed Socwatch data: {len(target_metrics)} metrics extracted")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse SocWatch data from {file_path}: {str(e)}")
    
    def _parse_socwatch_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse Socwatch content to extract all summary tables as a list of dictionaries in config order."""
        socwatch_tables = []
        lines = content.split('\n')
        
        # Load socwatch targets from config in their defined order
        socwatch_targets = self._load_socwatch_targets()
        
        # Process each target in the order defined in config
        for target in socwatch_targets:
            lookup_text = target['lookup']
            target_key = target['key']
            
            # Find the lookup text in the file
            table_start_idx = -1
            for i, line in enumerate(lines):
                if lookup_text in line:
                    table_start_idx = i
                    break
            
            if table_start_idx == -1:
                self.logger.debug(f"Table lookup '{lookup_text}' not found for {target_key}")
                continue
            
            # Extract table data starting after the lookup line
            table_data = self._extract_table_data(lines, table_start_idx, target)
            if table_data:
                # Store as dictionary with metadata
                table_dict = {
                    'table_key': target_key,
                    'table_info': target,
                    'data': table_data
                }
                socwatch_tables.append(table_dict)
                self.logger.debug(f"Extracted {len(table_data)} entries for {target_key}")
        
        return socwatch_tables
    
    def _extract_os_wakeups(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract OS wakeups data from Socwatch content."""
        os_wakeups = []
        
        # Find the "Processes by Platform Busy Duration" section
        in_process_section = False
        
        for line in lines:
            line = line.strip()
            
            # Look for the process section header
            if "Processes by Platform Busy Duration" in line:
                in_process_section = True
                continue
            
            # Skip header lines and separators
            if in_process_section and (line.startswith('Rank,') or line.startswith('----') or not line):
                continue
            
            # Process data lines
            if in_process_section and ',' in line:
                try:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 3:
                        # Extract rank, process name, and CPU percentage
                        rank = parts[0]
                        process_name = parts[1]
                        cpu_percent = parts[2]
                        
                        # Clean up the data
                        if rank and process_name and cpu_percent:
                            # Remove quotes and extra spaces
                            process_name = process_name.strip('"')
                            cpu_percent = cpu_percent.strip('"')
                            
                            try:
                                cpu_float = float(cpu_percent)
                                os_wakeups.append({
                                    'rank': rank,
                                    'process': process_name,
                                    'cpu_percent': cpu_float
                                })
                            except ValueError:
                                continue
                
                except Exception:
                    continue
            
            # Stop when we reach the legend or next section
            if in_process_section and ("Legend:" in line or "Complete list" in line):
                break
        
        return os_wakeups
    
    def _extract_core_states(self, lines: List[str]) -> Dict[str, str]:
        """Extract Core C-State data from Socwatch content."""
        core_states = {}
        
        # Look for core state information in various sections
        # Since this varies by platform, start with default values
        # This can be enhanced based on actual Socwatch file format
        for i in range(4):  # Default to 4 cores
            core_states[f'Core_{i}'] = 'C'
        
        # Look for specific core state patterns in the content
        for line in lines:
            line = line.strip()
            
            # Look for core state patterns - this would need customization
            # based on the actual format in your Socwatch files
            if 'Core' in line and ('C-State' in line or 'Residency' in line):
                # Extract actual core state information if found
                # For now, use enhanced state indicators
                for i in range(8):  # Check up to 8 cores
                    core_states[f'Core_{i}'] = 'LNC'  # Low Normal Core state
                break
        
        return core_states
    
    def _load_socwatch_targets(self) -> List[Dict[str, Any]]:
        """Load socwatch targets from enhanced config."""
        try:
            from pathlib import Path
            import json
            
            config_path = Path('config/enhanced_parser_config.json')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                return config.get('socwatch_targets', [])
            else:
                self.logger.warning("Enhanced config not found, using default targets")
                return self._get_default_targets()
        except Exception as e:
            self.logger.warning(f"Could not load socwatch targets from config: {e}")
            return self._get_default_targets()
    
    def _get_default_targets(self) -> List[Dict[str, Any]]:
        """Get default socwatch targets if config is not available."""
        return [
            {"key": "OS_wakeups", "lookup": "Processes by Platform Busy Duration", "description": "OS wakeup events"},
            {"key": "Core_Cstate", "lookup": "Core C-State Summary: Residency (Percentage and Time)", "description": "Core C-state residency"},
            {"key": "PKG_Cstate", "lookup": "Platform Monitoring Technology CPU Package C-States Residency Summary: Residency (Percentage and Time)", "description": "CPU package C-state residency"},
            {"key": "CPU_temp", "lookup": "Temperature Metrics Summary - Sampled: Min/Max/Avg", "description": "CPU temperature"},
        ]
    
    def _extract_table_data(self, lines: List[str], lookup_idx: int, target: Dict[str, Any]) -> Dict[str, Any]:
        """Extract table data after finding the lookup text, skipping headers and separators."""
        table_data = {}
        target_key = target['key']
        
        # Start from the line after the lookup text
        current_idx = lookup_idx + 1
        
        # Skip any header lines and separator lines (lines with only dashes)
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            if not line:  # Empty line - no table data found
                return {}
            
            # Skip header lines (typically contain column names) and separator lines
            if (line.startswith('---') or line.replace('-', '').replace(' ', '') == '' or 
                'Percentage' in line or 'Residency' in line or 'Time' in line or
                'Average' in line or 'Total' in line or 'Min/Max/Avg' in line):
                current_idx += 1
                continue
            else:
                # This should be the beginning of actual data
                break
        
        # Extract data rows until empty line
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            
            # Empty line marks end of table
            if not line:
                break
            
            # Parse the data line: first column is label, second column is value
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 2:
                data_label = parts[0].strip('"')  # Remove quotes if present
                data_value = parts[1].strip('"')  # Second column is the target data
                
                # Clean up the data
                if data_label and data_value:
                    table_data[data_label] = data_value
            
            current_idx += 1
        
        return table_data
    
    def _parse_os_wakeups_table(self, table_lines: List[str]) -> Dict[str, Any]:
        """Parse OS wakeups table."""
        wakeups_data = {}
        
        for i, line in enumerate(table_lines):
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 3:
                if i == 0:
                    # Header or first data row
                    wakeups_data['OS_wakeups'] = f"{parts[1]} ({parts[2]})"
                else:
                    # Process entries
                    rank = parts[0] if parts[0].isdigit() else str(i)
                    process_name = parts[1].split('(')[0].strip() if '(' in parts[1] else parts[1]
                    cpu_percent = parts[2].replace('%', '').strip()
                    wakeups_data[rank] = f"{process_name} ({cpu_percent}%)"
        
        return wakeups_data
    
    def _parse_temperature_table(self, table_lines: List[str], key: str) -> Dict[str, Any]:
        """Parse temperature table."""
        temp_data = {}
        
        for line in table_lines:
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 5:
                # Temperature format: Component, Min, Max, Avg, Unit
                component = parts[0]
                avg_temp = parts[4] if len(parts) > 4 else parts[3]
                temp_data[component] = avg_temp
        
        return temp_data
    
    def _parse_cstate_table(self, table_lines: List[str], key: str) -> Dict[str, Any]:
        """Parse C-state residency table."""
        cstate_data = {}
        
        for line in table_lines:
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 2:
                state_name = parts[0]
                residency = parts[1]
                if '%' in residency or 'Residency' in residency:
                    cstate_data[state_name] = residency.replace('%', '').strip()
        
        return cstate_data
    
    def _parse_pstate_table(self, table_lines: List[str], key: str, buckets: List[str]) -> Dict[str, Any]:
        """Parse P-state table with optional bucketing."""
        pstate_data = {}
        
        for line in table_lines:
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 2:
                freq_or_state = parts[0]
                residency = parts[1]
                pstate_data[freq_or_state] = residency
        
        # Apply bucketing if specified
        if buckets:
            pstate_data = self._apply_bucketing(pstate_data, buckets)
        
        return pstate_data
    
    def _parse_bandwidth_table(self, table_lines: List[str], key: str) -> Dict[str, Any]:
        """Parse bandwidth table."""
        bw_data = {}
        
        for line in table_lines:
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 3:
                # Usually has component, rate, total
                component = parts[0]
                rate = parts[2] if len(parts) > 2 else parts[1]  # Average rate
                bw_data[f"{key}_AvrRt(MB/s)"] = rate
        
        return bw_data
    
    def _parse_default_table(self, table_lines: List[str], key: str) -> Dict[str, Any]:
        """Parse default residency table."""
        default_data = {}
        
        for line in table_lines:
            parts = [part.strip() for part in line.split(',') if part.strip()]
            if len(parts) >= 2:
                state_name = parts[0]
                value = parts[1]
                default_data[state_name] = value
        
        return default_data
    
    def _apply_bucketing(self, data: Dict[str, Any], buckets: List[str]) -> Dict[str, Any]:
        """Apply bucketing to P-state data."""
        bucketed_data = {}
        
        for bucket in buckets:
            bucketed_data[bucket] = 0.0
        
        for state, value in data.items():
            if state.isdigit():
                freq = int(state)
                for bucket in buckets:
                    if '-' in bucket:
                        # Range bucket
                        range_parts = bucket.split('-')
                        if len(range_parts) == 2:
                            min_freq = int(range_parts[0])
                            max_freq = int(range_parts[1])
                            if min_freq <= freq <= max_freq:
                                bucketed_data[bucket] += float(value) if isinstance(value, str) and value.replace('.', '').isdigit() else 0
                    elif bucket == state:
                        # Exact match
                        bucketed_data[bucket] = float(value) if isinstance(value, str) and value.replace('.', '').isdigit() else 0
        
        return bucketed_data
    
    def _extract_target_metrics(self, socwatch_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metrics from parsed Socwatch tables list for Excel reporting, maintaining config order and grouping."""
        from collections import OrderedDict
        target_metrics = OrderedDict()
        
        # Process each table in the order they appear (which follows config order)
        for table_dict in socwatch_tables:
            table_key = table_dict['table_key']
            target_info = table_dict['table_info']
            table_data = table_dict['data']
            
            if isinstance(table_data, dict) and table_data:
                # Add table header
                header_text = self._get_table_header_text(table_key, target_info, table_data)
                header_key = f"{header_text}        {table_key}"
                target_metrics[header_key] = self._get_table_header_value(table_key, table_data)
                
                # Add all data rows for this table before moving to the next table
                # This ensures complete grouping of each table's data
                for metric_key, metric_value in table_data.items():
                    data_key = f"{metric_key}        {table_key}"
                    target_metrics[data_key] = metric_value
        
        return target_metrics
    
    def _get_table_header_text(self, table_key: str, target_info: Dict[str, Any], table_data: Dict[str, Any]) -> str:
        """Get appropriate table header text based on table type."""
        # Map table keys to their header descriptions based on sample Excel
        header_mapping = {
            'CPU_model': 'CPU_model',
            'PCH_SLP50': 'PCH SLP-S0 States',
            'S0ix_Substate': 'State',
            'PKG_Cstate': 'C-State',
            'Core_Cstate': 'C-State',
            'Core_Concurrency': '# Active Cores',
            'ACPI_Cstate': 'C-State',
            'OS_wakeups': 'OS_wakeups',
            'CPU-iGPU': 'CPU/Package_0 Residency (%)',
            'CPU_Pavr': 'CPU ID',
            'CPU_Pstate': 'P-State',
            'RC_Cstate': 'C-State',
            'DDR_BW': 'DDR_BW_AvrRt(MB/s)',
            'IO_BW': 'IO_BW_AvrRt(MB/s)',
            'VC1_BW': 'VC1_BW_AvrRt(MB/s)',
            'NPU_BW': 'NPU_BW_AvrRt(MB/s)',
            'Media_BW': 'Media_BW_AvrRt(MB/s)',
            'IPU_BW': 'IPU_BW_AvrRt(MB/s)',
            'CCE_BW': 'CCE_BW_AvrRt(MB/s)',
            'GT_BW': 'GT_BW_AvrRt(MB/s)',
            'D2D_BW': 'D2D_BW_AvrRt(MB/s)',
            'CPU_temp': 'Component Name',
            'SoC_temp': 'Component Name',
            'NPU_Dstate': 'State',
            'PMC+SLP_S0': 'PCH IP Blocks',
            'Media_Cstate': 'C-State',
            'NPU_Pstate': 'Frequency (MHz)',
            'MEMSS_Pstate': 'Frequency (MHz)',
            'NoC_Pstate': 'Frequency (MHz)',
            'iGFX_Pstate': 'Frequency (MHz)'
        }
        
        return header_mapping.get(table_key, table_key)
    
    def _get_table_header_value(self, table_key: str, table_data: Dict[str, Any]) -> str:
        """Get appropriate table header value based on table type."""
        # Map table keys to their header values based on sample Excel
        value_mapping = {
            'CPU_model': 'CPU_model',
            'PCH_SLP50': 'PCH Residency (%)',
            'S0ix_Substate': 'Residency (%)',
            'PKG_Cstate': 'Package Residency ()',
            'Core_Cstate': 'CPU/Package_0/Core_0 Residency ()',
            'Core_Concurrency': 'Time Active (%)',
            'ACPI_Cstate': 'CPU/Package_0/Core_0 Residency ()',
            'OS_wakeups': 'Process Name (PID) (CPU % (Platform))',
            'CPU-iGPU': 'CPU/Package_0 Residency (%)',
            'CPU_Pavr': 'Average (MHz)',
            'CPU_Pstate': 'Frequency (MHz)',
            'RC_Cstate': 'iGPU/Graphics Residency ()',
            'CPU_temp': 'Time-weighted Avg (oC)',
            'SoC_temp': 'Time-weighted Avg (oC)',
            'NPU_Dstate': 'Residency (%)',
            'PMC+SLP_S0': 'Description',
            'Media_Cstate': 'Residency ()',
            'NPU_Pstate': 'NPU (%)',
            'MEMSS_Pstate': 'MEMSS (%)',
            'NoC_Pstate': 'NoC (%)',
            'iGFX_Pstate': 'iGFX (%)'
        }
        
        # For bandwidth tables, return the actual value
        if table_key.endswith('_BW'):
            return next(iter(table_data.values())) if table_data else '0.00'
        
        return value_mapping.get(table_key, 'Value')
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed Socwatch data."""
        if not super().validate_data(data):
            return False
        
        # Check data type
        if data.get('data_type') != 'socwatch':
            return False
        
        # Check if we have socwatch data
        socwatch_data = data.get('socwatch_data', {})
        if not isinstance(socwatch_data, dict):
            return False
        
        # Valid if we have any socwatch metrics extracted
        return len(socwatch_data) > 0


class PCIeParser(BaseParser):
    """Parser for PCIe-only Socwatch data (when _osSession.etl is missing)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = self.config.get('delimiter', ',')
        self.encoding = self.config.get('encoding', 'utf-8')
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this is a PCIe-only Socwatch file (missing _osSession.etl)."""
        # Check file extension
        if file_path.suffix.lower() != '.csv':
            return False
        
        # Get the parent folder
        parent_folder = file_path.parent
        filename = file_path.name
        
        # Skip WakeupAnalysis files
        if 'wakeupanalysis' in filename.lower():
            return False
        
        # Check for Socwatch ETL files in the same folder
        required_etl_files = [
            '_extraSession.etl',
            '_hwSession.etl', 
            '_infoSession.etl'
        ]
        
        # Check if required ETL files exist but _osSession.etl is missing
        etl_files_found = []
        workload_prefix = None
        has_os_session = False
        
        for etl_file in parent_folder.glob('*.etl'):
            etl_name = etl_file.name
            
            # Check for _osSession.etl
            if etl_name.endswith('_osSession.etl'):
                has_os_session = True
            
            # Check for other required ETL files
            for required_suffix in required_etl_files:
                if etl_name.endswith(required_suffix):
                    etl_files_found.append(required_suffix)
                    # Extract workload prefix
                    workload_prefix = etl_name.replace(required_suffix, '')
                    break
        
        # Must have the 3 required ETL files but NOT _osSession.etl
        if len(set(etl_files_found)) >= 3 and not has_os_session:
            # Check if this CSV file matches the workload prefix
            if workload_prefix and filename.startswith(workload_prefix) and filename.endswith('.csv'):
                return True
        
        return False
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse PCIe-only Socwatch data file."""
        try:
            self.logger.info(f"Parsing PCIe Socwatch file: {file_path}")
            
            # Read the CSV file as text to extract PCIe-specific data
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # Extract PCIe-specific metrics
            pcie_data = self._extract_pcie_metrics(content)
            
            # Prepare result
            result = {
                'data_type': 'pcie_socwatch',
                'parser': 'PCIeParser',
                'pcie_data': pcie_data,
                'file_info': {
                    'path': str(file_path),
                    'content_size': len(content)
                }
            }
            
            self.logger.info(f"Successfully parsed PCIe data: {len(pcie_data)} metrics extracted")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse PCIe data from {file_path}: {str(e)}")
    
    def _extract_pcie_metrics(self, content: str) -> Dict[str, Any]:
        """Extract PCIe-specific metrics from content."""
        pcie_data = {}
        
        # Look for PCIe-related sections in the content
        lines = content.split('\n')
        
        # Extract basic PCIe information for now
        # This can be enhanced based on actual PCIe data structure
        for line in lines:
            line = line.strip()
            if 'pcie' in line.lower() or 'pci express' in line.lower():
                # Extract PCIe-related data
                # For now, just record that PCIe data was found
                pcie_data['pcie_detected'] = True
                break
        
        # Add placeholder data structure for Excel generation
        if not pcie_data:
            pcie_data['pcie_detected'] = False
        
        return pcie_data
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed PCIe data."""
        if not super().validate_data(data):
            return False
        
        return data.get('data_type') == 'pcie_socwatch'