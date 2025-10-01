"""
SocWatch data parser implementation.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


def cpu_model_table(table_data: List[List[str]]) -> Dict[str, Any]:
    """Parse CPU model table."""
    data = {}
    for line in table_data:
        if len(line) > 0 and '=' in line[0]:
            items = line[0].split("=")
            if len(items) > 1:
                key = items[0].split("/")[1].strip() if "/" in items[0] else items[0].strip()
                data[key] = items[-1].strip()
    return data


def one_line_colon_separator(table_data: List[List[str]]) -> Dict[str, Any]:
    """Parse single line colon-separated table."""
    data = {}
    for line in table_data:
        if len(line) > 0 and ':' in line[0]:
            items = line[0].split(":")
            if len(items) >= 2:
                key = items[0].strip()
                value = items[-1].strip()
                # Try to convert to number if possible
                try:
                    if '.' in value:
                        data[key] = float(value)
                    else:
                        data[key] = int(value)
                except ValueError:
                    data[key] = value
    return data


def temp_avr_table(table_data: List[List[str]], label: str) -> Dict[str, Any]:
    """Parse temperature average table."""
    data = {}
    for index, line in enumerate(table_data):
        if len(line) >= 5:
            if index == 0:
                data[label] = line[4]
            else:
                key = line[0].split("/")[-1] if "/" in line[0] else line[0]
                try:
                    data[key] = round(float(line[4]), 2)
                except (ValueError, IndexError):
                    data[key] = line[4] if len(line) > 4 else ''
    return data


def bw_total_avr(table_data: List[List[str]], label: str) -> Dict[str, Any]:
    """Parse bandwidth total average table."""
    if table_data and len(table_data) > 0:
        last_row = table_data[-1]
        if len(last_row) >= 3:
            try:
                value = round(float(last_row[2]), 2)
            except ValueError:
                value = last_row[2]
            return {f"{label}_AvrRt(MB/s)": value}
    return {f"{label}_AvrRt(MB/s)": 0}


def core_residency_table(table_data: List[List[str]]) -> Dict[str, Any]:
    """Parse core residency table."""
    data = {}
    if len(table_data) >= 2:
        header_row = table_data[0]
        data_row = table_data[1]
        
        # First column header and data
        if len(header_row) > 0 and len(data_row) > 0:
            data[header_row[0]] = data_row[0]
        
        # Process remaining columns
        for index in range(1, len(header_row)):
            if index >= len(data_row):
                break
            key = header_row[index].split("/")[-1] if "/" in header_row[index] else header_row[index]
            if "(%)" not in key:
                break
            try:
                data[key] = round(float(data_row[index]), 2)
            except ValueError:
                data[key] = data_row[index]
    return data


def os_wakeups_table(table_data: List[List[str]]) -> Dict[str, Any]:
    """Parse OS wakeups table for Thread Wakeups (OS) / Processes by Platform Busy Duration."""
    data = {}
    for idx, line in enumerate(table_data):
        if len(line) >= 3:
            if idx == 0:
                key = "OS_wakeups"
                value = f"{line[1].split(' ')[0]} ({' '.join(line[2].split(' ')[:-1])})"
            elif idx == 1:
                key = "Rank"
                # Extract percentage from the data and add "Overall" prefix
                process_name = line[1].split(' ')[0]
                # Look for percentage in parentheses in the third column
                percentage_match = line[2].split('(')[-1].split(')')[0] if '(' in line[2] and ')' in line[2] else line[2]
                value = f"Overall ({process_name})"
            else:
                # For Thread Wakeups (OS): Join Rank.ProcessName with CPU%(Platform) in parentheses
                rank = line[0] if line[0] else f"Entry_{idx}"
                
                # Extract process name (remove PID from process name)
                process_name_with_pid = line[1] if len(line) > 1 else ""
                # Remove PID part - typically in format "ProcessName (PID)"
                if '(' in process_name_with_pid and ')' in process_name_with_pid:
                    process_name = process_name_with_pid.split('(')[0].strip()
                else:
                    process_name = process_name_with_pid.split(' ')[0] if process_name_with_pid else ""
                
                # Extract CPU % (Platform) from 3rd column
                cpu_platform = line[2] if len(line) > 2 else ""
                
                key = rank
                value = f"{rank}.{process_name} ({cpu_platform})"
            data[key] = value
    return data


def core_freq_avr_table(table_data: List[List[str]], key_idx: int = 0, value_idx: int = 1) -> Dict[str, Any]:
    """Parse core frequency average table."""
    data = {}
    if len(table_data) > 0 and len(table_data[0]) > max(key_idx, value_idx):
        # Header row
        data[table_data[0][key_idx]] = table_data[0][value_idx]
        
        # Data rows
        for index in range(1, len(table_data)):
            line = table_data[index]
            if len(line) > max(key_idx, value_idx):
                key = line[key_idx].split("/")[2] if "/" in line[key_idx] and len(line[key_idx].split("/")) > 2 else line[key_idx]
                value = line[value_idx]
                try:
                    data[key] = int(float(value))
                except ValueError:
                    data[key] = value
    return data


def default_residency_table(table_data: List[List[str]], key_idx: int = 0, value_idx: int = 1) -> Dict[str, Any]:
    """Parse default residency table format."""
    data = {}
    for idx, line in enumerate(table_data):
        if len(line) > max(key_idx, value_idx):
            key = line[key_idx]
            # Handle P-state tables by removing decimal part
            if "_Pstate" in key and idx > 0 and "." in key:
                key = key.split(".")[0]
            
            value = line[value_idx]
            try:
                data[key] = round(float(value), 2)
            except ValueError:
                data[key] = value
    return data


def bucketized_table(table_data: List[List[str]], key_idx: int = 0, value_idx: int = 1, buckets: List[str] = None, table_label: str = None) -> Dict[str, Any]:
    """Parse bucketized table with frequency ranges for NOC, NPU, and iGFX tables."""
    
    # For bucketized tables, we only want to return the bucketed data, not the original raw data
    if not buckets:
        # If no buckets provided, fall back to original behavior
        data = {}
        for idx, line in enumerate(table_data):
            if len(line) > max(key_idx, value_idx):
                key = line[key_idx].strip()
                value = line[value_idx].strip()
                data[key] = value
        return data
    
    # Initialize bucketized data structure
    bucketized_data = {bucket: 0.0 for bucket in buckets}
    
    # Process each line of table data (skip header row)
    for idx, line in enumerate(table_data):
        if idx == 0:  # Skip header row
            continue
            
        if len(line) > max(key_idx, value_idx):
            key = line[key_idx].strip()
            value = line[value_idx].strip()
                
            try:
                # Convert frequency to float for proper comparison
                freq = float(key)
                numeric_value = float(value)
            except (ValueError, TypeError):
                # Skip non-numeric data
                continue
            
            # Check each bucket for frequency matches
            matched = False
            for bucket in buckets:
                if "-" in bucket:
                    # Range bucket: accumulate values for frequencies in range
                    try:
                        ranges = bucket.split("-")
                        if len(ranges) == 2:
                            min_freq = float(ranges[0])
                            max_freq = float(ranges[1])
                            if min_freq <= freq <= max_freq:
                                bucketized_data[bucket] += numeric_value
                                matched = True
                                break  # Found the bucket, no need to check others
                    except (ValueError, TypeError):
                        continue
                else:
                    # Single frequency bucket: direct copy if exact match
                    try:
                        bucket_freq = float(bucket)
                        if freq == bucket_freq:
                            bucketized_data[bucket] = numeric_value
                            matched = True
                            break  # Found exact match, no need to check others
                    except (ValueError, TypeError):
                        continue
    
    # Return only bucketized results with table-specific header
    result_data = {}
    
    # Determine the appropriate percentage label based on table type
    if table_label == 'NPU_Pstate':
        percentage_label = "NPU (%)"
    elif table_label == 'NoC_Pstate':
        percentage_label = "NOC (%)"
    elif table_label == 'iGFX_Pstate':
        percentage_label = "IGFX (%)"
    else:
        percentage_label = "Frequency Residency (%)"  # fallback
    
    result_data["Frequency Bucket (MHz)"] = percentage_label
    
    # Add bucketized data with proper formatting
    for bucket in buckets:
        accumulated_value = bucketized_data[bucket]
        # Round accumulated values to 2 decimal places
        formatted_value = round(accumulated_value, 2)
        result_data[bucket] = formatted_value
    
    return result_data


def socwatch_table_type_checker(table_data: List[List[str]], label: str, core_type: Dict[str, str] = None, 
                                soc_target: Dict[str, Any] = None, tdic: Dict[str, Any] = None) -> Dict[str, Any]:
    """Classify and parse SocWatch tables based on their labels using specialized parsing functions."""
    if label == 'CPU_model':
        return cpu_model_table(table_data)
    elif label in ['Core_Cstate', 'ACPI_Cstate']:
        return core_residency_table(table_data)
    elif label == 'OS_wakeups':
        return os_wakeups_table(table_data)
    elif label == 'CPU_Pavr':
        return core_freq_avr_table(table_data, 0, 1)
    elif label == 'CPU_Pstate':
        # Note: More complex parsing for per-core vs combined would need core_type parameter
        return default_residency_table(table_data, 0, 1)
    elif label == 'DC_count':
        return one_line_colon_separator(table_data)
    elif label in ['DDR_BW', 'IO_BW', 'VC1_BW', 'NPU_BW', 'Media_BW', 'IPU_BW', 'CCE_BW', 'GT_BW', 'D2D_BW']:
        return bw_total_avr(table_data, label)
    elif label in ['CPU_temp', 'SoC_temp']:
        return temp_avr_table(table_data, label)
    elif label == 'PMC+SLP_S0':
        return default_residency_table(table_data, 0, 2)
    elif label in ['NPU_Pstate', 'NoC_Pstate', 'iGFX_Pstate']:
        # Check if config has buckets defined for this table
        if soc_target and 'buckets' in soc_target:
            # Config HAS buckets defined, so DO bucketize using config buckets
            return bucketized_table(table_data, 0, 1, soc_target['buckets'], label)
        else:
            # Config does NOT have buckets, so DON'T bucketize - just return all frequencies
            return default_residency_table(table_data, 0, 1)
    elif soc_target and 'buckets' in soc_target:
        # For other tables that have buckets in config
        return bucketized_table(table_data, 0, 1, soc_target['buckets'], label)
    else:
        return default_residency_table(table_data, 0, 1)


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
                'socwatch_data': target_metrics,
                'file_info': {
                    'path': str(file_path)
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
                # Store as dictionary with metadata and data (headers integrated into data)
                table_dict = {
                    'table_key': target_key,
                    'table_info': target,
                    'data': table_data
                }
                socwatch_tables.append(table_dict)
                self.logger.debug(f"Extracted {len(table_data)} entries for {target_key}")
        
        return socwatch_tables
    

    

    
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
        """Extract table data after finding the lookup text using specialized table classification."""
        target_key = target['key']
        
        # Start from the line after the lookup text
        current_idx = lookup_idx + 1
        
        # Collect raw table lines until empty line or end of file
        raw_table_lines = []
        while current_idx < len(lines):
            line = lines[current_idx].strip()
            
            # Empty line marks end of table
            if not line:
                break
            
            # Skip separator lines (only dashes)
            if line.startswith('---') or line.replace('-', '').replace(' ', '') == '':
                current_idx += 1
                continue
            
            # Add line to raw table data
            # Split by comma and clean up each part
            parts = [part.strip().strip('"') for part in line.split(',') if part.strip()]
            if parts:  # Only add non-empty rows
                raw_table_lines.append(parts)
            
            current_idx += 1
        
        # If no table data found, return empty dict
        if not raw_table_lines:
            return {}
        
        # Use the table classification system to parse the raw data
        try:
            # Get any additional context needed for specialized parsing
            core_type = getattr(self, '_core_type_cache', None)  # Could be set from CPU_model table
            soc_target = target  # The target config contains bucket info if needed
            tdic = getattr(self, '_parsing_context', {})  # Additional parsing context
            
            # Apply specialized parsing based on table type
            parsed_data = socwatch_table_type_checker(
                raw_table_lines, 
                target_key, 
                core_type, 
                soc_target, 
                tdic
            )
            
            # Cache core type information if this is a CPU_model table
            if target_key == 'CPU_model' and parsed_data:
                self._core_type_cache = parsed_data
            
            return parsed_data
            
        except Exception as e:
            self.logger.warning(f"Failed to parse {target_key} table with specialized parser, falling back to generic: {e}")
            # Fallback to simple key-value parsing
            fallback_data = {}
            for row in raw_table_lines:
                if len(row) >= 2:
                    fallback_data[row[0]] = row[1]
            return fallback_data
    

    

    

    

    

    

    
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
                # Check if this is a specialized parsed table (from table classification)
                # Specialized tables already have proper key-value structure and don't need extra headers
                is_specialized_table = self._is_specialized_table_format(table_data, table_key)
                
                if not is_specialized_table:
                    # Add table header only for non-specialized tables
                    header_text = self._get_table_header_text(table_key, target_info, table_data)
                    header_key = f"{header_text}        {table_key}"
                    target_metrics[header_key] = self._get_table_header_value(table_key, table_data)
                
                # Add all data rows for this table before moving to the next table
                # This ensures complete grouping of each table's data
                for metric_key, metric_value in table_data.items():
                    data_key = f"{metric_key}        {table_key}"
                    target_metrics[data_key] = metric_value
        
        return target_metrics
    
    def _is_specialized_table_format(self, table_data: Dict[str, Any], table_key: str) -> bool:
        """Check if table data has been processed by specialized parsing functions."""
        # All tables processed by the new classification system should be considered specialized
        # This prevents adding redundant headers for any table that went through socwatch_table_type_checker
        
        # Check if this looks like output from specialized parsing functions
        keys = list(table_data.keys())
        
        # If table is empty, not specialized
        if not keys:
            return False
        
        # Check for bandwidth tables - they have a specific format with AvrRt in the key
        if table_key.endswith('_BW'):
            return len(keys) == 1 and 'AvrRt(MB/s)' in str(keys[0])
        
        # Check for temperature tables - they have component names as keys
        if table_key in ['CPU_temp', 'SoC_temp']:
            return len(keys) > 1 and table_key in str(keys[0])
        
        # Check for CPU model table - has specific key patterns
        if table_key == 'CPU_model':
            return any(key for key in keys if any(term in str(key).lower() for term in ['processor', 'cpu', 'family', 'model', 'stepping']))
        
        # Check for OS wakeups table - has specific format
        if table_key == 'OS_wakeups':
            return 'OS_wakeups' in keys
        
        # Check for DC count table - colon separated single line
        if table_key == 'DC_count':
            return len(keys) >= 1 and not any('(' in str(key) and ')' in str(key) for key in keys[:2])
        
        # Check for bucketized P-state tables - they have "Frequency Bucket (MHz)" header
        if table_key in ['NPU_Pstate', 'NoC_Pstate', 'iGFX_Pstate']:
            return any('Frequency Bucket (MHz)' in str(key) for key in keys)
        
        # For C-state and P-state tables, check if they have proper structure
        if table_key in ['Core_Cstate', 'ACPI_Cstate', 'PKG_Cstate', 'CPU_Pstate', 'CPU_Pavr']:
            # Specialized tables don't have generic header patterns like "Component (Unit)"
            first_key = str(keys[0])
            
            # If first key contains generic patterns, it might not be specialized
            generic_patterns = ['Component', 'State', 'Frequency', 'Residency', 'Time']
            has_generic_pattern = any(pattern in first_key for pattern in generic_patterns)
            
            # If first key has units in parentheses and generic patterns, might not be specialized
            if has_generic_pattern and '(' in first_key and ')' in first_key:
                return False
            
            # Otherwise, assume it's been specialized
            return True
        
        # For other table types, assume they've been processed by specialized functions
        # if they don't look like raw CSV headers
        first_key = str(keys[0])
        
        # Raw CSV headers typically have units in parentheses and descriptive names
        looks_like_raw_header = ('(' in first_key and ')' in first_key and 
                                any(term in first_key for term in ['Component', 'State', 'Frequency', 'Residency', 'Percentage']))
        
        # If it looks like a raw header, it probably wasn't specialized
        return not looks_like_raw_header
    
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
                'pcie_data': pcie_data,
                'file_info': {
                    'path': str(file_path)
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
        
        # Check if we have pcie data
        pcie_data = data.get('pcie_data', {})
        return isinstance(pcie_data, dict)