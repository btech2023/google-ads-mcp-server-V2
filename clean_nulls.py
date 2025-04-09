import os
import sys
import chardet
import glob

def clean_all_python_files():
    """Find and clean all .py files in the current directory and subdirectories."""
    # Find all Python files
    all_py_files = glob.glob("**/*.py", recursive=True)
    print(f"Found {len(all_py_files)} Python files")
    
    # Process each file
    fixed_files = []
    for filepath in all_py_files:
        # Skip if it's a directory somehow
        if os.path.isdir(filepath):
            continue
            
        try:
            # Read file in binary mode
            with open(filepath, 'rb') as f:
                content = f.read()
                
            # Check for null bytes
            if b'\x00' in content:
                print(f"Found null bytes in {filepath}")
                
                # Remove null bytes
                cleaned = content.replace(b'\x00', b'')
                
                # Write cleaned content back
                with open(filepath, 'wb') as f:
                    f.write(cleaned)
                    
                fixed_files.append(filepath)
                print(f"Cleaned null bytes from {filepath}")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    if fixed_files:
        print(f"\nCleaned {len(fixed_files)} files:")
        for file in fixed_files:
            print(f" - {file}")
    else:
        print("No files needed cleaning.")

if __name__ == "__main__":
    print("Scanning and cleaning all Python files for null bytes...")
    clean_all_python_files()
    print("Done.") 