"""
ETL data parser implementation.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class ETLParser(BaseParser):
    """Parser for ETL (Extract, Transform, Load) data files."""
    
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
        etl_patterns = [
            r'.*etl.*',
            r'.*extract.*',
            r'.*transform.*',
            r'.*load.*',
            r'.*pipeline.*'
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in etl_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse ETL data file."""
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
            
            # Identify ETL-related columns
            etl_columns = self._identify_etl_columns(df.columns)
            
            # Extract timing information
            timing_info = self._extract_timing_info(df)
            
            # Calculate performance metrics
            performance = self._calculate_performance_metrics(df, etl_columns)
            
            # Prepare result
            result = {
                'data_type': 'etl',
                'columns': list(df.columns),
                'row_count': len(df),
                'etl_columns': etl_columns,
                'timing_info': timing_info,
                'performance_metrics': performance,
                'raw_data': df.to_dict('records')
            }
            
            self.logger.info(f"Parsed ETL data: {len(df)} rows, {len(etl_columns)} ETL columns")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse ETL data from {file_path}: {str(e)}")
    
    def _identify_etl_columns(self, columns: List[str]) -> List[str]:
        """Identify columns that contain ETL-related data."""
        etl_keywords = [
            'time', 'duration', 'throughput', 'rate', 'count', 'size',
            'extract', 'transform', 'load', 'process', 'status', 'error',
            'success', 'fail', 'latency', 'bandwidth'
        ]
        
        etl_columns = []
        for col in columns:
            col_lower = col.lower().replace('_', '').replace('-', '').replace(' ', '')
            if any(keyword in col_lower for keyword in etl_keywords):
                etl_columns.append(col)
        
        return etl_columns
    
    def _extract_timing_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract timing information from ETL data."""
        timing_info = {}
        
        # Look for timestamp or time columns
        time_columns = [col for col in df.columns if 'time' in col.lower() or 'timestamp' in col.lower()]
        
        if time_columns:
            timing_info['time_columns'] = time_columns
            
            # Try to parse timestamps and calculate duration
            for col in time_columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    timing_info[f'{col}_range'] = {
                        'start': str(df[col].min()),
                        'end': str(df[col].max()),
                        'duration': str(df[col].max() - df[col].min())
                    }
                except Exception:
                    # Skip if conversion fails
                    continue
        
        return timing_info
    
    def _calculate_performance_metrics(self, df: pd.DataFrame, etl_columns: List[str]) -> Dict[str, Any]:
        """Calculate performance metrics for ETL data."""
        metrics = {}
        
        for col in etl_columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                col_data = df[col].dropna()
                if not col_data.empty:
                    metrics[col] = {
                        'count': len(col_data),
                        'mean': float(col_data.mean()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'std': float(col_data.std()) if len(col_data) > 1 else 0.0,
                        'total': float(col_data.sum())
                    }
                    
                    # Additional ETL-specific metrics
                    if 'throughput' in col.lower() or 'rate' in col.lower():
                        metrics[col]['average_rate'] = float(col_data.mean())
                        metrics[col]['peak_rate'] = float(col_data.max())
        
        return metrics
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed ETL data."""
        required_keys = ['data_type', 'columns', 'row_count']
        
        # Check required keys
        if not all(key in data for key in required_keys):
            return False
        
        # Check data type
        if data['data_type'] != 'etl':
            return False
        
        # Check if we have some data
        if data['row_count'] <= 0:
            return False
        
        return True