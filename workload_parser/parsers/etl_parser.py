"""
Enhanced ETL Parser with timestamp and event analysis.
Based on the original ETL_parser.py but with modern architecture.
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class ETLParser(BaseParser):
    """Enhanced parser for ETL (Event Trace Log) files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.encoding = self.config.get('encoding', 'utf-8')
        self.max_events = self.config.get('max_events', 10000)  # Limit for memory
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        # Check file extension
        if file_path.suffix.lower() not in ['.etl', '.txt', '.log']:
            return False
        
        # Check filename patterns (from old project)
        filename_lower = file_path.name.lower()
        etl_patterns = [
            r'.*\.etl$',
            r'.*etl.*\.txt',
            r'.*_output\.txt',
        ]
        
        # Exclude socwatch ETL files
        if 'session.etl' in filename_lower:
            return False
            
        return any(re.match(pattern, filename_lower) for pattern in etl_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse ETL file and extract timing information."""
        try:
            self.logger.info(f"Parsing ETL file: {file_path}")
            
            if file_path.suffix.lower() == '.etl':
                # Binary ETL file - would need Windows ETW tools to parse
                return self._parse_binary_etl(file_path)
            else:
                # Text-based ETL output file
                return self._parse_text_etl(file_path)
                
        except Exception as e:
            error_msg = f"Error parsing ETL file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg) from e
    
    def _parse_binary_etl(self, file_path: Path) -> Dict[str, Any]:
        """Parse binary ETL file (placeholder - requires ETW tools)."""
        # For binary ETL files, we would typically use Windows ETW tools
        # This is a placeholder that records the file info
        
        file_stats = file_path.stat()
        
        result = {
            'data_type': 'etl_binary',
            'parser': 'ETLParser',
            'etl_data': {
                'file_type': 'binary_etl',
                'parsing_note': 'Binary ETL requires Windows ETW tools for full parsing',
                'file_size_bytes': file_stats.st_size,
                'file_modification_time': file_stats.st_mtime
            },
            'file_info': {
                'path': str(file_path),
                'size_bytes': file_stats.st_size
            }
        }
        
        self.logger.info(f"Recorded binary ETL file info: {file_path}")
        return result
    
    def _parse_text_etl(self, file_path: Path) -> Dict[str, Any]:
        """Parse text-based ETL output file."""
        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            content = f.read()
        
        if not content.strip():
            raise ParsingError(f"Empty ETL file: {file_path}")
        
        # Extract timing information (from old project)
        etl_data = self._extract_etl_metrics(content)
        
        result = {
            'data_type': 'etl',
            'parser': 'ETLParser',
            'etl_data': etl_data,
            'file_info': {
                'path': str(file_path),
                'content_size': len(content),
                'line_count': len(content.split('\\n'))
            }
        }
        
        self.logger.info(f"Successfully parsed ETL data: {len(etl_data)} metrics extracted")
        return result
    
    def _extract_etl_metrics(self, content: str) -> Dict[str, Any]:
        """Extract metrics from ETL content."""
        etl_data = {}
        lines = content.split('\\n')
        
        # Look for timing patterns (from old project)
        timestamps = []
        events = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract timestamps if present
            timestamp = self._extract_timestamp(line)
            if timestamp:
                timestamps.append(timestamp)
            
            # Extract events
            event_info = self._extract_event_info(line)
            if event_info:
                events.append(event_info)
        
        # Calculate timing metrics
        if timestamps:
            etl_data['timing'] = self._calculate_timing_metrics(timestamps)
        
        if events:
            etl_data['events'] = self._analyze_events(events)
            
        # Look for first event epoch (from old project)
        first_event_epoch = self._find_first_event_epoch(content)
        if first_event_epoch:
            etl_data['socwatch_first_event_epoch_milli'] = first_event_epoch
        
        return etl_data
    
    def _extract_timestamp(self, line: str) -> Optional[float]:
        """Extract timestamp from a line."""
        # Look for various timestamp formats
        timestamp_patterns = [
            r'(\\d{13})',  # 13-digit millisecond epoch
            r'(\\d{10})',  # 10-digit second epoch
            r'(\\d+\\.\\d+)',  # Decimal timestamp
            r'(\\d{4}-\\d{2}-\\d{2}[T\\s]\\d{2}:\\d{2}:\\d{2})',  # ISO format
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    
                    # Try to convert to float
                    if '.' in timestamp_str:
                        return float(timestamp_str)
                    elif len(timestamp_str) == 13:  # Millisecond epoch
                        return float(timestamp_str)
                    elif len(timestamp_str) == 10:  # Second epoch
                        return float(timestamp_str) * 1000  # Convert to milliseconds
                    else:
                        return float(timestamp_str)
                        
                except ValueError:
                    continue
        
        return None
    
    def _extract_event_info(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract event information from a line."""
        # Look for common event patterns
        event_patterns = [
            r'Event[:\\s]+(\\w+)',
            r'(\\w+)\\s+Event',
            r'Task[:\\s]+(\\w+)',
            r'Process[:\\s]+(\\w+)',
        ]
        
        for pattern in event_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return {
                    'event_name': match.group(1),
                    'full_line': line[:100]  # Truncate for memory
                }
        
        return None
    
    def _calculate_timing_metrics(self, timestamps: List[float]) -> Dict[str, Any]:
        """Calculate timing metrics from timestamps."""
        if not timestamps:
            return {}
        
        timestamps.sort()
        
        timing_metrics = {
            'first_timestamp': timestamps[0],
            'last_timestamp': timestamps[-1],
            'duration_ms': timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0,
            'event_count': len(timestamps),
        }
        
        # Calculate intervals between events
        if len(timestamps) > 1:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            timing_metrics['avg_interval_ms'] = sum(intervals) / len(intervals)
            timing_metrics['min_interval_ms'] = min(intervals)
            timing_metrics['max_interval_ms'] = max(intervals)
        
        return timing_metrics
    
    def _analyze_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze event patterns."""
        if not events:
            return {}
        
        # Count event types
        event_counts = {}
        for event in events:
            event_name = event.get('event_name', 'unknown')
            event_counts[event_name] = event_counts.get(event_name, 0) + 1
        
        return {
            'total_events': len(events),
            'unique_event_types': len(event_counts),
            'event_type_counts': event_counts,
            'most_common_event': max(event_counts.items(), key=lambda x: x[1])[0] if event_counts else None
        }
    
    def _find_first_event_epoch(self, content: str) -> Optional[int]:
        """Find first event epoch timestamp (from old project)."""
        # Look for 13-digit epoch timestamps
        epoch_pattern = r'(\\d{13})'
        matches = re.findall(epoch_pattern, content)
        
        if matches:
            for match in matches:
                try:
                    epoch = int(match)
                    # Validate epoch is reasonable (between 2020 and 2030)
                    if 1577836800000 <= epoch <= 1893456000000:  # 2020-2030 in milliseconds
                        return epoch
                except ValueError:
                    continue
        
        return None
    
    def _is_epoch_milliseconds(self, value: float) -> bool:
        """Check if value is epoch milliseconds (from old project)."""
        # Check if value is between reasonable epoch bounds
        return 1e10 <= value <= 4102444800000  # Roughly 1970-2100
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed ETL data."""
        if not super().validate_data(data):
            return False
        
        etl_data = data.get('etl_data', {})
        return len(etl_data) > 0


class ModelOutputParser(BaseParser):
    """Parser for AI model output files (from old project)."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle model output files."""
        filename_lower = file_path.name.lower()
        
        # Check for model output patterns (from old project)
        model_patterns = [
            r'.*_qdq_proxy_.*',
            r'.*model.*output.*',
            r'.*inference.*output.*',
        ]
        
        return any(re.match(pattern, filename_lower) for pattern in model_patterns)
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse model output file."""
        try:
            self.logger.info(f"Parsing model output file: {file_path}")
            
            # Check if file exists and has content
            if not file_path.exists():
                model_data = {
                    'model_output_status': 'failed',
                    'error': 'File not found'
                }
            elif file_path.stat().st_size == 0:
                model_data = {
                    'model_output_status': 'failed',
                    'error': 'Empty file'
                }
            else:
                # Parse model output
                model_data = self._parse_model_content(file_path)
            
            result = {
                'data_type': 'model_output',
                'parser': 'ModelOutputParser',
                'model_output_data': model_data,
                'file_info': {
                    'path': str(file_path),
                    'exists': file_path.exists(),
                    'size_bytes': file_path.stat().st_size if file_path.exists() else 0
                }
            }
            
            self.logger.info(f"Successfully parsed model output: {model_data.get('model_output_status', 'unknown')}")
            return result
            
        except Exception as e:
            error_msg = f"Error parsing model output file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg) from e
    
    def _parse_model_content(self, file_path: Path) -> Dict[str, Any]:
        """Parse model output content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract throughput information
            throughput = self._extract_throughput(content)
            
            model_data = {
                'model_output_status': 'success',
                'throughput': throughput if throughput else [0],
                'content_preview': content[:500] if content else ''
            }
            
            return model_data
            
        except Exception as e:
            return {
                'model_output_status': 'failed',
                'error': str(e)
            }
    
    def _extract_throughput(self, content: str) -> Optional[List[float]]:
        """Extract throughput values from model output."""
        # Look for common throughput patterns
        throughput_patterns = [
            r'throughput[:\\s]+([\\d\\.]+)',
            r'fps[:\\s]+([\\d\\.]+)',
            r'frames[\\s]+per[\\s]+second[:\\s]+([\\d\\.]+)',
            r'([\\d\\.]+)[\\s]+fps',
        ]
        
        for pattern in throughput_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    return [float(match) for match in matches]
                except ValueError:
                    continue
        
        return None