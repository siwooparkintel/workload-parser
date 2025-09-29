"""
HOBL Parser for detecting .PASS/.FAIL files and dataset organization.
Based on the old project's HOBL integration.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..core.parser import BaseParser
from ..core.exceptions import ParsingError


class HOBLParser(BaseParser):
    """Parser for HOBL .PASS/.FAIL marker files."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.hobl_enabled = self.config.get('hobl_enabled', False)
        
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle HOBL marker files."""
        if not self.hobl_enabled:
            return False
            
        # Check for HOBL marker files (from old project)
        filename = file_path.name
        return filename in ['.PASS', '.FAIL']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse HOBL marker file and extract dataset information."""
        try:
            self.logger.info(f"Parsing HOBL marker file: {file_path}")
            
            # Extract dataset information from path structure
            dataset_info = self._extract_dataset_info(file_path)
            
            # Determine test result
            test_result = 'PASS' if file_path.name == '.PASS' else 'FAIL'
            
            result = {
                'data_type': 'hobl_marker',
                'parser': 'HOBLParser',
                'hobl_data': {
                    'test_result': test_result,
                    'dataset_path': str(file_path.parent),
                    'dataset_label': dataset_info['label'],
                    'dataset_hierarchy': dataset_info['hierarchy']
                },
                'file_info': {
                    'path': str(file_path),
                    'marker_type': test_result
                }
            }
            
            self.logger.info(f"Successfully parsed HOBL marker: {test_result} for dataset {dataset_info['label']}")
            return result
            
        except Exception as e:
            error_msg = f"Error parsing HOBL marker file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg) from e
    
    def _extract_dataset_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract dataset information from path structure (from old project)."""
        path_parts = file_path.parts
        
        # Get the parent directory as the dataset path
        dataset_path = file_path.parent
        
        # Extract meaningful label from path structure
        if len(path_parts) >= 2:
            # Use last two directories as label
            label_parts = path_parts[-2:]
            label = f"{label_parts[0]}_{label_parts[1]}" if len(label_parts) > 1 else label_parts[0]
        else:
            label = path_parts[-1] if path_parts else 'unknown'
        
        return {
            'label': label,
            'hierarchy': list(path_parts),
            'depth': len(path_parts)
        }
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed HOBL data."""
        if not super().validate_data(data):
            return False
        
        hobl_data = data.get('hobl_data', {})
        required_fields = ['test_result', 'dataset_path', 'dataset_label']
        
        return all(field in hobl_data for field in required_fields)


class DatasetClassifier:
    """Utility class for classifying and organizing datasets (from old project)."""
    
    # Classification constants from old project
    CL_UNCLASSIFIED = "unclassified"
    CL_ETL = ".etl"
    CL_OUTPUT = '_output.txt'
    CL_SOCWATCH = 'Session.etl'
    CL_SOCWATCH_CSV = "socwatch.csv"
    CL_AI_MODEL = '_qdq_proxy_'
    CL_DAQ_SUMMARY = 'pacs-summary.csv'
    CL_DAQ_TRACES = 'pacs-traces'
    CL_PASS = ".PASS"
    CL_FAIL = ".FAIL"
    
    # Data type constants
    ETL = "ETL"
    POWER = "POWER"
    SOCWATCH = "SOCWATCH"
    PCIE = "PCIE"
    MODEL_OUTPUT = "MODEL_OUTPUT"
    
    # Folder structure detection
    SECOND_FOLDER_LIST = [ETL, POWER, SOCWATCH, PCIE]
    
    def __init__(self):
        self.datasets = []
    
    def classify_file(self, file_path: Path) -> str:
        """Classify file type based on patterns (from old project)."""
        filename = file_path.name.lower()
        
        if filename == self.CL_PASS or filename == self.CL_FAIL:
            return 'HOBL_MARKER'
        elif self.CL_ETL in filename and self.CL_SOCWATCH not in filename:
            return 'ETL'
        elif self.CL_DAQ_SUMMARY in filename:
            return 'POWER_SUMMARY'
        elif self.CL_DAQ_TRACES in filename and filename.endswith('.csv'):
            return 'POWER_TRACE'
        elif self.CL_SOCWATCH in filename:
            return 'SOCWATCH_ETL'
        elif self.CL_SOCWATCH_CSV in filename:
            return 'SOCWATCH_CSV'
        elif self.CL_AI_MODEL in filename:
            return 'MODEL_OUTPUT'
        else:
            return self.CL_UNCLASSIFIED
    
    def get_dataset_label(self, abs_path: Path) -> List[str]:
        """Get dataset label from path structure (from old project)."""
        path_parts = abs_path.parts
        
        # Check for folder structure separation
        if len(path_parts) >= 2:
            last_folder = path_parts[-1].upper()
            if last_folder in self.SECOND_FOLDER_LIST:
                # Hierarchical structure: return grand parent folders
                if len(path_parts) >= 4:
                    return [path_parts[-4], path_parts[-3]]
                else:
                    return [path_parts[-2], path_parts[-1]]
            else:
                # Flat structure: return parent folders
                if len(path_parts) >= 3:
                    return [path_parts[-3], path_parts[-2]]
                else:
                    return [path_parts[-2], path_parts[-1]] if len(path_parts) >= 2 else [path_parts[-1]]
        
        return ['unknown']
    
    def create_dataset(self, dataset_path: Path, hobl_enabled: bool = False) -> Dict[str, Any]:
        """Create dataset structure (from old project)."""
        dataset_label = self.get_dataset_label(dataset_path)
        
        dataset = {
            'ID_path': str(dataset_path),
            'data_label': dataset_label,
            'data_type': [],
            'files': {},
            'hobl_enabled': hobl_enabled
        }
        
        self.datasets.append(dataset)
        return dataset
    
    def find_dataset(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Find dataset that contains the given file path."""
        file_path_str = str(file_path)
        
        for dataset in self.datasets:
            if file_path_str.startswith(dataset['ID_path']):
                return dataset
        
        return None
    
    def add_file_to_dataset(self, file_path: Path, file_type: str, parsed_data: Dict[str, Any]):
        """Add parsed file data to appropriate dataset."""
        dataset = self.find_dataset(file_path)
        
        if dataset is None:
            # Create new dataset
            dataset = self.create_dataset(file_path.parent)
        
        # Add file type to dataset if not already present
        if file_type not in dataset['data_type']:
            dataset['data_type'].append(file_type)
        
        # Store parsed file data
        dataset['files'][str(file_path)] = {
            'file_type': file_type,
            'parsed_data': parsed_data
        }
    
    def get_datasets(self) -> List[Dict[str, Any]]:
        """Get all collected datasets."""
        return self.datasets
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all datasets."""
        total_datasets = len(self.datasets)
        data_types = set()
        total_files = 0
        
        for dataset in self.datasets:
            data_types.update(dataset['data_type'])
            total_files += len(dataset['files'])
        
        return {
            'total_datasets': total_datasets,
            'unique_data_types': list(data_types),
            'total_files': total_files,
            'avg_files_per_dataset': total_files / total_datasets if total_datasets > 0 else 0
        }