import sys
from io import BytesIO

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.response import FileIter

print("Testing FileIter with block_size=0 - Detailed")
print("=" * 50)

# Test 1: Fresh BytesIO
print("\nTest 1: Fresh BytesIO with content")
content = b"Hello, World!"
file_obj = BytesIO(content)
print(f"File position before: {file_obj.tell()}")

file_iter = FileIter(file_obj, block_size=0)

# Manually call __next__
try:
    result = file_iter.__next__()
    print(f"First __next__() returned: {repr(result)} (length: {len(result)})")
    if result == b'':
        print("ERROR: Returned empty bytes without StopIteration!")
        # Try again
        result2 = file_iter.__next__()
        print(f"Second __next__() returned: {repr(result2)} (length: {len(result2)})")
except StopIteration:
    print("StopIteration raised on first call")

print(f"File position after: {file_obj.tell()}")

# Test 2: What does read(0) actually do?
print("\n" + "=" * 50)
print("Test 2: What does BytesIO.read(0) return?")
file_obj2 = BytesIO(b"Test content")
print(f"Position: {file_obj2.tell()}")
result = file_obj2.read(0)
print(f"read(0) returned: {repr(result)} (type: {type(result)})")
print(f"Position after read(0): {file_obj2.tell()}")

# Test with a real file
print("\n" + "=" * 50)
print("Test 3: With a real file")
import tempfile
import os

with tempfile.NamedTemporaryFile(delete=False) as f:
    f.write(b"File content here")
    temp_path = f.name

try:
    with open(temp_path, 'rb') as f:
        print(f"File position: {f.tell()}")
        result = f.read(0)
        print(f"file.read(0) returned: {repr(result)}")
        print(f"File position after: {f.tell()}")
        
        # Now test with FileIter
        f.seek(0)
        file_iter = FileIter(f, block_size=0)
        
        for i in range(5):
            try:
                chunk = next(file_iter)
                print(f"  Iteration {i}: {repr(chunk)}")
                if chunk == b'' and i < 4:
                    print("  WARNING: Infinite loop condition!")
            except StopIteration:
                print(f"  StopIteration at iteration {i}")
                break
finally:
    os.unlink(temp_path)