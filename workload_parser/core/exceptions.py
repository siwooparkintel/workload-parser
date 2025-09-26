"""
Custom exceptions for the workload parser framework.
"""


class WorkloadParserError(Exception):
    """Base exception for all workload parser errors."""
    pass


class ParsingError(WorkloadParserError):
    """Raised when parsing operations fail."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(message)


class ConfigurationError(WorkloadParserError):
    """Raised when configuration is invalid or missing."""
    pass


class ParserNotFoundError(WorkloadParserError):
    """Raised when a requested parser is not available."""
    pass


class ValidationError(WorkloadParserError):
    """Raised when data validation fails."""
    pass