"""
Tests for the core parser functionality.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from workload_parser.core.parser import WorkloadParser, BaseParser, ParserRegistry
from workload_parser.core.config import ParserConfig
from workload_parser.core.exceptions import ParsingError, ParserNotFoundError


class MockParser(BaseParser):
    """Mock parser for testing."""
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.name.startswith("test_")
    
    def parse(self, file_path: Path) -> dict:
        return {
            'data_type': 'mock',
            'file_name': file_path.name,
            'row_count': 10
        }


class TestParserRegistry(unittest.TestCase):
    """Test the parser registry functionality."""
    
    def setUp(self):
        self.registry = ParserRegistry()
    
    def test_register_parser(self):
        """Test parser registration."""
        self.registry.register("mock", MockParser)
        self.assertIn("mock", self.registry.get_available_parsers())
    
    def test_get_parser(self):
        """Test getting a registered parser."""
        self.registry.register("mock", MockParser)
        parser_class = self.registry.get_parser("mock")
        self.assertEqual(parser_class, MockParser)
    
    def test_parser_not_found(self):
        """Test exception when parser not found."""
        with self.assertRaises(ParserNotFoundError):
            self.registry.get_parser("nonexistent")


class TestParserConfig(unittest.TestCase):
    """Test the configuration management."""
    
    def test_default_config(self):
        """Test default configuration loading."""
        config = ParserConfig()
        enabled_parsers = config.get_enabled_parsers()
        self.assertIn("power", enabled_parsers)
        self.assertIn("etl", enabled_parsers)
        self.assertIn("socwatch", enabled_parsers)
    
    def test_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "parsers": {
                "test": {
                    "name": "test",
                    "enabled": True,
                    "file_patterns": ["*.test"],
                    "options": {"delimiter": ";"}
                }
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ParserConfig(temp_path)
            self.assertIn("test", config.get_enabled_parsers())
            parser_config = config.get_parser_config("test")
            self.assertEqual(parser_config.options["delimiter"], ";")
        finally:
            Path(temp_path).unlink()


class TestWorkloadParser(unittest.TestCase):
    """Test the main workload parser."""
    
    def setUp(self):
        self.parser = WorkloadParser()
        self.parser.register_parser("mock", MockParser)
    
    def test_parser_status(self):
        """Test getting parser status."""
        status = self.parser.get_parser_status()
        self.assertIn('available_parsers', status)
        self.assertIn('enabled_parsers', status)
        self.assertIn("mock", status['available_parsers'])
    
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        with self.assertRaises(ParsingError):
            self.parser.parse_file("nonexistent_file.csv")
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_parse_file_success(self, mock_is_file, mock_exists):
        """Test successful file parsing."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(prefix="test_", suffix=".csv", delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.parser.parse_file(temp_path)
            self.assertEqual(result['data_type'], 'mock')
            self.assertIn('_metadata', result)
        finally:
            Path(temp_path).unlink()


if __name__ == '__main__':
    unittest.main()