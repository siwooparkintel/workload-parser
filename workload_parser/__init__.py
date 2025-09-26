"""
Workload Parser - A modern framework for parsing and analyzing workload data.

This package provides a flexible, extensible framework for parsing various types
of workload data including power consumption, ETL processes, and socwatch metrics.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.parser import WorkloadParser
from .core.config import ParserConfig
from .core.exceptions import ParsingError, ConfigurationError

__all__ = [
    "WorkloadParser",
    "ParserConfig", 
    "ParsingError",
    "ConfigurationError",
]