"""
Integration tests for processing real workload data from network share.

This test suite processes all subfolders in the data directory and validates
the parser's performance on different datasets.

Data Location: \\10.54.63.126\Pnpext\Siwoo\data
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workload_parser import WorkloadParser


class DataIntegrationTester:
    """
    Comprehensive integration tester for workload parser.
    
    Processes all subfolders in a data directory and generates detailed reports
    about parser performance, success rates, and any issues encountered.
    """
    
    def __init__(self, data_root: str, output_dir: str = None):
        """
        Initialize the integration tester.
        
        Args:
            data_root: Root directory containing workload data subfolders
            output_dir: Directory for test results (default: ./test_results)
        """
        self.data_root = Path(data_root)
        self.output_dir = Path(output_dir or "./test_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.summary = {
            'total_folders': 0,
            'successful': 0,
            'failed': 0,
            'warnings': 0,
            'total_time': 0,
            'start_time': None,
            'end_time': None
        }
        
    def validate_data_root(self) -> bool:
        """Validate that the data root exists and is accessible."""
        if not self.data_root.exists():
            print(f"❌ ERROR: Data root not found: {self.data_root}")
            print(f"   Please ensure the network share is mounted.")
            return False
        
        if not self.data_root.is_dir():
            print(f"❌ ERROR: Data root is not a directory: {self.data_root}")
            return False
        
        print(f"✅ Data root validated: {self.data_root}")
        return True
    
    def find_workload_folders(self, max_depth: int = 3) -> List[Path]:
        """
        Find all workload data folders recursively in the data root.
        
        A folder is considered a workload if it:
        - Contains data files directly (CSV, ETL, TXT, LOG)
        - Has subdirectories with PACS summary files or typical workload structure
        
        Args:
            max_depth: Maximum depth to search (default 3 levels)
        
        Returns:
            List of paths to workload folders
        """
        workload_folders = []
        
        print(f"\n🔍 Scanning for workload folders recursively (max depth: {max_depth}) in: {self.data_root}")
        
        def is_workload_folder(folder: Path, depth: int) -> bool:
            """Check if a folder contains workload data."""
            if depth > max_depth:
                return False
            
            try:
                # Check for direct data files
                data_files = list(folder.glob("*.csv")) + list(folder.glob("*.etl")) + \
                            list(folder.glob("*.txt")) + list(folder.glob("*.log"))
                
                # Check for PACS summary files (strong indicator of workload data)
                pacs_files = list(folder.rglob("*pacs-summary.csv"))
                
                # Check for socwatch data
                socwatch_files = list(folder.glob("socwatch/*.csv"))
                
                # It's a workload if it has direct data files OR pacs/socwatch subdirs
                has_workload_data = (len(data_files) > 0) or (len(pacs_files) > 0) or (len(socwatch_files) > 0)
                
                return has_workload_data
                
            except (PermissionError, OSError):
                return False
        
        def scan_recursive(current_path: Path, depth: int = 0):
            """Recursively scan for workload folders."""
            if depth > max_depth:
                return
            
            try:
                subdirs = [item for item in current_path.iterdir() if item.is_dir()]
                
                # Check each subdirectory
                for subdir in subdirs:
                    try:
                        if is_workload_folder(subdir, depth + 1):
                            # Get relative path for display
                            rel_path = subdir.relative_to(self.data_root)
                            workload_folders.append(subdir)
                            print(f"   {'  ' * depth}✓ Found: {rel_path}")
                        else:
                            # Continue scanning deeper if this isn't a workload folder
                            scan_recursive(subdir, depth + 1)
                    except (PermissionError, OSError) as e:
                        rel_path = subdir.relative_to(self.data_root)
                        print(f"   {'  ' * depth}⚠️  Cannot access {rel_path}: {e}")
                        
            except (PermissionError, OSError) as e:
                print(f"   {'  ' * depth}⚠️  Cannot scan {current_path.name}: {e}")
        
        try:
            # Start recursive scan from data root
            scan_recursive(self.data_root, 0)
        
        except (PermissionError, OSError) as e:
            print(f"❌ ERROR: Cannot access data root: {e}")
            return []
        
        print(f"\n📊 Found {len(workload_folders)} workload folders to test")
        return workload_folders
    
    def test_single_folder(self, folder_path: Path, daq_config_path: str = None) -> Dict[str, Any]:
        """
        Test parsing a single workload folder.
        
        Args:
            folder_path: Path to workload data folder
            daq_config_path: Optional DAQ configuration file path
            
        Returns:
            Dictionary with test results
        """
        result = {
            'folder_name': folder_path.name,
            'folder_path': str(folder_path),
            'status': 'unknown',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': 0,
            'output_file': None,
            'error': None,
            'warnings': [],
            'stats': {
                'files_found': 0,
                'files_parsed': 0,
                'power_rails_detected': 0,
                'output_size_kb': 0
            }
        }
        
        start_time = time.time()
        
        try:
            print(f"\n{'='*80}")
            print(f"Testing: {folder_path.name}")
            print(f"{'='*80}")
            
            # Count files in folder
            file_count = sum(1 for _ in folder_path.rglob("*") if _.is_file())
            result['stats']['files_found'] = file_count
            print(f"   Files in folder: {file_count}")
            
            # Note: Parser generates its own filename with pattern workload_analysis_YYYYMMDD_HHMMSS.xlsx
            # We just specify the output directory
            print(f"   Parsing with {'DAQ config' if daq_config_path else 'auto-detection mode'}...")
            
            # Run parser - it will create output file with its own naming convention
            parse_success, output_file_path, file_size_kb = self._run_parser(folder_path, self.output_dir, daq_config_path)
            
            if parse_success:
                # Update result with actual output file info
                if output_file_path and file_size_kb > 0:
                    result['status'] = 'success'
                    result['output_file'] = output_file_path
                    result['stats']['output_size_kb'] = file_size_kb
                    output_name = Path(output_file_path).name
                    print(f"   ✅ Output created: {output_name} ({file_size_kb:.1f} KB)")
                else:
                    result['status'] = 'warning'
                    result['warnings'].append("Output file not found")
                    print(f"   ⚠️  Warning: Output file not found")
            else:
                result['status'] = 'failed'
                result['error'] = "Parser returned failure"
                print(f"   ❌ Parsing failed")
        
        except PermissionError as e:
            result['status'] = 'failed'
            result['error'] = f"Permission denied: {str(e)}"
            print(f"   ❌ Permission denied: {e}")
        
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            print(f"   ❌ Error: {e}")
        
        finally:
            end_time = time.time()
            result['duration_seconds'] = round(end_time - start_time, 2)
            result['end_time'] = datetime.now().isoformat()
            print(f"   ⏱️  Duration: {result['duration_seconds']:.2f} seconds")
        
        return result
    
    def _run_parser(self, folder_path: Path, output_dir: Path, daq_config_path: str = None) -> tuple:
        """
        Run the parser on a folder using the actual wlparser.py main function.
        
        Args:
            folder_path: Path to workload data folder
            output_dir: Directory where output files will be created
            daq_config_path: Optional DAQ configuration file path
            
        Returns:
            tuple: (success: bool, output_file_path: str or None, file_size_kb: float)
        """
        try:
            # Import the main function from wlparser.py
            import wlparser
            
            # Record files before parsing to identify new output
            existing_files = set(output_dir.glob("workload_analysis_*.xlsx"))
            
            # Call the main function with the appropriate parameters
            # Suppress GUI folder selection by providing baseline_path
            wlparser.main(
                baseline_path=str(folder_path),
                output_dir=str(output_dir),
                daq_config_path=daq_config_path
            )
            
            # Find newly created files
            current_files = set(output_dir.glob("workload_analysis_*.xlsx"))
            new_files = current_files - existing_files
            
            if new_files:
                # Use the most recent new file
                most_recent = max(new_files, key=lambda p: p.stat().st_mtime)
                size_kb = most_recent.stat().st_size / 1024
                return (True, str(most_recent), size_kb)
            
            return (False, None, 0)
            
        except Exception as e:
            print(f"      Parser error: {e}")
            import traceback
            traceback.print_exc()
            return (False, None, 0)
    
    def run_all_tests(self, daq_config_path: str = None, max_folders: int = None, excel_enabled: bool = False) -> None:
        """
        Run tests on all workload folders.
        
        Args:
            daq_config_path: Optional DAQ configuration file path
            max_folders: Optional limit on number of folders to test
            excel_enabled: If True, generate Excel report in addition to JSON (default: False)
        """
        print("\n" + "="*80)
        print("WORKLOAD PARSER INTEGRATION TEST SUITE")
        print("="*80)
        
        self.summary['start_time'] = datetime.now().isoformat()
        start_time = time.time()
        
        # Validate data root
        if not self.validate_data_root():
            return
        
        # Find workload folders
        folders = self.find_workload_folders()
        
        if not folders:
            print("\n❌ No workload folders found to test!")
            return
        
        # Limit number of folders if specified
        if max_folders and len(folders) > max_folders:
            print(f"\n⚠️  Limiting test to first {max_folders} folders (found {len(folders)})")
            folders = folders[:max_folders]
        
        self.summary['total_folders'] = len(folders)
        
        # Test each folder
        print(f"\n🚀 Starting tests on {len(folders)} folders...")
        
        for idx, folder in enumerate(folders, 1):
            print(f"\n[{idx}/{len(folders)}] ", end="")
            result = self.test_single_folder(folder, daq_config_path)
            self.results.append(result)
            
            # Update summary
            if result['status'] == 'success':
                self.summary['successful'] += 1
            elif result['status'] == 'failed':
                self.summary['failed'] += 1
            elif result['status'] == 'warning':
                self.summary['warnings'] += 1
        
        # Calculate total time
        end_time = time.time()
        self.summary['total_time'] = round(end_time - start_time, 2)
        self.summary['end_time'] = datetime.now().isoformat()
        
        # Generate reports
        self.generate_reports()
    
    def generate_reports(self) -> None:
        """Generate test result reports (JSON format)."""
        print("\n" + "="*80)
        print("GENERATING TEST REPORTS")
        print("="*80)
        
        # Save JSON report (always generated)
        json_report = self.output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'summary': self.summary,
            'results': self.results
        }
        
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"   ✅ JSON report: {json_report}")
        
        # Print summary to console
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test summary to console."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total folders tested: {self.summary['total_folders']}")
        print(f"   ✅ Successful: {self.summary['successful']} ({self.summary['successful']/max(1, self.summary['total_folders'])*100:.1f}%)")
        print(f"   ❌ Failed: {self.summary['failed']} ({self.summary['failed']/max(1, self.summary['total_folders'])*100:.1f}%)")
        print(f"   ⚠️  Warnings: {self.summary['warnings']} ({self.summary['warnings']/max(1, self.summary['total_folders'])*100:.1f}%)")
        print(f"   ⏱️  Total time: {self.summary['total_time']:.2f} seconds")
        print(f"   ⏱️  Average time per folder: {self.summary['total_time']/max(1, self.summary['total_folders']):.2f} seconds")
        
        # List failed folders
        if self.summary['failed'] > 0:
            print(f"\n❌ Failed Folders:")
            for result in self.results:
                if result['status'] == 'failed':
                    print(f"   - {result['folder_name']}: {result['error']}")
        
        # List warnings
        if self.summary['warnings'] > 0:
            print(f"\n⚠️  Folders with Warnings:")
            for result in self.results:
                if result['status'] == 'warning':
                    print(f"   - {result['folder_name']}: {', '.join(result['warnings'])}")
        
        print(f"\n📁 Results saved to: {self.output_dir}")
        print("="*80)


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integration test for workload parser on real data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all folders in data directory
  python test_data_integration.py
  
  # Test with DAQ configuration
  python test_data_integration.py -d config/daq_targets_default.json
  
  # Test only first 5 folders
  python test_data_integration.py --max-folders 5
  
  # Custom data location
  python test_data_integration.py --data-root "D:/my/data/folder"
        """
    )
    
    parser.add_argument(
        '--data-root',
        default=r'\\10.54.63.126\Pnpext\Siwoo\data',
        help='Root directory containing workload data subfolders (default: \\\\10.54.63.126\\Pnpext\\Siwoo\\data)'
    )
    
    parser.add_argument(
        '-d', '--daq-config',
        help='Path to DAQ targets configuration JSON file'
    )
    
    parser.add_argument(
        '--max-folders',
        type=int,
        help='Maximum number of folders to test (for quick testing)'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='./test_results',
        help='Directory for test results (default: ./test_results)'
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = DataIntegrationTester(
        data_root=args.data_root,
        output_dir=args.output_dir
    )
    
    # Run all tests
    tester.run_all_tests(
        daq_config_path=args.daq_config,
        max_folders=args.max_folders
    )


if __name__ == "__main__":
    main()
