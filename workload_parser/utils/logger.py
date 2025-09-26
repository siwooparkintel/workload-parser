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
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Setup console handler
    if config.console:
        if RICH_AVAILABLE:
            console_handler = RichHandler(
                rich_tracebacks=True,
                show_time=False,
                show_path=False
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
        
        console_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
        logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if config.file_path:
        file_path = Path(config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)