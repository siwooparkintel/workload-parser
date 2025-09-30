#!/usr/bin/env python3
"""
Demonstration of the enhanced SocWatch parser with header information.

This demo shows how the enhanced parser now integrates table headers directly 
into the data dictionary, making the parsed data more self-documenting and 
easier to understand.

Features demonstrated:
- Header information integrated as first entry in data dictionary
- Column names and units captured from SocWatch CSV headers  
- Maintains natural order and grouping of SocWatch tables
"""

import sys
import json
from pathlib import Path

# Add the workload_parser to the path  
sys.path.insert(0, str(Path(__file__).parent))

from workload_parser.parsers.socwatch_parser import SocwatchParser

def demonstrate_enhanced_parser():
    """Demonstrate the enhanced parser capabilities."""
    parser = SocwatchParser()
    
    # Sample socwatch data content
    sample_content = """
Core C-State Summary: Residency (Percentage and Time)
---------------------------------------------------
State Name, Residency (Percentage and Time)
C0, 45.2%
C1, 32.1% 
C6, 22.7%

Temperature Metrics Summary - Sampled: Min/Max/Avg
-------------------------------------------------
Component Name, Min (°C), Max (°C), Avg (°C)
CPU Core 0, 35.2, 78.5, 52.3
CPU Core 1, 36.1, 79.2, 53.1
CPU Package, 38.5, 81.0, 55.7
    """
    
    print("=== Enhanced SocWatch Parser Demonstration ===\n")
    
    # Parse the content
    tables = parser._parse_socwatch_content(sample_content)
    
    for table in tables:
        print(f"📊 Table: {table['table_key']}")
        print(f"📝 Description: {table['table_info']['description']}")
        
        print("📈 Data (with integrated headers):")
        first_item = True
        for key, value in table['data'].items():
            if first_item:
                print(f"   📋 HEADER -> {key}: {value}")
                first_item = False
            else:
                print(f"   📊 DATA   -> {key}: {value}")
        
        print("-" * 50)

if __name__ == "__main__":
    demonstrate_enhanced_parser()