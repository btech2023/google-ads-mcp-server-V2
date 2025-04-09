import sys
import os

def clean_file_null_bytes(file_path):
    """Reads a file, removes null bytes, and writes it back."""
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()

        original_length = len(content_bytes)
        null_count = content_bytes.count(b'\x00')

        if null_count == 0:
            print(f"No null bytes found in {file_path}. File not modified.")
            return

        print(f"Found {null_count} null bytes in {file_path} (Original size: {original_length} bytes).")
        cleaned_bytes = content_bytes.replace(b'\x00', b'')
        cleaned_length = len(cleaned_bytes)
        print(f"Cleaning file. New size: {cleaned_length} bytes.")

        with open(file_path, 'wb') as f:
            f.write(cleaned_bytes)

        print(f"Successfully cleaned and wrote back {file_path}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clean_nulls.py <file_path>")
        sys.exit(1)

    target_file = sys.argv[1]
    clean_file_null_bytes(target_file) 