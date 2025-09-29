"""
Enhanced configuration management for the workload parser framework.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from .exceptions import ConfigurationError


class ParserConfig:
    """Enhanced configuration management class with DAQ, Socwatch, and PCIe target support."""
    
    def __init__(self, config_path: Optional[str] = None):
        self._config_path = config_path
        self._config = {}
        self._load_configuration(config_path)
    
    def _load_configuration(self, config_path: Optional[str]) -> None:
        """Load configuration from file or create defaults."""
        if config_path and Path(config_path).exists():
            self.load_from_file(config_path)
        else:
            self._load_defaults()
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
                
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def get_parser_config(self, parser_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific parser."""
        parsers = self._config.get('parsers', {})
        parser_config = parsers.get(parser_name, {})
        
        # Merge with global targets for enhanced parsers
        if parser_name == 'power':
            parser_config.setdefault('options', {})['daq_targets'] = self.get_daq_targets()
        elif parser_name == 'socwatch':
            parser_config.setdefault('options', {})['socwatch_targets'] = self.get_socwatch_targets()
        elif parser_name == 'pcie':
            parser_config.setdefault('options', {})['pcie_targets'] = self.get_pcie_targets()
        elif parser_name == 'hobl':
            parser_config.setdefault('options', {})['hobl_enabled'] = self.is_hobl_enabled()
        
        return parser_config
    
    def get_enabled_parsers(self) -> List[str]:
        """Get list of enabled parser names."""
        parsers = self._config.get('parsers', {})
        enabled = [name for name, config in parsers.items() if config.get('enabled', True)]
        
        # Add HOBL parser if enabled
        if self.is_hobl_enabled() and 'hobl' not in enabled:
            enabled.insert(0, 'hobl')  # High priority for HOBL
        
        return enabled
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get('logging', {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'console': True
        })
    
    def get_daq_targets(self) -> Dict[str, Any]:
        """Get DAQ target configuration."""
        return self._config.get('daq_targets', {})
    
    def get_socwatch_targets(self) -> List[Dict[str, Any]]:
        """Get Socwatch target configuration."""
        return self._config.get('socwatch_targets', [])
    
    def get_pcie_targets(self) -> List[Dict[str, Any]]:
        """Get PCIe target configuration."""
        return self._config.get('pcie_targets', [])
    
    def is_hobl_enabled(self) -> bool:
        """Check if HOBL processing is enabled."""
        processing = self._config.get('processing', {})
        return processing.get('hobl_enabled', False)
    
    def get_power_picking_strategy(self) -> str:
        """Get power picking strategy."""
        processing = self._config.get('processing', {})
        return processing.get('power_picking_strategy', 'MED')
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self._config.get('output', {
            'format': 'excel',
            'filename_template': '{input_name}_allPower_v{version}.xlsx'
        })
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        # Try to load from the enhanced config file
        enhanced_config_path = Path(__file__).parent.parent.parent / 'config' / 'enhanced_parser_config.json'
        
        if enhanced_config_path.exists():
            try:
                with open(enhanced_config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                return
            except Exception:
                pass  # Fall back to basic defaults
        
        # Basic defaults if enhanced config not available
        self._config = {
            "version": "2.0.0",
            "parsers": {
                "power": {
                    "enabled": True,
                    "priority": 10,
                    "file_patterns": ["*power*summary*.csv", "*pacs-summary*.csv"],
                    "options": {"average_column": "Average", "delimiter": ",", "encoding": "utf-8-sig"}
                },
                "power_trace": {
                    "enabled": True,
                    "priority": 15,
                    "file_patterns": ["*pacs-traces*.csv", "*trace*.csv"],
                    "options": {"sample_rate": 1000, "max_samples": 100000}
                },
                "etl": {
                    "enabled": True,
                    "priority": 20,
                    "file_patterns": ["*.etl", "*etl*.txt", "*_output.txt"],
                    "options": {"max_events": 10000, "encoding": "utf-8"}
                },
                "model_output": {
                    "enabled": True,
                    "priority": 25,
                    "file_patterns": ["*_qdq_proxy_*", "*model*output*"],
                    "options": {}
                },
                "socwatch": {
                    "enabled": True,
                    "priority": 30,
                    "file_patterns": ["*socwatch*.csv"],
                    "options": {"encoding": "utf-8-sig"}
                },
                "pcie": {
                    "enabled": True,
                    "priority": 35,
                    "file_patterns": ["*socwatch*.csv"],
                    "options": {}
                },
                "hobl": {
                    "enabled": False,
                    "priority": 5,
                    "file_patterns": [".PASS", ".FAIL"],
                    "options": {}
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "console": True
            },
            "daq_targets": {},
            "socwatch_targets": [],
            "pcie_targets": [],
            "processing": {
                "hobl_enabled": False,
                "power_picking_strategy": "MED",
                "inference_only_mode": False,
                "sort_similar_data": False
            },
            "output": {
                "format": "excel",
                "filename_template": "{input_name}_allPower_v{version}.xlsx",
                "include_raw_data": False
            }
        }
    
    def save_config(self, output_path: str) -> None:
        """Save current configuration to file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        def deep_update(base_dict: Dict, update_dict: Dict) -> Dict:
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
            return base_dict
        
        deep_update(self._config, updates)