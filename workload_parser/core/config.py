"""
Configuration management for the workload parser framework.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator

from .exceptions import ConfigurationError


class ParserConfigModel(BaseModel):
    """Pydantic model for parser configuration validation."""
    
    name: str = Field(..., description="Parser name")
    enabled: bool = Field(True, description="Whether parser is enabled")
    file_patterns: List[str] = Field(..., description="File patterns to match")
    options: Dict[str, Any] = Field(default_factory=dict, description="Parser-specific options")
    
    @validator('file_patterns')
    def validate_patterns(cls, v):
        if not v:
            raise ValueError("At least one file pattern is required")
        return v


class LoggingConfig(BaseModel):
    """Configuration for logging settings."""
    
    level: str = Field("INFO", description="Logging level")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
                       description="Log format string")
    file_path: Optional[str] = Field(None, description="Log file path")
    console: bool = Field(True, description="Enable console logging")


class ParserConfig:
    """Main configuration management class."""
    
    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._parsers: Dict[str, ParserConfigModel] = {}
        self._logging: LoggingConfig = LoggingConfig()
        
        if config_path:
            self.load_from_file(config_path)
        else:
            self._load_defaults()
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from a file."""
        path = Path(config_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            if path.suffix.lower() in ['.yml', '.yaml']:
                with open(path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                raise ConfigurationError(f"Unsupported config format: {path.suffix}")
                
            self._validate_and_load_config()
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {config_path}: {str(e)}")
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        self._config = {
            "parsers": {
                "power": {
                    "name": "power",
                    "enabled": True,
                    "file_patterns": ["*power*.csv", "*Power*.csv"],
                    "options": {
                        "delimiter": ",",
                        "skip_rows": 0
                    }
                },
                "etl": {
                    "name": "etl",
                    "enabled": True,
                    "file_patterns": ["*etl*.csv", "*ETL*.csv"],
                    "options": {
                        "delimiter": ",",
                        "skip_rows": 0
                    }
                },
                "socwatch": {
                    "name": "socwatch",
                    "enabled": True,
                    "file_patterns": ["*socwatch*.csv", "*SocWatch*.csv"],
                    "options": {
                        "delimiter": ",",
                        "skip_rows": 0
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "console": True
            }
        }
        self._validate_and_load_config()
    
    def _validate_and_load_config(self) -> None:
        """Validate and load the configuration."""
        try:
            # Load parser configurations
            parsers_config = self._config.get("parsers", {})
            for parser_name, parser_config in parsers_config.items():
                self._parsers[parser_name] = ParserConfigModel(**parser_config)
            
            # Load logging configuration
            logging_config = self._config.get("logging", {})
            self._logging = LoggingConfig(**logging_config)
            
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    
    def get_parser_config(self, parser_name: str) -> Optional[ParserConfigModel]:
        """Get configuration for a specific parser."""
        return self._parsers.get(parser_name)
    
    def get_enabled_parsers(self) -> List[str]:
        """Get list of enabled parser names."""
        return [name for name, config in self._parsers.items() if config.enabled]
    
    @property
    def logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return self._logging
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def update_parser_config(self, parser_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific parser."""
        try:
            self._parsers[parser_name] = ParserConfigModel(**config)
        except Exception as e:
            raise ConfigurationError(f"Invalid parser configuration for {parser_name}: {str(e)}")
    
    def save_to_file(self, config_path: str) -> None:
        """Save current configuration to a file."""
        path = Path(config_path)
        
        try:
            # Convert to serializable format
            config_dict = {
                "parsers": {
                    name: config.dict() for name, config in self._parsers.items()
                },
                "logging": self._logging.dict()
            }
            
            if path.suffix.lower() in ['.yml', '.yaml']:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            elif path.suffix.lower() == '.json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2)
            else:
                raise ConfigurationError(f"Unsupported config format: {path.suffix}")
                
        except Exception as e:
            raise ConfigurationError(f"Failed to save config to {config_path}: {str(e)}")