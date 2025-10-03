"""
Example: Parsing PCIe-only SocWatch Data
=========================================

This example demonstrates how to parse PCIe-only SocWatch data
(e.g., from UHX2_DC_006, UHX2_DC_007) using the workload-parser.

PCIe-only data occurs when the _osSession.etl file is missing,
resulting in CSV summaries that only contain PCIe hardware metrics.
"""

from pathlib import Path
from workload_parser.parsers import PCIeParser
import json


def example_1_basic_parsing():
    """Example 1: Basic PCIe data parsing"""
    print("=" * 60)
    print("Example 1: Basic PCIe Data Parsing")
    print("=" * 60)
    
    # Initialize the PCIe parser
    parser = PCIeParser()
    
    # Path to a PCIe-only SocWatch CSV file
    # This should be a CSV file in a directory with:
    # - workload_extraSession.etl
    # - workload_hwSession.etl
    # - workload_infoSession.etl
    # But WITHOUT workload_osSession.etl
    file_path = Path("path/to/UHX2_DC_006/workload.csv")
    
    # Check if this parser can handle the file
    if parser.can_parse(file_path):
        print(f"✓ File detected as PCIe-only SocWatch data: {file_path.name}")
        
        # Parse the file
        result = parser.parse(file_path)
        
        # Access the parsed data
        pcie_data = result['pcie_data']
        file_info = result['file_info']
        
        print(f"\n✓ Successfully parsed {len(pcie_data)} PCIe metrics")
        print(f"  File: {file_info['path']}")
        
        # Display some sample metrics
        print("\nSample Metrics:")
        for i, (key, value) in enumerate(pcie_data.items()):
            if i < 5:  # Show first 5 metrics
                print(f"  {key}: {value}")
            else:
                print(f"  ... and {len(pcie_data) - 5} more metrics")
                break
    else:
        print(f"✗ File is not PCIe-only SocWatch data: {file_path.name}")
        print("  This could mean:")
        print("  - _osSession.etl exists (full SocWatch data)")
        print("  - Missing required ETL files")
        print("  - File is not a CSV")


def example_2_extract_specific_metrics():
    """Example 2: Extract specific PCIe metrics"""
    print("\n" + "=" * 60)
    print("Example 2: Extract Specific Metrics")
    print("=" * 60)
    
    parser = PCIeParser()
    file_path = Path("path/to/UHX2_DC_006/workload.csv")
    
    if parser.can_parse(file_path):
        result = parser.parse(file_path)
        pcie_data = result['pcie_data']
        
        # Extract PCIe Link Power Management (LPM) metrics for NVM
        print("\nPCIe LPM Residency (NVM):")
        lpm_metrics = {k: v for k, v in pcie_data.items() if 'PCIe_LPM' in k}
        for key, value in lpm_metrics.items():
            state = key.split('_')[0]  # Extract state name (L0, L0s, L1, L2)
            print(f"  {state}: {value}%")
        
        # Extract PCIe Active metrics
        print("\nPCIe Link Activity:")
        active_metrics = {k: v for k, v in pcie_data.items() if 'PCIe_Active' in k}
        for key, value in active_metrics.items():
            print(f"  Active Time: {value}%")
        
        # Extract LTR Snoop histogram
        print("\nPCIe LTR Snoop Latency Distribution:")
        ltr_metrics = {k: v for k, v in pcie_data.items() if 'PCIe_LTRsnoop' in k}
        for key, value in ltr_metrics.items():
            latency_bucket = key.split('_')[0]
            print(f"  {latency_bucket}: {value}%")


def example_3_batch_processing():
    """Example 3: Process multiple directories with PCIe-only data"""
    print("\n" + "=" * 60)
    print("Example 3: Batch Processing")
    print("=" * 60)
    
    parser = PCIeParser()
    
    # List of directories to process
    directories = [
        Path("path/to/UHX2_DC_006"),
        Path("path/to/UHX2_DC_007"),
        Path("path/to/other_dataset")
    ]
    
    results = []
    
    for directory in directories:
        print(f"\nProcessing: {directory.name}")
        
        # Find CSV files in the directory
        csv_files = list(directory.glob("*.csv"))
        
        for csv_file in csv_files:
            if parser.can_parse(csv_file):
                try:
                    result = parser.parse(csv_file)
                    results.append({
                        'dataset': directory.name,
                        'file': csv_file.name,
                        'metrics': result['pcie_data'],
                        'status': 'success'
                    })
                    print(f"  ✓ {csv_file.name}: {len(result['pcie_data'])} metrics")
                except Exception as e:
                    results.append({
                        'dataset': directory.name,
                        'file': csv_file.name,
                        'status': 'error',
                        'error': str(e)
                    })
                    print(f"  ✗ {csv_file.name}: {str(e)}")
    
    # Summary
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'error'])
    
    print(f"\n" + "=" * 60)
    print(f"Summary: {successful} successful, {failed} failed")
    print("=" * 60)


def example_4_custom_config():
    """Example 4: Using custom PCIe target configuration"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)
    
    # Custom configuration with additional devices
    custom_config = {
        'encoding': 'utf-8',
        'delimiter': ',',
        # Add custom config options here
    }
    
    # Initialize parser with custom config
    parser = PCIeParser(config=custom_config)
    
    # Load current targets
    targets = parser._load_pcie_targets()
    
    print("\nCurrent PCIe Targets:")
    for target in targets:
        print(f"  - {target['key']}")
        print(f"    Lookup: {target['lookup']}")
        print(f"    Devices: {', '.join(target['devices'])}")
    
    print("\nTo customize targets, edit: config/pcie_targets_default.json")


def example_5_validate_and_check():
    """Example 5: Validation and checking"""
    print("\n" + "=" * 60)
    print("Example 5: Data Validation")
    print("=" * 60)
    
    parser = PCIeParser()
    
    # Valid data structure
    valid_data = {
        'pcie_data': {
            'L0 (%)_NVM        PCIe_LPM': '95.2',
            'L1 (%)_NVM        PCIe_LPM': '2.5'
        },
        'file_info': {'path': '/some/path'}
    }
    
    # Invalid data structure (missing pcie_data)
    invalid_data = {
        'file_info': {'path': '/some/path'}
    }
    
    print("\nValidating data structures:")
    print(f"  Valid data: {parser.validate_data(valid_data)}")
    print(f"  Invalid data: {parser.validate_data(invalid_data)}")
    
    # Check file detection
    test_path = Path("path/to/test.csv")
    print(f"\nFile detection for {test_path}:")
    print(f"  Can parse: {parser.can_parse(test_path)}")


def example_6_export_to_json():
    """Example 6: Export parsed data to JSON"""
    print("\n" + "=" * 60)
    print("Example 6: Export to JSON")
    print("=" * 60)
    
    parser = PCIeParser()
    file_path = Path("path/to/UHX2_DC_006/workload.csv")
    
    if parser.can_parse(file_path):
        result = parser.parse(file_path)
        
        # Export to JSON file
        output_file = Path("pcie_data.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✓ Exported PCIe data to: {output_file}")
        print(f"  Metrics: {len(result['pcie_data'])}")
        
        # Pretty print sample
        print("\nJSON Structure:")
        print(json.dumps(result, indent=2)[:500] + "...")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("PCIe-Only SocWatch Data Parsing Examples")
    print("=" * 60)
    print("\nNote: These are demonstration examples.")
    print("Update file paths to match your actual data locations.\n")
    
    # Run examples (comment out the ones you don't need)
    try:
        example_1_basic_parsing()
    except Exception as e:
        print(f"Example 1 error: {e}")
    
    try:
        example_2_extract_specific_metrics()
    except Exception as e:
        print(f"Example 2 error: {e}")
    
    try:
        example_3_batch_processing()
    except Exception as e:
        print(f"Example 3 error: {e}")
    
    try:
        example_4_custom_config()
    except Exception as e:
        print(f"Example 4 error: {e}")
    
    try:
        example_5_validate_and_check()
    except Exception as e:
        print(f"Example 5 error: {e}")
    
    try:
        example_6_export_to_json()
    except Exception as e:
        print(f"Example 6 error: {e}")


if __name__ == "__main__":
    main()
