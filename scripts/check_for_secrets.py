#!/usr/bin/env python
"""
Secret Detection Utility

This script scans the codebase for potential secrets and credentials.
"""

import re
import os
import argparse
from pathlib import Path

# Patterns that might indicate secrets
SECRET_PATTERNS = [
    r'(access_?token|api_?key|aws_?(access|secret)|secret|token).{0,3}[=:].{0,3}[\'"][A-Za-z0-9+/=]{8,}[\'"]',
    r'(client|app|consumer)_?(id|key|secret).{0,3}[=:].{0,3}[\'"][A-Za-z0-9+/=]{8,}[\'"]',
    r'(auth|oauth|refresh)_?token.{0,3}[=:].{0,3}[\'"][A-Za-z0-9+/=]{8,}[\'"]',
    r'GOOGLE_ADS_[A-Z_]+=.+',
    r'[0-9]{10,}[-]?[0-9]{1,}',  # Potential Google customer IDs
]

# Files and directories to ignore
IGNORE_PATHS = [
    '.git',
    '.venv',
    '__pycache__',
    'node_modules',
    '.env.example',
    'sensitive-doc-template.md',
    'templates',
]

def should_ignore(path):
    """Check if the path should be ignored."""
    for ignore in IGNORE_PATHS:
        if ignore in str(path):
            return True
    return False

def scan_file(file_path):
    """Scan a file for potential secrets."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        findings = []
        for pattern in SECRET_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 20)
                context_end = min(len(content), match.end() + 20)
                context = content[context_start:context_end].replace('\n', ' ')
                
                # Skip if it's clearly a placeholder
                if any(marker in match.group(0).lower() for marker in ['your_', 'example', 'placeholder', 'xxxxxxx']):
                    continue
                    
                findings.append({
                    'pattern': pattern,
                    'match': match.group(0),
                    'context': context,
                    'line_number': content[:match.start()].count('\n') + 1
                })
        
        return findings
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
        return []

def scan_directory(directory, extensions=None):
    """Recursively scan a directory for potential secrets."""
    directory_path = Path(directory)
    all_findings = {}
    
    for path in directory_path.glob('**/*'):
        if path.is_file() and not should_ignore(path):
            if extensions and path.suffix not in extensions:
                continue
                
            findings = scan_file(path)
            if findings:
                all_findings[str(path)] = findings
    
    return all_findings

def print_findings(findings):
    """Print findings in a readable format."""
    if not findings:
        print("No potential secrets found!")
        return
        
    print(f"Found potential secrets in {len(findings)} files:")
    
    for file_path, file_findings in findings.items():
        print(f"\n{file_path}:")
        for i, finding in enumerate(file_findings, 1):
            print(f"  {i}. Line {finding['line_number']}: {finding['match']}")
            print(f"     Context: ...{finding['context']}...")

def main():
    parser = argparse.ArgumentParser(description='Scan codebase for potential secrets')
    parser.add_argument('--dir', default='.', help='Directory to scan')
    parser.add_argument('--extensions', help='Comma-separated list of file extensions to scan')
    
    args = parser.parse_args()
    
    extensions = None
    if args.extensions:
        extensions = [f".{ext.strip()}" for ext in args.extensions.split(',')]
    
    findings = scan_directory(args.dir, extensions)
    print_findings(findings)

if __name__ == '__main__':
    main()
