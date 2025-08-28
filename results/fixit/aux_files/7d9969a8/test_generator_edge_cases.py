#!/usr/bin/env python3
"""Test edge cases in fixit_bytes generator."""

import sys
from pathlib import Path

sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.api import fixit_bytes
from fixit.ftypes import Config, FileContent

print("Testing fixit_bytes edge cases...")
print("=" * 60)

# Test 1: Empty content with empty config (no rules)
print("\nTest 1: Empty content, no rules enabled")
config = Config(path=Path("test.py"), enable=[], disable=[])
content = b""

generator = fixit_bytes(Path("test.py"), content, config=config, autofix=False)

results = []
try:
    while True:
        result = generator.send(None)
        results.append(result)
        print(f"  Yielded: {result}")
except StopIteration as e:
    return_value = e.value
    print(f"  Return value: {return_value}")

print(f"  Total results yielded: {len(results)}")
assert len(results) >= 1, "Should yield at least one result"

# Test 2: Non-Python content  
print("\nTest 2: Binary/non-Python content")
binary_content = b"\x00\x01\x02\x03\xff\xfe\xfd"
generator2 = fixit_bytes(Path("binary.dat"), binary_content, config=config, autofix=False)

results2 = []
try:
    while True:
        result = generator2.send(None)
        results2.append(result)
        print(f"  Yielded: {result}")
except StopIteration as e:
    return_value2 = e.value
    print(f"  Return value: {return_value2}")

print(f"  Total results yielded: {len(results2)}")

# Test 3: Very large path names
print("\nTest 3: Extremely long path name")
long_path = Path("a" * 1000 + "/" + "b" * 1000 + ".py")
generator3 = fixit_bytes(long_path, b"print('hello')", config=config, autofix=False)

results3 = []
try:
    while True:
        result = generator3.send(None)
        results3.append(result)
        if len(str(result)) > 100:
            print(f"  Yielded result with long path (truncated): {str(result)[:100]}...")
        else:
            print(f"  Yielded: {result}")
except StopIteration as e:
    return_value3 = e.value

print(f"  Total results yielded: {len(results3)}")

print("\n" + "=" * 60)
print("All edge case tests completed.")