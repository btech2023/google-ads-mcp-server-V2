#!/usr/bin/env python
"""
Google Ads API Usage Analysis Script

This script analyzes Google Ads API call logs and generates optimization reports
to help identify potential improvements in API usage patterns.
"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_tracker import APICallTracker

def generate_report(hours=24, format_type='markdown', db_path=None):
    """
    Generate an API usage report.
    
    Args:
        hours: Number of hours to analyze
        format_type: Output format ('markdown' or 'json')
        db_path: Path to the API call logs database
        
    Returns:
        The report as a string in the specified format
    """
    # Initialize the API call tracker
    api_tracker = APICallTracker(db_path=db_path)
    
    # Generate the report
    if format_type == 'markdown':
        return api_tracker.generate_optimization_report(hours=hours)
    else:  # json
        analysis = api_tracker.analyze_call_patterns(hours=hours)
        return json.dumps(analysis, indent=2)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze Google Ads API usage patterns.')
    
    parser.add_argument('--hours', type=int, default=24,
                        help='Number of hours to analyze (default: 24)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path for the report (default: stdout)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                        help='Output format (default: markdown)')
    parser.add_argument('--db-path', type=str, default=None,
                        help='Path to the API call logs database (default: use default path)')
    parser.add_argument('--clear-logs', action='store_true',
                        help='Clear logs after analysis')
    parser.add_argument('--clear-logs-older-than', type=int, default=None,
                        help='Clear logs older than specified hours')
    
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Generate the report
    report = generate_report(
        hours=args.hours,
        format_type=args.format,
        db_path=args.db_path
    )
    
    # Output the report
    if args.output:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        
        # Write the report to the file
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        # Print to stdout
        print(report)
    
    # Handle log clearing if requested
    if args.clear_logs:
        api_tracker = APICallTracker(db_path=args.db_path)
        api_tracker.clear_logs()
        print("All API call logs have been cleared.")
    elif args.clear_logs_older_than is not None:
        api_tracker = APICallTracker(db_path=args.db_path)
        api_tracker.clear_logs(hours=args.clear_logs_older_than)
        print(f"API call logs older than {args.clear_logs_older_than} hours have been cleared.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 