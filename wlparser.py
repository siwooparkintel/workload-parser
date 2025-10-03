"""
Workload Analyzer - Comprehensive workload data parsing and analysis tool

This script parses workload data from directories containing:
- Power measurement files (PACS summary with auto-detection of P_* rails)
- ETL trace files 
- Socwatch monitoring data
- Model output files

Features:
- **Standalone Executable**: Can be built as wlparser.exe with all dependencies bundled
- **GUI Folder Browser**: Interactive folder selection when no path provided
- **Auto-Detection Mode**: Automatically detects all P_* power rails from power summary
- **DAQ Config Mode**: Use predefined power rail targets from DAQ configuration
- **Comprehensive Output**: Generates detailed Excel reports with metrics and timing

Usage:
  # GUI mode (folder browser)
  wlparser.exe
  
  # Auto-detect all P_* power rails
  wlparser.exe -i "path/to/workload/data"
  
  # Use DAQ config for specific power rails
  wlparser.exe -i "path/to/data" -d config/daq_targets_default.json
"""
import sys
import os
import time
import json
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workload_parser import WorkloadParser

def get_last_folder():
    """Get the last used folder from config file"""
    config_file = Path.home() / '.workload_parser_last_folder'
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                last_folder = f.read().strip()
                if os.path.exists(last_folder):
                    return last_folder
        except:
            pass
    return os.path.expanduser("~")

def save_last_folder(folder_path):
    """Save the last used folder to config file"""
    try:
        config_file = Path.home() / '.workload_parser_last_folder'
        with open(config_file, 'w') as f:
            f.write(folder_path)
    except:
        pass  # Silently fail if we can't save

def select_folder_gui():
    """Open a GUI folder selection dialog"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create root window and hide it
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        # Get last used folder or default to home
        initial_dir = get_last_folder()
        
        # Open folder selection dialog
        folder_path = filedialog.askdirectory(
            title="Select Workload Data Folder",
            initialdir=initial_dir
        )
        
        root.destroy()
        
        # Save the selected folder for next time
        if folder_path:
            save_last_folder(folder_path)
        
        return folder_path
    except ImportError:
        print("ERROR: tkinter is not available. Please install tkinter or use -i option.")
        return None
    except Exception as e:
        print(f"ERROR: Failed to open folder dialog: {e}")
        return None

def main(baseline_path=None, output_dir=None, daq_config_path=None):
    """
    Main function to parse workload data and generate Excel report
    
    Args:
        baseline_path: Path to workload data directory. If None, will use GUI to select folder.
        output_dir: Output directory for Excel report. If None, uses input directory.
        daq_config_path: Path to DAQ targets config JSON file. If None, auto-detect power rails.
    """
    # Start timing the entire process
    start_time = time.time()
    print(f"Starting workload parsing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # If no path provided, use GUI folder selector
    if baseline_path is None:
        print("No folder path provided. Opening folder selection dialog...")
        baseline_path = select_folder_gui()
        
        if not baseline_path:
            print("ERROR: No folder selected. Exiting.")
            return None
        
        print(f"Selected folder: {baseline_path}")
        print("=" * 80)
    
    # Validate path exists
    if not os.path.exists(baseline_path):
        print(f"ERROR: Path does not exist: {baseline_path}")
        return None
    
    # Initialize parser and disable power_trace parser
    parser = WorkloadParser()
    print(f"Initial enabled parsers: {parser.config.get_enabled_parsers()}")
    
    # Disable power_trace parser as requested
    if 'parsers' not in parser.config._config:
        parser.config._config['parsers'] = {}
    if 'power_trace' not in parser.config._config['parsers']:
        parser.config._config['parsers']['power_trace'] = {}
    parser.config._config['parsers']['power_trace']['enabled'] = False
    
    print(f"After disabling power_trace: {parser.config.get_enabled_parsers()}")
    
    # Parse all files in the directory
    results = parser.parse_directory(baseline_path)
    
    print(f"\nParsing Results:")
    print(f"Total files parsed: {len(results)}")
    
    # Display results
    for i, result in enumerate(results, 1):
        file_path = result.get('_metadata', {}).get('file_path', 'Unknown')
        parser_name = result.get('_metadata', {}).get('parser_name', 'Unknown')
        
        print(f"{i}. {file_path} - Parser: {parser_name}")
        
        # Show sample metrics
        if parser_name == 'power':
            # Extract power metrics from power_data dictionary
            power_data = result.get('power_data', {})
            print(f"   Power metrics extracted: {len(power_data)}")
        elif parser_name == 'socwatch':
            # Extract socwatch metrics from socwatch_data dictionary
            socwatch_data = result.get('socwatch_data', {})
            print(f"   Socwatch metrics extracted: {len(socwatch_data)}")
        elif parser_name == 'pcie':
            # Extract PCIe metrics from pcie_data dictionary
            pcie_data = result.get('pcie_data', {})
            print(f"   PCIe metrics extracted: {len(pcie_data)}")
        elif parser_name == 'etl':
            print(f"   ETL file processed")
    
    # Analyze folder types
    print(f"\nFolder Analysis by Collection Type:")
    
    # Group by folder
    folders = {}
    for result in results:
        file_path = result.get('_metadata', {}).get('file_path', '')
        parser_name = result.get('_metadata', {}).get('parser_name', '')
        
        # Extract folder name - look for common patterns like UHX2_DC_XXX or CataV3_XXX_XXX
        folder_name = None
        path_parts = file_path.replace('\\', '/').split('/')
        
        # Try to find a folder that looks like a test directory
        # Common patterns: UHX2_DC_XXX, CataV3_XXX_XXX, or any folder ending with _XXX where XXX is digits
        import re
        for part in path_parts:
            # Match patterns like: UHX2_DC_000, CataV3_PCDfix_000, etc.
            if re.search(r'_\d{3}$', part) or part.startswith('UHX2_DC_') or part.startswith('CataV3_'):
                folder_name = part
                break
        
        if folder_name:
            if folder_name not in folders:
                folders[folder_name] = set()
            folders[folder_name].add(parser_name)
    
    # Categorize folders
    power_only = []
    etl_power = []
    socwatch_power = []
    pcie_power = []
    
    for folder_name, parsers in sorted(folders.items()):
        parsers_list = sorted(list(parsers))
        if parsers == {'power'}:
            power_only.append(folder_name)
            print(f"{folder_name}: Power-only - Parsers: {parsers_list}")
        elif 'etl' in parsers and 'power' in parsers:
            etl_power.append(folder_name)
            print(f"{folder_name}: ETL+Power - Parsers: {parsers_list}")
        elif 'socwatch' in parsers and 'power' in parsers:
            socwatch_power.append(folder_name)
            print(f"{folder_name}: Socwatch+Power - Parsers: {parsers_list}")
        elif 'pcie' in parsers and 'power' in parsers:
            pcie_power.append(folder_name)
            print(f"{folder_name}: PCIe+Power - Parsers: {parsers_list}")
        else:
            print(f"{folder_name}: Other combination - Parsers: {parsers_list}")
    
    print(f"\nSummary by Collection Type:")
    print(f"Power-only folders ({len(power_only)}): {power_only}")
    print(f"ETL+Power folders ({len(etl_power)}): {etl_power}")
    print(f"Socwatch+Power folders ({len(socwatch_power)}): {socwatch_power}")
    print(f"PCIe+Power folders ({len(pcie_power)}): {pcie_power}")
    
        # Show sample metrics
    if results:
        print(f"\nSample Power Metrics Available:")
        for result in results:
            if result.get('_metadata', {}).get('parser_name') == 'power':
                # Extract power metrics from power_data dictionary
                power_data = result.get('power_data', {})
                for metric, value in list(power_data.items())[:25]:  # Show first 25 metrics
                    print(f"  {metric}: {value}")
                break
    
    print(f"\nTotal workload folders found: {len(folders)}")
    print(f"Successfully parsed files: {len(results)}")
    
    # Generate Excel report
    return generate_excel_report(results, folders, start_time, baseline_path, output_dir, daq_config_path)

def generate_excel_report(results, folders_info, start_time, baseline_path, output_dir=None, daq_config_path=None):
    """Generate Excel report in vertical format matching reference with DAQ targets order
    
    Args:
        results: Parsing results
        folders_info: Folder information
        start_time: Start time of processing
        baseline_path: Path to input directory
        output_dir: Output directory for Excel report. If None, uses input directory.
        use_daq_config: If True, use DAQ targets from config. If False, auto-detect power rails.
    """
    
    # Check if we have any results
    if not results:
        print("\nERROR: No data to export. No files were successfully parsed.")
        return None
    
    # Determine which metrics to include
    daq_targets_order = []
    if daq_config_path:
        # Load DAQ targets order from specified config file
        config_file = Path(daq_config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                    # Handle both enhanced config format and simple config format
                    if 'daq_targets' in config:
                        # Enhanced config format
                        daq_targets_order = list(config.get('daq_targets', {}).keys())
                    else:
                        # Simple config format (like daq_targets_default.json)
                        daq_targets_order = list(config.keys())
                print(f"Using DAQ targets from {config_file}: {len(daq_targets_order)} metrics")
            except Exception as e:
                print(f"Warning: Could not load config from {daq_config_path}: {e}")
                print("Falling back to auto-detection...")
                daq_config_path = None  # Fall back to auto-detection
    
    if not daq_config_path:
        # Auto-detect power rails from power summary files (exclude V_* and I_* rails)
        print("Auto-detecting power rails from power summary files...")
        power_rails = []  # Use list to preserve natural order
        for result in results:
            if result.get('_metadata', {}).get('parser_name') == 'power':
                power_data = result.get('power_data', {})
                for key in power_data.keys():
                    # Only include P_* rails, exclude V_* (voltage) and I_* (current)
                    if key.startswith('P_') and not key.startswith(('V_', 'I_')):
                        if key not in power_rails:  # Avoid duplicates while preserving order
                            power_rails.append(key)
        
        # Keep natural order from power summary, add Run Time at the end
        daq_targets_order = power_rails.copy()
        if 'Run Time' not in daq_targets_order:
            daq_targets_order.append('Run Time')
        
        print(f"Auto-detected {len(power_rails)} power rails (P_*) + Run Time")
        print(f"Power rails: {', '.join(power_rails[:5])}{'...' if len(power_rails) > 5 else ''}")
    
    # Organize data by folder
    folder_data = {}
    all_metrics = []  # Use list to preserve order instead of set
    
    # Group results by folder and collect all metrics
    import re
    for result in results:
        file_path = result.get('_metadata', {}).get('file_path', '')
        parser_name = result.get('_metadata', {}).get('parser_name', '')
        
        # Extract folder name - look for common patterns
        folder_name = None
        path_parts = file_path.replace('\\', '/').split('/')
        
        # Try to find a folder that looks like a test directory
        for part in path_parts:
            # Match patterns like: UHX2_DC_000, CataV3_PCDfix_000, etc.
            if re.search(r'_\d{3}$', part) or part.startswith('UHX2_DC_') or part.startswith('CataV3_'):
                folder_name = part
                break
        
        if folder_name:
            if folder_name not in folder_data:
                folder_data[folder_name] = {}
            
            # Add all non-metadata metrics
            for key, value in result.items():
                if not key.startswith('_'):
                    if key == 'power_data' and isinstance(value, dict):
                        # Extract individual power metrics from power_data dictionary
                        for power_metric, power_value in value.items():
                            # Filter out internal metrics (starting with _)
                            if power_metric.startswith('_'):
                                continue  # Skip internal metrics like _soc_power
                            
                            # If using DAQ config, ONLY include metrics from daq_targets_order
                            if daq_config_path:
                                if power_metric in daq_targets_order:
                                    folder_data[folder_name][power_metric] = power_value
                                    if power_metric not in all_metrics:  # Preserve order, avoid duplicates
                                        all_metrics.append(power_metric)
                            # Otherwise (auto-detection), include P_* rails only (exclude V_* and I_*)
                            elif not (power_metric.startswith('V_') or power_metric.startswith('I_')):
                                folder_data[folder_name][power_metric] = power_value
                                if power_metric not in all_metrics:  # Preserve order, avoid duplicates
                                    all_metrics.append(power_metric)
                    elif key == 'socwatch_data' and isinstance(value, dict):
                        # Extract individual socwatch metrics from socwatch_data dictionary
                        for socwatch_metric, socwatch_value in value.items():
                            folder_data[folder_name][socwatch_metric] = socwatch_value
                            if socwatch_metric not in all_metrics:  # Preserve order, avoid duplicates
                                all_metrics.append(socwatch_metric)
                    elif key == 'pcie_data' and isinstance(value, dict):
                        # Extract individual PCIe metrics from pcie_data dictionary
                        for pcie_metric, pcie_value in value.items():
                            folder_data[folder_name][pcie_metric] = pcie_value
                            if pcie_metric not in all_metrics:  # Preserve order, avoid duplicates
                                all_metrics.append(pcie_metric)
                    else:
                        # Handle file_info fields - extract just the path value
                        if key in ['file_info', 'etl_file_info', 'socwatch_file_info'] and isinstance(value, dict):
                            # Extract path from file_info dictionary
                            path_value = value.get('path', str(value))  # Fallback to string representation if no path
                            
                            # Create unique metric names for different parsers
                            if parser_name == 'power':
                                metric_name = key
                            elif parser_name == 'socwatch':
                                metric_name = f"socwatch_{key}"
                            else:
                                metric_name = f"{parser_name}_{key}"
                            
                            folder_data[folder_name][metric_name] = path_value
                        else:
                            # Create unique metric names for different parsers
                            if parser_name == 'power':
                                metric_name = key
                            elif parser_name == 'socwatch':
                                metric_name = f"socwatch_{key}"
                            else:
                                metric_name = f"{parser_name}_{key}"
                            
                            folder_data[folder_name][metric_name] = value
                        
                        if metric_name not in all_metrics:  # Preserve order, avoid duplicates
                            all_metrics.append(metric_name)
    
    # Check if we found any folders
    if not folder_data:
        print("\nWARNING: No workload folders detected in the parsed files.")
        print("This usually means the folder naming pattern is not recognized.")
        print("Looking for folders with patterns like: UHX2_DC_XXX, CataV3_XXX_XXX, or ending with _###")
        print("\nERROR: Cannot generate Excel report without folder data.")
        return None
    
    # Keep original folder order (no sorting)
    sorted_folders = list(folder_data.keys())
    
    # Order metrics according to DAQ targets configuration, preserve natural discovery order for others
    daq_metrics = [metric for metric in daq_targets_order if metric in all_metrics]
    other_metrics = [metric for metric in all_metrics if metric not in daq_targets_order]
    sorted_metrics = daq_metrics + other_metrics
    
    # Create horizontal format DataFrame (folders as rows, metrics as columns)
    horizontal_data = []
    
    for folder_name in sorted_folders:
        row_data = {'Folder': folder_name}
        
        # Add all metrics as columns
        for metric in sorted_metrics:
            value = folder_data[folder_name].get(metric, '')
            # Format numeric values
            if isinstance(value, (int, float)) and value != '':
                try:
                    value = float(value)
                except:
                    pass
            row_data[metric] = value
        
        horizontal_data.append(row_data)
    
    # Create horizontal DataFrame
    df_horizontal = pd.DataFrame(horizontal_data)
    
    # Create vertical format using transpose for Excel output
    # First, set Folder as index for proper transposition
    df_horizontal_indexed = df_horizontal.set_index('Folder')
    
    # Transpose to get metrics as rows and folders as columns
    df_vertical = df_horizontal_indexed.transpose()
    
    # Add header rows for the vertical format
    # Create header rows as lists to match the vertical structure
    header_rows = []
    
    # Data label row
    data_label_row = ['Data label'] + ['WW2533.2_CataV3ITCCAUHX2_DCBAL'] * len(sorted_folders)
    header_rows.append(data_label_row)
    
    # Condition row
    condition_row = ['Condition'] + ['Baseline'] * len(sorted_folders)
    header_rows.append(condition_row)
    
    # Create column names: 'Data label' + folder names
    column_names = ['Data label'] + list(df_vertical.columns)
    
    # Convert transposed DataFrame to list of lists for easier concatenation
    metric_rows = []
    for index, row in df_vertical.iterrows():
        metric_row = [index] + list(row.values)
        metric_rows.append(metric_row)
    
    # Combine all rows
    all_rows = header_rows + metric_rows
    
    # Create final DataFrame
    df = pd.DataFrame(all_rows, columns=column_names)
    
    # Determine output directory
    if output_dir is None:
        # Use input directory as output directory
        output_path = Path(baseline_path)
    else:
        output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped filename in output folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = output_path / f'workload_analysis_{timestamp}.xlsx'
    
    # Write Excel file
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Main sheet with vertical format
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        
        # Summary sheet
        summary_data = []
        folders_by_type = {}
        
        for folder_name, parsers in folders_info.items():
            parsers_list = sorted(list(parsers))
            if parsers == {'power'}:
                folder_type = 'Power-only'
            elif 'etl' in parsers and 'power' in parsers:
                folder_type = 'ETL+Power'
            elif 'socwatch' in parsers and 'power' in parsers:
                folder_type = 'Socwatch+Power'
            else:
                folder_type = 'Other'
            
            if folder_type not in folders_by_type:
                folders_by_type[folder_type] = []
            folders_by_type[folder_type].append(folder_name)
        
        # Summary statistics
        summary_data.append({'Metric': 'Total_Folders', 'Value': len(sorted_folders)})
        summary_data.append({'Metric': 'Total_Metrics', 'Value': len(sorted_metrics)})
        summary_data.append({'Metric': 'Total_Files_Parsed', 'Value': len(results)})
        
        for folder_type, folder_list in folders_by_type.items():
            summary_data.append({'Metric': f'{folder_type}_Count', 'Value': len(folder_list)})
            summary_data.append({'Metric': f'{folder_type}_Folders', 'Value': ', '.join(sorted(folder_list))})
        
        summary_data.append({'Metric': 'Analysis_Timestamp', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\nExcel report generated: {excel_filename}")
    
    # Calculate and display total processing time
    end_time = time.time()
    total_time = end_time - start_time
    minutes, seconds = divmod(total_time, 60)
    
    print("=" * 80)
    print(f"Processing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total processing time: {int(minutes):02d}:{seconds:05.2f}")
    print(f"Performance summary:")
    print(f"  - Files processed: {len(results)}")
    print(f"  - Folders analyzed: {len(sorted_folders)}")
    print(f"  - Metrics extracted: {len(sorted_metrics)}")
    print(f"  - Processing rate: {len(results)/total_time:.2f} files/second")
    print("=" * 80)
    
    return excel_filename

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Workload Parser - Parse and analyze workload data from directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\nExamples:
  python wlparser.py
      Opens a GUI folder browser to select the workload data directory
      Auto-detects all P_* power rails and Run Time from power summary files
  
  python wlparser.py -i "C:\\path\\to\\data"
      Analyzes the specified workload data directory with auto-detected power rails
      (output saved to C:\\path\\to\\data)
  
  python wlparser.py -i "\\\\server\\share\\data" -o "C:\\reports" -d config/daq_targets_default.json
      Analyzes a network workload directory using DAQ targets from specified config file
      and saves report to C:\\reports
        """
    )
    parser.add_argument(
        '-i', '--input',
        dest='baseline_path',
        type=str,
        help='Path to workload data directory'
    )
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        type=str,
        help='Output directory for Excel report (default: same as input directory)'
    )
    parser.add_argument(
        '-d', '--daq-config',
        dest='daq_config_path',
        type=str,
        default=None,
        help='Path to DAQ targets config JSON file. If not specified, auto-detects all P_* power rails and Run Time'
    )
    
    args = parser.parse_args()
    
    # Run main with provided path (or None to trigger GUI)
    main(args.baseline_path, args.output_dir, args.daq_config_path)