#!/usr/bin/env python3
"""
Script to clean null bytes from Python files in the utils directory.
"""

import os
import glob

def clean_utils_files():
    # Focus specifically on utils module
    utils_files = glob.glob("google_ads_mcp_server/utils/**/*.py", recursive=True)
    
    print(f"Found {len(utils_files)} files in utils directory")
    
    for file_path in utils_files:
        print(f"Processing {file_path}...")
        
        try:
            # Read original content
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Create backup
            backup_path = file_path + '.bak'
            with open(backup_path, 'wb') as f:
                f.write(content)
                
            print(f"  Created backup at {backup_path}")
            
            # Check for and remove null bytes
            if b'\x00' in content:
                print(f"  Found null bytes in {file_path}")
                cleaned = content.replace(b'\x00', b'')
                
                # Write clean content
                with open(file_path, 'wb') as f:
                    f.write(cleaned)
                print(f"  Cleaned null bytes from {file_path}")
            else:
                print(f"  No null bytes found in {file_path}")
                
            # Verify content can be properly decoded as UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    _ = f.read()
                print(f"  File verified as valid UTF-8")
            except UnicodeDecodeError:
                print(f"  ⚠️ WARNING: File has UTF-8 decoding issues, trying to fix...")
                try:
                    # Read with error replacement
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Try to decode with errors='replace'
                    text = content.decode('utf-8', errors='replace')
                    
                    # Write back as clean UTF-8
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    print(f"  ✅ Fixed encoding issues in {file_path}")
                except Exception as e:
                    print(f"  ❌ Failed to fix encoding: {e}")
        
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    print("\nDone processing utils files!")

if __name__ == "__main__":
    clean_utils_files() 