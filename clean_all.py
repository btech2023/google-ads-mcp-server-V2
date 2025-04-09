#!/usr/bin/env python3
"""
Script to fix encoding/byte issues across all Python files and remove cache files.
"""

import os
import glob
import sys
import shutil

def clean_pycache():
    """Remove all __pycache__ directories and .pyc files."""
    # Find and remove __pycache__ directories
    pycache_dirs = glob.glob("**/__pycache__", recursive=True)
    for pycache_dir in pycache_dirs:
        print(f"Removing {pycache_dir}")
        try:
            shutil.rmtree(pycache_dir)
        except Exception as e:
            print(f"  Error removing {pycache_dir}: {e}")
    
    # Find and remove .pyc files
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    for pyc_file in pyc_files:
        print(f"Removing {pyc_file}")
        try:
            os.remove(pyc_file)
        except Exception as e:
            print(f"  Error removing {pyc_file}: {e}")

def fix_null_byte_files():
    """Find and fix null bytes in all Python files."""
    # Find all Python files
    py_files = glob.glob("**/*.py", recursive=True)
    print(f"Found {len(py_files)} Python files to check")
    
    fixed_files = []
    
    for file_path in py_files:
        if "__pycache__" in file_path:
            continue  # Skip cache files
            
        try:
            # Read file in binary mode
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for null bytes
            if b'\x00' in content:
                print(f"Found null bytes in {file_path}")
                cleaned_content = content.replace(b'\x00', b'')
                
                # Write cleaned content back
                with open(file_path, 'wb') as f:
                    f.write(cleaned_content)
                
                fixed_files.append(file_path)
                print(f"Fixed null bytes in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return fixed_files

def fix_encoding_issues():
    """Fix encoding issues in Python files."""
    # Find all Python files
    py_files = glob.glob("**/*.py", recursive=True)
    print(f"Found {len(py_files)} Python files to check for encoding issues")
    
    fixed_files = []
    
    for file_path in py_files:
        if "__pycache__" in file_path:
            continue  # Skip cache files
            
        try:
            # Try to open and read file with UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # File is already valid UTF-8, no need to fix
            except UnicodeDecodeError:
                print(f"Found encoding issue in {file_path}")
                
                # Read in binary and convert to UTF-8
                with open(file_path, 'rb') as f:
                    binary_content = f.read()
                
                # Try to decode with various encodings
                for encoding in ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        content = binary_content.decode(encoding, errors='replace')
                        break
                    except:
                        continue
                
                # Write back as UTF-8
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                fixed_files.append(file_path)
                print(f"Fixed encoding in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return fixed_files

if __name__ == "__main__":
    print("Step 1: Removing Python cache files...")
    clean_pycache()
    
    print("\nStep 2: Fixing null bytes in Python files...")
    fixed_null_files = fix_null_byte_files()
    
    print("\nStep 3: Fixing encoding issues in Python files...")
    fixed_encoding_files = fix_encoding_issues()
    
    print("\nSummary:")
    if fixed_null_files:
        print(f"Fixed null bytes in {len(fixed_null_files)} files")
    else:
        print("No files with null bytes found")
        
    if fixed_encoding_files:
        print(f"Fixed encoding issues in {len(fixed_encoding_files)} files")
    else:
        print("No files with encoding issues found")
        
    print("\nDone!") 