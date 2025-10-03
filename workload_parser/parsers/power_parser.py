"""
Enhanced Power Parser with DAQ target support.
Based on the original power_summary_parser.py but with modern architecture.
"""

import re
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class PowerParser(BaseParser):
    """Enhanced parser for power consumption data files with DAQ target support."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = self.config.get('delimiter', ',')
        self.skip_rows = self.config.get('skip_rows', 0)
        self.encoding = self.config.get('encoding', 'utf-8')
        self.daq_targets = self.config.get('daq_targets', {})
        self.average_column = self.config.get('average_column', 'Average')
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check file extension
        if file_path.suffix.lower() not in ['.csv', '.txt']:
            return False
        
        # Check filename patterns (from old project)
        filename_lower = file_path.name.lower()
        power_patterns = [
            r'.*power.*summary.*',
            r'.*pacs-summary.*',
            r'.*power.*',
            r'.*pwr.*',
            r'.*energy.*',
            r'.*watt.*',
            r'.*daq.*'
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in power_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse power data file with DAQ target mapping."""
        try:
            self.logger.info(f"Parsing power file: {file_path}")
            
            # Read the CSV file with UTF-8 BOM handling (from old project)
            df = pd.read_csv(
                file_path,
                delimiter=self.delimiter,
                skiprows=self.skip_rows,
                encoding='utf-8-sig',  # Handle BOM
                low_memory=False
            )
            
            if df.empty:
                raise ParsingError(f"Empty CSV file: {file_path}")
            
            # Validate required columns
            if self.average_column not in df.columns:
                raise ParsingError(f"Required column '{self.average_column}' not found in {file_path}")
            
            # Extract power data based on DAQ targets (from old project logic)
            power_data = self._extract_power_data(df)
            
            # Calculate derived metrics
            derived_metrics = self._calculate_derived_metrics(power_data)
            power_data.update(derived_metrics)
            
            # Build result
            result = {
                'power_data': power_data,
                'file_info': {
                    'path': str(file_path)
                }
            }
            
            self.logger.info(f"Successfully parsed power data: {len(power_data)} metrics extracted")
            return result
            
        except Exception as e:
            error_msg = f"Error parsing power file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg) from e
    
    def _extract_power_data(self, df) -> Dict[str, float]:
        """Extract ALL power data from the power summary file."""
        from collections import OrderedDict
        power_data = OrderedDict()
        
        # Convert DataFrame to dictionary for easier searching
        rows_dict = {}
        for _, row in df.iterrows():
            rail_name = str(row.iloc[0]).strip()  # First column is rail name
            rows_dict[rail_name] = row
        
        # Extract ALL metrics from the power summary file
        p_soc = 0
        for rail_name, row in rows_dict.items():
            try:
                value = float(row[self.average_column])
                power_data[rail_name] = value
                
                # Track SOC power for energy calculation
                if 'P_SOC' in rail_name or 'P_MCP' in rail_name:
                    p_soc = value
                    
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Could not extract value for {rail_name}: {e}")
                power_data[rail_name] = -1
        
        # Store SOC power for energy calculations
        if p_soc > 0:
            power_data['_soc_power'] = p_soc
            
        return power_data
    
    def _calculate_derived_metrics(self, power_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived metrics like energy (from old project logic)."""
        derived = {}
        
        # Calculate total energy if SOC power and runtime are available
        soc_power = power_data.get('_soc_power', 0)
        runtime = power_data.get('Run Time', 0)
        
        if soc_power > 0 and runtime > 0:
            # Energy in Joules (Power in Watts * Time in seconds)
            derived['Energy (J)'] = soc_power * runtime
            self.logger.debug(f"Calculated energy: {derived['Energy (J)']} J")
        
        # Calculate P_SOC+MEMORY if individual components are available
        soc_components = ['P_VCC_PCORE', 'P_VCC_ECORE', 'P_VCCSA', 'P_VCCGT']
        memory_components = ['P_VDDQ', 'P_VDD2H', 'P_VDD2L']
        
        soc_total = sum(power_data.get(comp, 0) for comp in soc_components if power_data.get(comp, -1) > 0)
        memory_total = sum(power_data.get(comp, 0) for comp in memory_components if power_data.get(comp, -1) > 0)
        
        if soc_total > 0 and memory_total > 0:
            derived['P_SOC+MEMORY'] = soc_total + memory_total
        
        return derived
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed power data."""
        if not super().validate_data(data):
            return False
        
        power_data = data.get('power_data', {})
        if not power_data:
            return False
        
        # Check if at least some DAQ targets were found
        valid_measurements = sum(1 for v in power_data.values() if isinstance(v, (int, float)) and v >= 0)
        
        return valid_measurements > 0


class PowerTraceParser(BaseParser):
    """Parser for power trace files (detailed time-series data)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.sample_rate = self.config.get('sample_rate', 1000)  # Hz
        self.max_samples = self.config.get('max_samples', 100000)  # Limit for memory
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle trace files."""
        filename_lower = file_path.name.lower()
        trace_patterns = [
            r'.*pacs-traces.*',
            r'.*trace.*\.csv',
            r'.*_sr\.csv',  # Sample rate files
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in trace_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse power trace file."""
        try:
            self.logger.info(f"Parsing power trace file: {file_path}")
            
            # Read trace data
            df = pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
            
            if df.empty:
                raise ParsingError(f"Empty trace file: {file_path}")
            
            # Limit samples for memory efficiency
            if len(df) > self.max_samples:
                self.logger.warning(f"Trace file has {len(df)} samples, limiting to {self.max_samples}")
                df = df.head(self.max_samples)
            
            # Calculate basic statistics for each column
            trace_stats = {}
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    trace_stats[col] = {
                        'mean': float(df[col].mean()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'std': float(df[col].std())
                    }
            
            result = {
                'trace_stats': trace_stats,
                'file_info': {
                    'path': str(file_path)
                }
            }
            
            self.logger.info(f"Successfully parsed trace data: {len(df)} samples, {len(trace_stats)} metrics")
            return result
            
        except Exception as e:
            error_msg = f"Error parsing trace file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg) from e