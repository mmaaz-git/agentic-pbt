import sys
import os
import tempfile

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.response import FileResponse

# Test 1: Null byte in middle of path
print("Test 1: Null byte in middle of filename")
try:
    fake_path = "/tmp/test\x00file.txt"
    response = FileResponse(fake_path)
    print("  SUCCESS: FileResponse created (unexpected!)")
except (ValueError, OSError, FileNotFoundError) as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 2: Null byte at start
print("\nTest 2: Null byte at start of filename")
try:
    fake_path = "/tmp/\x00test.txt"
    response = FileResponse(fake_path)
    print("  SUCCESS: FileResponse created (unexpected!)")
except (ValueError, OSError, FileNotFoundError) as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 3: Just null byte
print("\nTest 3: Just null byte as filename")
try:
    fake_path = "/tmp/\x00"
    response = FileResponse(fake_path)
    print("  SUCCESS: FileResponse created (unexpected!)")
except (ValueError, OSError, FileNotFoundError) as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 4: What about _guess_type with null bytes?
print("\nTest 4: _guess_type with null byte")
from pyramid.response import _guess_type
try:
    content_type, encoding = _guess_type("/tmp/test\x00.txt")
    print(f"  SUCCESS: Got {content_type}, {encoding}")
except (ValueError, OSError) as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 5: Create a file with special name and test
print("\nTest 5: Valid file path after null byte is stripped")
# What if path looks like: "/tmp/valid_file.txt\x00ignored"
with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
    f.write(b"test content")
    valid_path = f.name

try:
    # Add null byte and text after the valid path
    malicious_path = valid_path + "\x00/etc/passwd"
    print(f"  Testing path: {repr(malicious_path)}")
    response = FileResponse(malicious_path)
    print(f"  SUCCESS: FileResponse created for path: {repr(malicious_path)}")
    print(f"  Content length: {response.content_length}")
except (ValueError, OSError, FileNotFoundError) as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
finally:
    os.unlink(valid_path)