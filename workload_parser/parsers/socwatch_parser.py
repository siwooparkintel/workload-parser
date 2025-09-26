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
        """Check if this parser can handle the given file."""
        # Check file extension
        if file_path.suffix.lower() not in ['.csv', '.txt']:
            return False
        
        # Check filename patterns
        filename_lower = file_path.name.lower()
        socwatch_patterns = [
            r'.*socwatch.*',
            r'.*soc.*watch.*',
            r'.*system.*monitor.*',
            r'.*perf.*monitor.*'
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in socwatch_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse SocWatch data file."""
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
            
            # Identify SocWatch-related columns
            socwatch_columns = self._identify_socwatch_columns(df.columns)
            
            # Extract performance counters
            performance_counters = self._extract_performance_counters(df, socwatch_columns)
            
            # Calculate system metrics
            system_metrics = self._calculate_system_metrics(df, socwatch_columns)
            
            # Prepare result
            result = {
                'data_type': 'socwatch',
                'columns': list(df.columns),
                'row_count': len(df),
                'socwatch_columns': socwatch_columns,
                'performance_counters': performance_counters,
                'system_metrics': system_metrics,
                'raw_data': df.to_dict('records')
            }
            
            self.logger.info(f"Parsed SocWatch data: {len(df)} rows, {len(socwatch_columns)} monitoring columns")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse SocWatch data from {file_path}: {str(e)}")
    
    def _identify_socwatch_columns(self, columns: List[str]) -> List[str]:
        """Identify columns that contain SocWatch monitoring data."""
        socwatch_keywords = [
            'cpu', 'gpu', 'memory', 'mem', 'freq', 'frequency', 'util', 
            'utilization', 'load', 'temp', 'temperature', 'voltage', 'current',
            'counter', 'perf', 'performance', 'bandwidth', 'latency', 'cache',
            'instruction', 'cycle', 'branch', 'miss', 'hit'
        ]
        
        socwatch_columns = []
        for col in columns:
            col_lower = col.lower().replace('_', '').replace('-', '').replace(' ', '')
            if any(keyword in col_lower for keyword in socwatch_keywords):
                socwatch_columns.append(col)
        
        return socwatch_columns
    
    def _extract_performance_counters(self, df: pd.DataFrame, socwatch_columns: List[str]) -> Dict[str, Any]:
        """Extract performance counter information."""
        counters = {}
        
        # Group columns by category
        categories = {
            'cpu': ['cpu', 'processor', 'core'],
            'gpu': ['gpu', 'graphics'],
            'memory': ['memory', 'mem', 'ram'],
            'cache': ['cache', 'l1', 'l2', 'l3'],
            'frequency': ['freq', 'frequency', 'clock'],
            'utilization': ['util', 'utilization', 'load', 'usage']
        }
        
        for category, keywords in categories.items():
            category_columns = []
            for col in socwatch_columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in keywords):
                    category_columns.append(col)
            
            if category_columns:
                counters[category] = category_columns
        
        return counters
    
    def _calculate_system_metrics(self, df: pd.DataFrame, socwatch_columns: List[str]) -> Dict[str, Any]:
        """Calculate system performance metrics."""
        metrics = {}
        
        for col in socwatch_columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                col_data = df[col].dropna()
                if not col_data.empty:
                    metrics[col] = {
                        'count': len(col_data),
                        'mean': float(col_data.mean()),
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'std': float(col_data.std()) if len(col_data) > 1 else 0.0,
                        'median': float(col_data.median())
                    }
                    
                    # Calculate percentiles for performance analysis
                    metrics[col]['percentiles'] = {
                        'p25': float(col_data.quantile(0.25)),
                        'p75': float(col_data.quantile(0.75)),
                        'p90': float(col_data.quantile(0.90)),
                        'p95': float(col_data.quantile(0.95)),
                        'p99': float(col_data.quantile(0.99))
                    }
        
        return metrics
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed SocWatch data."""
        required_keys = ['data_type', 'columns', 'row_count']
        
        # Check required keys
        if not all(key in data for key in required_keys):
            return False
        
        # Check data type
        if data['data_type'] != 'socwatch':
            return False
        
        # Check if we have some data
        if data['row_count'] <= 0:
            return False
        
        return True