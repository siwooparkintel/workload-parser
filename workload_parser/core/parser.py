"""
Main workload parser framework.

This module provides the core parsing infrastructure for workload data analysis.
Supports multiple parser types for different file formats and data sources.

Features:
- Extensible parser registry system
- Enhanced configuration with auto-detection and DAQ config modes
- Power rail auto-detection from PACS summary files
- DAQ configuration support for predefined power rail targets
- Comprehensive logging and error handling
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from abc import ABC, abstractmethod

from .config import ParserConfig
from .exceptions import ParsingError, ParserNotFoundError
from ..utils.logger import setup_logging


class BaseParser(ABC):
    """
    Abstract base class for all parsers.
    
    All custom parsers must inherit from this class and implement
    the can_parse() and parse() methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        pass
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parse the given file and return structured data."""
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data (override in subclasses if needed)."""
        return data is not None and len(data) > 0


class ParserRegistry:
    """Registry for managing available parsers."""
    
    def __init__(self):
        self._parsers: Dict[str, Type[BaseParser]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register(self, name: str, parser_class: Type[BaseParser]) -> None:
        """Register a parser class."""
        if not issubclass(parser_class, BaseParser):
            raise ValueError(f"Parser class must inherit from BaseParser: {parser_class}")
        
        self._parsers[name] = parser_class
        self.logger.debug(f"Registered parser: {name}")
    
    def get_parser(self, name: str) -> Type[BaseParser]:
        """Get a parser class by name."""
        if name not in self._parsers:
            raise ParserNotFoundError(f"Parser not found: {name}")
        return self._parsers[name]
    
    def get_available_parsers(self) -> List[str]:
        """Get list of available parser names."""
        return list(self._parsers.keys())
    
    def find_compatible_parser(self, file_path: Path, config: ParserConfig) -> Optional[str]:
        """Find a parser that can handle the given file."""
        for parser_name in config.get_enabled_parsers():
            if parser_name in self._parsers:
                parser_config = config.get_parser_config(parser_name)
                if parser_config:
                    # Create temporary instance to check compatibility
                    parser_options = parser_config.get('options', {})
                    parser_instance = self._parsers[parser_name](parser_options)
                    if parser_instance.can_parse(file_path):
                        return parser_name
        return None


class WorkloadParser:
    """
    Main workload parser orchestrator.
    
    Coordinates parsing of workload data files using registered parsers.
    Supports both individual file parsing and directory-level batch processing.
    
    Features:
    - Auto-detection of power rails from PACS summary files
    - DAQ configuration support for predefined targets
    - Enhanced parser configuration system
    - Comprehensive error handling and logging
    - Extensible parser registry
    
    Args:
        config_path: Path to configuration JSON file (optional)
        config: Pre-configured ParserConfig instance (optional)
    """
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[ParserConfig] = None):
        # Load configuration
        self.config = config or ParserConfig(config_path)
        
        # Setup logging
        setup_logging(self.config.logging_config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize parser registry
        self.registry = ParserRegistry()
        self._register_default_parsers()
        
        self.logger.info("WorkloadParser initialized")
    
    def _register_default_parsers(self) -> None:
        """Register default parsers."""
        try:
            # Import enhanced parsers
            from ..parsers.power_parser import PowerParser, PowerTraceParser
            from ..parsers.etl_parser import ETLParser, ModelOutputParser
            from ..parsers.socwatch_parser import SocwatchParser, PCIeParser
            from ..parsers.hobl_parser import HOBLParser
            from ..parsers.intel_parsers import PacsParser, IntelEtlParser, GenericCsvParser, LogFileParser
            
            # Register enhanced parsers with old project functionality
            self.registry.register("power", PowerParser)
            self.registry.register("power_trace", PowerTraceParser)
            self.registry.register("etl", ETLParser)
            self.registry.register("model_output", ModelOutputParser)
            self.registry.register("socwatch", SocwatchParser)
            self.registry.register("pcie", PCIeParser)
            self.registry.register("hobl", HOBLParser)
            
            # Register Intel-specific parsers
            self.registry.register("pacs", PacsParser)
            self.registry.register("intel_etl", IntelEtlParser)
            self.registry.register("log_file", LogFileParser)
            self.registry.register("generic_csv", GenericCsvParser)  # This should be last as fallback
            
        except ImportError as e:
            self.logger.warning(f"Some default parsers could not be loaded: {e}")
    
    def register_parser(self, name: str, parser_class: Type[BaseParser]) -> None:
        """Register a custom parser."""
        self.registry.register(name, parser_class)
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a single file."""
        path = Path(file_path)
        
        if not path.exists():
            raise ParsingError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ParsingError(f"Path is not a file: {file_path}")
        
        # Find compatible parser
        parser_name = self.registry.find_compatible_parser(path, self.config)
        
        if not parser_name:
            raise ParsingError(f"No compatible parser found for: {file_path}")
        
        try:
            # Get parser configuration
            parser_config = self.config.get_parser_config(parser_name)
            
            # Create parser instance
            parser_class = self.registry.get_parser(parser_name)
            parser_options = parser_config.get('options', {})
            parser_instance = parser_class(parser_options)
            
            # Parse the file
            self.logger.info(f"Parsing {file_path} with {parser_name} parser")
            result = parser_instance.parse(path)
            
            # Validate result
            if not parser_instance.validate_data(result):
                raise ParsingError(f"Data validation failed for: {file_path}")
            
            # Add metadata
            result['_metadata'] = {
                'file_path': str(path),
                'parser_name': parser_name,
                'file_size': path.stat().st_size,
                'parsed_at': str(Path().resolve())  # Current timestamp placeholder
            }
            
            self.logger.info(f"Successfully parsed {file_path}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to parse {file_path} with {parser_name}: {str(e)}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg, str(path))
    
    def parse_directory(self, directory_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """Parse all compatible files in a directory."""
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise ParsingError(f"Directory not found: {directory_path}")
        
        if not dir_path.is_dir():
            raise ParsingError(f"Path is not a directory: {directory_path}")
        
        results = []
        errors = []
        
        # Get file pattern
        pattern = "**/*" if recursive else "*"
        
        # Find all files
        all_files = [f for f in dir_path.glob(pattern) if f.is_file()]
        
        self.logger.info(f"Found {len(all_files)} files in {directory_path}")
        
        for file_path in all_files:
            try:
                result = self.parse_file(str(file_path))
                results.append(result)
            except ParsingError as e:
                self.logger.warning(f"Skipping file due to parsing error: {e}")
                errors.append({
                    'file_path': str(file_path),
                    'error': str(e)
                })
            except Exception as e:
                self.logger.error(f"Unexpected error parsing {file_path}: {e}")
                errors.append({
                    'file_path': str(file_path),
                    'error': f"Unexpected error: {str(e)}"
                })
        
        self.logger.info(f"Successfully parsed {len(results)} files, {len(errors)} errors")
        
        if errors:
            self.logger.warning(f"Parsing errors occurred for {len(errors)} files")
        
        return results
    
    def get_parser_status(self) -> Dict[str, Any]:
        """Get status information about available parsers."""
        return {
            'available_parsers': self.registry.get_available_parsers(),
            'enabled_parsers': self.config.get_enabled_parsers(),
            'config_loaded': self.config is not None
        }