"""
Power data parser implementation.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class PowerParser(BaseParser):
    """Parser for power consumption data files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = self.config.get('delimiter', ',')
        self.skip_rows = self.config.get('skip_rows', 0)
        self.encoding = self.config.get('encoding', 'utf-8')
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check file extension
        if file_path.suffix.lower() not in ['.csv', '.txt']:
            return False
        
        # Check filename patterns
        filename_lower = file_path.name.lower()
        power_patterns = [
            r'.*power.*',
            r'.*pwr.*',
            r'.*energy.*',
            r'.*watt.*'
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in power_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse power data file."""
        try:
            # Read the CSV file
            df = pd.read_csv(
                file_path,
                delimiter=self.delimiter,
                skiprows=self.skip_rows,
                encoding=self.encoding,
                low_memory=False
            )
            
            # Basic validation
            if df.empty:
                raise ParsingError(f"Empty data file: {file_path}")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Identify power-related columns
            power_columns = self._identify_power_columns(df.columns)
            
            # Extract summary statistics
            summary = self._calculate_summary_stats(df, power_columns)
            
            # Prepare result
            result = {
                'data_type': 'power',
                'columns': list(df.columns),
                'row_count': len(df),
                'power_columns': power_columns,
                'summary_stats': summary,
                'raw_data': df.to_dict('records')  # Consider limiting size for large files
            }
            
            self.logger.info(f"Parsed power data: {len(df)} rows, {len(power_columns)} power columns")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse power data from {file_path}: {str(e)}")
    
    def _identify_power_columns(self, columns: List[str]) -> List[str]:
        """Identify columns that contain power data."""
        power_keywords = [
            'power', 'pwr', 'watt', 'w', 'energy', 'current', 'voltage', 
            'amp', 'milliwatt', 'mw', 'kilowatt', 'kw'
        ]
        
        power_columns = []
        for col in columns:
            col_lower = col.lower().replace('_', '').replace('-', '').replace(' ', '')
            if any(keyword in col_lower for keyword in power_keywords):
                power_columns.append(col)
        
        return power_columns
    
    def _calculate_summary_stats(self, df: pd.DataFrame, power_columns: List[str]) -> Dict[str, Any]:
        """Calculate summary statistics for power data."""
        summary = {}
        
        for col in power_columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                col_data = df[col].dropna()
                if not col_data.empty:
                    summary[col] = {
                        'count': len(col_data),
                        'mean': float(col_data.mean()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'std': float(col_data.std()) if len(col_data) > 1 else 0.0,
                        'total': float(col_data.sum())
                    }
        
        return summary
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed power data."""
        required_keys = ['data_type', 'columns', 'row_count']
        
        # Check required keys
        if not all(key in data for key in required_keys):
            return False
        
        # Check data type
        if data['data_type'] != 'power':
            return False
        
        # Check if we have some data
        if data['row_count'] <= 0:
            return False
        
        # Check if we found power columns
        if not data.get('power_columns'):
            self.logger.warning("No power columns identified in the data")
        
        return True