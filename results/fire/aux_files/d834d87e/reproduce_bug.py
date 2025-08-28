import os
from fire.testutils import ChangeDirectory

# Save original directory
original_dir = os.getcwd()
print(f"Original directory: {original_dir}")

# Try to change to a path with null character
path_with_null = "\x00"

try:
    with ChangeDirectory(path_with_null):
        print("Inside context (shouldn't get here)")
except ValueError as e:
    print(f"Caught ValueError: {e}")

# Check if we're back in the original directory
current_dir = os.getcwd()
print(f"Current directory after exception: {current_dir}")

if current_dir == original_dir:
    print("✓ Directory was restored correctly")
else:
    print(f"✗ BUG: Directory was NOT restored! Expected {original_dir}, got {current_dir}")