"""Check how IGzipFile handles invalid compression levels"""

import sys
import io
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip as igzip
import isal.isal_zlib as isal_zlib

print(f"Valid compression level range: {isal_zlib.ISAL_BEST_SPEED} to {isal_zlib.ISAL_BEST_COMPRESSION}")

# Test IGzipFile with invalid compression levels
print("\nTesting IGzipFile with negative compression level...")
try:
    buffer = io.BytesIO()
    f = igzip.IGzipFile(mode='wb', fileobj=buffer, compresslevel=-1)
    print("  Unexpectedly succeeded")
except ValueError as e:
    print(f"  ValueError (good!): {e}")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

print("\nTesting IGzipFile with large compression level...")
try:
    buffer = io.BytesIO()
    f = igzip.IGzipFile(mode='wb', fileobj=buffer, compresslevel=2147483648)
    print("  Unexpectedly succeeded")
except (ValueError, OverflowError) as e:
    print(f"  {type(e).__name__} (good!): {e}")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")

print("\nTesting IGzipFile with level 4...")
try:
    buffer = io.BytesIO()
    f = igzip.IGzipFile(mode='wb', fileobj=buffer, compresslevel=4)
    print("  Unexpectedly succeeded")
except ValueError as e:
    print(f"  ValueError (good!): {e}")
except Exception as e:
    print(f"  {type(e).__name__}: {e}")