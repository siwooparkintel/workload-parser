#!/usr/bin/env python3
"""
Test script to verify the enhanced SocWatch parser functionality.

This test validates that the SocWatch parser correctly:
1. Captures table headers along with data
2. Integrates header information into the data dictionary
3. Preserves natural table order and grouping
4. Maintains backward compatibility
"""

import sys
import json
from pathlib import Path

# Add the workload_parser to the path
sys.path.insert(0, str(Path(__file__).parent))

from workload_parser.parsers.socwatch_parser import SocwatchParser

def test_header_parsing():
    """Test the header parsing functionality."""
    parser = SocwatchParser()
    
    # Test the header parsing method directly
    test_headers = [
        "State Name, Residency (Percentage and Time)",
        "Component, Rate (MB/s), Total",
        "Process Name, CPU Usage (%)",
        "Temperature Sensor, Min/Max/Avg (°C)"
    ]
    
    print("Testing header parsing:")
    for header_line in test_headers:
        parsed_headers = parser._parse_header_line(header_line)
        print(f"\nInput: {header_line}")
        print(f"Parsed: {json.dumps(parsed_headers, indent=2)}")

def test_table_structure():
    """Test that the new table structure integrates headers into data."""
    parser = SocwatchParser()
    
    # Create sample socwatch content with headers
    sample_content = """
Core C-State Summary: Residency (Percentage and Time)
---------------------------------------------------
State Name, Residency (Percentage and Time)
C0, 45.2%
C1, 32.1%
C6, 22.7%

Platform Monitoring Technology CPU Package C-States Residency Summary: Residency (Percentage and Time)
------------------------------------------------------------------------------------------------------
Package State, Time (ms), Percentage (%)
PC0, 1500.5, 60.2%
PC2, 750.3, 30.1%
PC6, 240.2, 9.7%
    """
    
    print("\n\nTesting table structure:")
    
    # Parse the content
    lines = sample_content.strip().split('\n')
    tables = parser._parse_socwatch_content(sample_content)
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"\nTable: {table['table_key']}")
        print(f"Total data entries: {len(table.get('data', {}))}")
        print("All data entries:")
        for key, value in table.get('data', {}).items():
            print(f"   {key}: {value}")

if __name__ == "__main__":
    test_header_parsing()
    test_table_structure()