"""
Logging utilities for the workload parser.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def setup_logging(config) -> None:
    """Setup logging configuration."""
    
    # Handle both dict and object configurations
    if isinstance(config, dict):
        level = config.get('level', 'INFO')
        format_str = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console = config.get('console', True)
        file_path = config.get('file_path')
    else:
        level = getattr(config, 'level', 'INFO')
        format_str = getattr(config, 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console = getattr(config, 'console', True)
        file_path = getattr(config, 'file_path', None)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Setup console handler
    if console:
        if RICH_AVAILABLE:
            console_handler = RichHandler(
                rich_tracebacks=True,
                show_time=False,
                show_path=False
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
        
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if file_path:
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path_obj, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)