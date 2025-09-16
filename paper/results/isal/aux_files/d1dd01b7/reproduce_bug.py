"""Minimal reproduction of the bug in isal.igzip.compress"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip as igzip

# Bug 1: OverflowError with large compression level
print("Testing large compression level...")
try:
    data = b''
    level = 2147483648  # 2^31
    compressed = igzip.compress(data, compresslevel=level)
    print(f"  Unexpectedly succeeded with level={level}")
except OverflowError as e:
    print(f"  OverflowError with level=2147483648: {e}")
except ValueError as e:
    print(f"  ValueError (expected): {e}")

# Bug 2: IsalError with negative compression level  
print("\nTesting negative compression level...")
try:
    data = b''
    level = -1
    compressed = igzip.compress(data, compresslevel=level)
    print(f"  Unexpectedly succeeded with level={level}")
except Exception as e:
    print(f"  {type(e).__name__} with level=-1: {e}")

# Expected behavior: should raise ValueError for invalid levels
print("\nExpected behavior would be:")
print("  ValueError: Compression level should be between 0 and 3, got <level>")