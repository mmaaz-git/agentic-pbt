#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
import srsly

# Bug 1: is_json_serializable crashes with certain byte strings
print("Testing is_json_serializable with various byte strings:")

test_bytes = [
    b'\x00',      # Hypothesis found this returns True incorrectly
    b'\x80',      # Hypothesis found this crashes  
    b'hello',     # Regular ASCII bytes
    b'\xff\xfe',  # Non-UTF8 bytes
]

for test_byte in test_bytes:
    try:
        result = srsly.is_json_serializable(test_byte)
        print(f"{repr(test_byte):20} -> {result}")
        
        # If it says it's serializable, verify that
        if result:
            try:
                json_str = srsly.json_dumps(test_byte)
                print(f"  Successfully serialized to: {repr(json_str)}")
            except Exception as e:
                print(f"  ERROR: is_json_serializable returned True but json_dumps failed: {e}")
    except Exception as e:
        print(f"{repr(test_byte):20} -> CRASHED: {e}")

print("\n" + "="*60)
print("Checking if bytes are actually JSON serializable...")

# Let's see what happens when we try to actually serialize bytes
for test_byte in test_bytes:
    try:
        json_str = srsly.json_dumps(test_byte)
        print(f"{repr(test_byte):20} -> SUCCESS: {repr(json_str)}")
    except Exception as e:
        print(f"{repr(test_byte):20} -> FAILED: {e}")