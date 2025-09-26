#!/usr/bin/env python3
"""
Example usage of the Workload Parser framework.
"""

import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import workload_parser
sys.path.insert(0, str(Path(__file__).parent.parent))

from workload_parser import WorkloadParser, ParserConfig


def main():
    """Main example function."""
    print("Workload Parser Example")
    print("=" * 50)
    
    # Example 1: Parse with default configuration
    print("\n1. Using default configuration:")
    parser = WorkloadParser()
    
    # Show parser status
    status = parser.get_parser_status()
    print(f"Available parsers: {status['available_parsers']}")
    print(f"Enabled parsers: {status['enabled_parsers']}")
    
    # Example 2: Parse with custom configuration
    print("\n2. Using custom configuration:")
    config_path = Path(__file__).parent.parent / "config" / "parser_config.json"
    
    if config_path.exists():
        parser_with_config = WorkloadParser(str(config_path))
        print(f"Configuration loaded from: {config_path}")
        
        # Example file parsing (would work with actual files)
        example_data_dir = Path(__file__).parent / "sample_data"
        if example_data_dir.exists():
            print(f"\n3. Parsing directory: {example_data_dir}")
            results = parser_with_config.parse_directory(str(example_data_dir))
            print(f"Parsed {len(results)} files")
            
            for result in results[:3]:  # Show first 3 results
                metadata = result.get('_metadata', {})
                print(f"  - {metadata.get('file_path', 'Unknown')}: "
                      f"{result.get('data_type', 'unknown')} data, "
                      f"{result.get('row_count', 0)} rows")
        else:
            print(f"Sample data directory not found: {example_data_dir}")
            print("Create some sample CSV files to test parsing.")
    else:
        print(f"Configuration file not found: {config_path}")
    
    # Example 3: Custom parser registration
    print("\n3. Custom parser example:")
    print("You can register custom parsers by inheriting from BaseParser")
    print("and calling parser.register_parser('my_parser', MyCustomParser)")


if __name__ == "__main__":
    main()