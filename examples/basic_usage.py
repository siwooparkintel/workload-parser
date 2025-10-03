#!/usr/bin/env python3
"""
Example usage of the Workload Parser framework.

This example demonstrates:
1. Basic parsing with default configuration
2. Using DAQ configuration for specific power rails
3. Auto-detection mode for all P_* power rails
4. Custom configuration loading
5. Directory parsing

For standalone executable usage, see README_DISTRIBUTION.md
"""

import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import workload_parser
sys.path.insert(0, str(Path(__file__).parent.parent))

from workload_parser import WorkloadParser, ParserConfig


def main():
    """Main example function demonstrating various parser usage patterns."""
    print("Workload Parser Examples")
    print("=" * 80)
    
    # Example 1: Parse with default configuration (auto-detect mode)
    print("\n1. Auto-Detection Mode (detects all P_* power rails):")
    print("   This is the default behavior when no DAQ config is provided.")
    parser = WorkloadParser()
    
    # Show parser status
    status = parser.get_parser_status()
    print(f"   Available parsers: {status['available_parsers']}")
    print(f"   Enabled parsers: {status['enabled_parsers']}")
    
    # Example 2: Using DAQ Configuration (specific power rails)
    print("\n2. DAQ Configuration Mode (predefined power rail targets):")
    print("   Use this when you want specific power rails defined in a config file.")
    daq_config_path = Path(__file__).parent.parent / "config" / "daq_targets_default.json"
    
    if daq_config_path.exists():
        print(f"   DAQ config: {daq_config_path}")
        print("   Example command: wlparser.exe -i data_dir -d config/daq_targets_default.json")
    else:
        print(f"   DAQ config not found: {daq_config_path}")
    
    # Example 3: Parse with custom parser configuration
    print("\n3. Using custom parser configuration:")
    config_path = Path(__file__).parent.parent / "config" / "parser_config.json"
    
    if config_path.exists():
        parser_with_config = WorkloadParser(str(config_path))
        print(f"   Configuration loaded from: {config_path}")
        
        # Example file parsing (would work with actual files)
        example_data_dir = Path(__file__).parent / "sample_data"
        if example_data_dir.exists():
            print(f"\n   Parsing directory: {example_data_dir}")
            results = parser_with_config.parse_directory(str(example_data_dir))
            print(f"   Parsed {len(results)} files")
            
            for result in results[:3]:  # Show first 3 results
                metadata = result.get('_metadata', {})
                print(f"     - {metadata.get('file_path', 'Unknown')}: "
                      f"{result.get('data_type', 'unknown')} data, "
                      f"{result.get('row_count', 0)} rows")
        else:
            print(f"   Sample data directory not found: {example_data_dir}")
            print("   Create sample CSV files to test parsing.")
    else:
        print(f"   Configuration file not found: {config_path}")
    
    # Example 4: Standalone Executable Usage
    print("\n4. Standalone Executable Usage (wlparser.exe):")
    print("   - GUI mode: Double-click wlparser.exe or run without arguments")
    print("   - Auto-detect: wlparser.exe -i \"path/to/data\"")
    print("   - DAQ config: wlparser.exe -i \"path/to/data\" -d config/daq_targets_default.json")
    print("   - Custom output: wlparser.exe -i \"path/to/data\" -o \"custom_report.xlsx\"")
    print("   See README_DISTRIBUTION.md for complete standalone executable guide")
    
    # Example 5: Custom parser registration
    print("\n5. Custom parser registration example:")
    print("   You can register custom parsers by inheriting from BaseParser")
    print("   and calling parser.register_parser('my_parser', MyCustomParser)")


if __name__ == "__main__":
    main()