"""
Intel workload-specific parsers.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class PacsParser(BaseParser):
    """Parser for PACS (Power Analysis and Control System) data files."""
    
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
        
        # Check filename patterns for PACS files
        filename_lower = file_path.name.lower()
        pacs_patterns = [
            r'.*pacs.*',
            r'.*configuration.*\.csv',
            r'.*config.*\.csv',
            r'.*summary.*\.csv',
            r'.*traces.*\.csv'
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in pacs_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse PACS data file."""
        try:
            # Try different parsing approaches
            try:
                # First try standard CSV parsing
                df = pd.read_csv(
                    file_path,
                    delimiter=self.delimiter,
                    skiprows=self.skip_rows,
                    encoding=self.encoding,
                    low_memory=False
                )
            except Exception:
                # If that fails, try with different delimiters
                for delimiter in [',', '\t', ';', '|']:
                    try:
                        df = pd.read_csv(
                            file_path,
                            delimiter=delimiter,
                            skiprows=self.skip_rows,
                            encoding=self.encoding,
                            low_memory=False
                        )
                        if len(df.columns) > 1:  # Found a good delimiter
                            break
                    except Exception:
                        continue
                else:
                    raise ParsingError("Could not parse file with any delimiter")
            
            # Basic validation
            if df.empty:
                raise ParsingError(f"Empty data file: {file_path}")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Prepare result
            result = {
                'pacs_data': {
                    'columns': list(df.columns),
                    'row_count': len(df),
                    'raw_data': df.to_dict('records')
                },
                'file_info': {
                    'path': str(file_path)
                }
            }
            
            self.logger.info(f"Parsed PACS data: {len(df)} rows, {len(df.columns)} columns")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse PACS data from {file_path}: {str(e)}")


class IntelEtlParser(BaseParser):
    """Parser for Intel ETL (Event Tracing for Windows) files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # ETL files or files with ETL in the name
        filename_lower = file_path.name.lower()
        return (
            file_path.suffix.lower() == '.etl' or
            'etl' in filename_lower or
            '_start_end_times' in filename_lower
        )
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse Intel ETL file."""
        try:
            if file_path.suffix.lower() == '.etl':
                # Binary ETL file - return metadata only for now
                result = {
                    'intel_etl_data': {
                        'file_type': 'binary_etl',
                        'file_size': file_path.stat().st_size,
                        'note': 'Binary ETL file - requires ETW processing tools for full parsing'
                    },
                    'file_info': {
                        'path': str(file_path)
                    }
                }
            else:
                # Text-based ETL file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                lines = content.split('\n')
                result = {
                    'intel_etl_data': {
                        'file_type': 'text_etl',
                        'line_count': len(lines),
                        'content_sample': lines[:10],  # First 10 lines
                        'raw_content': content
                    },
                    'file_info': {
                        'path': str(file_path)
                    }
                }
            
            self.logger.info(f"Parsed Intel ETL file: {file_path.name}")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse Intel ETL file {file_path}: {str(e)}")


class GenericCsvParser(BaseParser):
    """Generic CSV parser that attempts to parse any CSV file."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = self.config.get('delimiter', ',')
        self.skip_rows = self.config.get('skip_rows', 0)
        self.encoding = self.config.get('encoding', 'utf-8')
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in ['.csv', '.txt']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse generic CSV file with flexible approach."""
        try:
            # Try multiple encoding and delimiter combinations
            encodings = ['utf-8', 'latin1', 'cp1252']
            delimiters = [',', '\t', ';', '|']
            
            df = None
            used_encoding = 'utf-8'
            used_delimiter = ','
            
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(
                            file_path,
                            delimiter=delimiter,
                            skiprows=self.skip_rows,
                            encoding=encoding,
                            low_memory=False,
                            on_bad_lines='skip'
                        )
                        if len(df.columns) > 1 and len(df) > 0:
                            used_encoding = encoding
                            used_delimiter = delimiter
                            break
                    except Exception:
                        continue
                if df is not None and len(df.columns) > 1:
                    break
            
            if df is None or df.empty:
                # Try as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                lines = content.split('\n')
                return {
                    'text_data': {
                        'line_count': len(lines),
                        'content_sample': lines[:20],
                        'parsing_info': 'Parsed as text file - CSV parsing failed'
                    },
                    'file_info': {
                        'path': str(file_path)
                    }
                }
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Determine data type based on filename
            filename_lower = file_path.name.lower()
            if 'power' in filename_lower:
                data_type = 'power_data'
            elif 'config' in filename_lower:
                data_type = 'configuration'
            elif 'summary' in filename_lower:
                data_type = 'summary'
            elif 'automation' in filename_lower:
                data_type = 'automation'
            else:
                data_type = 'generic_csv'
            
            result = {
                'csv_data': {
                    'data_type': data_type,
                    'columns': list(df.columns),
                    'row_count': len(df),
                    'parsing_info': f'Parsed with delimiter={used_delimiter}, encoding={used_encoding}',
                    'raw_data': df.to_dict('records')
                },
                'file_info': {
                    'path': str(file_path)
                }
            }
            
            self.logger.info(f"Parsed generic CSV: {len(df)} rows, {len(df.columns)} columns")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse file {file_path}: {str(e)}")


class LogFileParser(BaseParser):
    """Parser for log files."""
    
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in ['.log', '.txt']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse log file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            result = {
                'log_data': {
                    'total_lines': len(lines),
                    'non_empty_lines': len(non_empty_lines),
                    'file_size': file_path.stat().st_size,
                    'content_sample': non_empty_lines[:20],  # First 20 non-empty lines
                    'full_content': content
                },
                'file_info': {
                    'path': str(file_path)
                }
            }
            
            self.logger.info(f"Parsed log file: {len(lines)} lines")
            return result
            
        except Exception as e:
            raise ParsingError(f"Failed to parse log file {file_path}: {str(e)}")