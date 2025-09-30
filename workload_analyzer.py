"""
Workload Analyzer - Comprehensive workload data parsing and analysis tool

This script parses workload data from baseline directories containing:
- Power measurement files (PACS summary)
- ETL trace files 
- Socwatch monitoring data
- Model output files

Generates detailed Excel reports with performance metrics, timing analysis,
and comprehensive data extraction from multiple file formats.
"""
import sys
import os
import time
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workload_parser import WorkloadParser

def main():
    # Start timing the entire process
    start_time = time.time()
    print(f"Starting workload parsing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Network path to the baseline directory
    baseline_path = r"\\10.54.63.126\Pnpext\Siwoo\data\WW2533.2_CataV3ITCCAUHX2_DCBAL\Baseline"
    
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
    
    # Parse all files in the baseline directory
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
        elif parser_name == 'etl':
            print(f"   ETL file processed")
    
    # Analyze folder types
    print(f"\nFolder Analysis by Collection Type:")
    
    # Group by folder
    folders = {}
    for result in results:
        file_path = result.get('_metadata', {}).get('file_path', '')
        parser_name = result.get('_metadata', {}).get('parser_name', '')
        
        # Extract folder name (UHX2_DC_XXX)
        folder_name = None
        path_parts = file_path.replace('\\', '/').split('/')
        for part in path_parts:
            if part.startswith('UHX2_DC_'):
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
        else:
            print(f"{folder_name}: Other combination - Parsers: {parsers_list}")
    
    print(f"\nSummary by Collection Type:")
    print(f"Power-only folders ({len(power_only)}): {power_only}")
    print(f"ETL+Power folders ({len(etl_power)}): {etl_power}")
    print(f"Socwatch+Power folders ({len(socwatch_power)}): {socwatch_power}")
    
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
    
    print(f"\nTotal baseline folders found: {len(folders)}")
    print(f"Successfully parsed files: {len(results)}")
    
    # Generate Excel report
    generate_excel_report(results, folders, start_time)

def generate_excel_report(results, folders_info, start_time):
    """Generate Excel report in vertical format matching reference with DAQ targets order"""
    
    # Load DAQ targets order from config
    config_path = Path('config/enhanced_parser_config.json')
    daq_targets_order = []
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                daq_targets_order = list(config.get('daq_targets', {}).keys())
        except Exception as e:
            print(f"Warning: Could not load config for DAQ targets order: {e}")
    
    # Organize data by folder
    folder_data = {}
    all_metrics = []  # Use list to preserve order instead of set
    
    # Group results by folder and collect all metrics
    for result in results:
        file_path = result.get('_metadata', {}).get('file_path', '')
        parser_name = result.get('_metadata', {}).get('parser_name', '')
        
        # Extract folder name
        folder_name = None
        path_parts = file_path.replace('\\', '/').split('/')
        for part in path_parts:
            if part.startswith('UHX2_DC_'):
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
                            folder_data[folder_name][power_metric] = power_value
                            if power_metric not in all_metrics:  # Preserve order, avoid duplicates
                                all_metrics.append(power_metric)
                    elif key == 'socwatch_data' and isinstance(value, dict):
                        # Extract individual socwatch metrics from socwatch_data dictionary
                        for socwatch_metric, socwatch_value in value.items():
                            folder_data[folder_name][socwatch_metric] = socwatch_value
                            if socwatch_metric not in all_metrics:  # Preserve order, avoid duplicates
                                all_metrics.append(socwatch_metric)
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
    
    # Create .testdata directory if it doesn't exist
    testdata_dir = Path('.testdata')
    testdata_dir.mkdir(exist_ok=True)
    
    # Generate timestamped filename in .testdata folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = testdata_dir / f'baseline_analysis_vertical_{timestamp}.xlsx'
    
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
    main()