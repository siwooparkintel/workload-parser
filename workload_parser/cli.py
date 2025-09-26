"""
Command-line interface for the Workload Parser.
"""

import sys
import json
from pathlib import Path
from typing import Optional

try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    click = None

from .core.parser import WorkloadParser
from .core.exceptions import ParsingError, ConfigurationError


def simple_cli():
    """Simple CLI without click dependency."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workload Parser - Parse and analyze workload data")
    parser.add_argument("input_path", help="Path to file or directory to parse")
    parser.add_argument("-c", "--config", help="Path to configuration file")
    parser.add_argument("-o", "--output", help="Output file path (JSON format)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                       help="Parse directory recursively")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Initialize parser
        workload_parser = WorkloadParser(args.config)
        
        # Determine if input is file or directory
        input_path = Path(args.input_path)
        
        if input_path.is_file():
            results = [workload_parser.parse_file(str(input_path))]
        elif input_path.is_dir():
            results = workload_parser.parse_directory(str(input_path), args.recursive)
        else:
            print(f"Error: Input path does not exist: {args.input_path}")
            return 1
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to: {args.output}")
        else:
            # Print summary to console
            print(f"Parsed {len(results)} files:")
            for result in results:
                metadata = result.get('_metadata', {})
                print(f"  - {metadata.get('file_path', 'Unknown')}: "
                      f"{result.get('data_type', 'unknown')} data, "
                      f"{result.get('row_count', 0)} rows")
        
        return 0
        
    except (ParsingError, ConfigurationError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if CLICK_AVAILABLE:
    @click.command()
    @click.argument('input_path', type=click.Path(exists=True))
    @click.option('-c', '--config', type=click.Path(), 
                  help='Path to configuration file')
    @click.option('-o', '--output', type=click.Path(), 
                  help='Output file path (JSON format)')
    @click.option('-r', '--recursive', is_flag=True, 
                  help='Parse directory recursively')
    @click.option('-v', '--verbose', is_flag=True, 
                  help='Verbose output')
    def cli_main(input_path: str, config: Optional[str], output: Optional[str], 
                 recursive: bool, verbose: bool):
        """Workload Parser - Parse and analyze workload data."""
        try:
            # Initialize parser
            workload_parser = WorkloadParser(config)
            
            # Determine if input is file or directory
            input_path_obj = Path(input_path)
            
            if input_path_obj.is_file():
                results = [workload_parser.parse_file(input_path)]
            else:
                results = workload_parser.parse_directory(input_path, recursive)
            
            # Output results
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, default=str)
                click.echo(f"Results saved to: {output}")
            else:
                # Print summary to console
                click.echo(f"Parsed {len(results)} files:")
                for result in results:
                    metadata = result.get('_metadata', {})
                    click.echo(f"  - {metadata.get('file_path', 'Unknown')}: "
                              f"{result.get('data_type', 'unknown')} data, "
                              f"{result.get('row_count', 0)} rows")
            
        except (ParsingError, ConfigurationError) as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Main CLI entry point."""
    if CLICK_AVAILABLE:
        cli_main()
    else:
        return simple_cli()


if __name__ == "__main__":
    main()