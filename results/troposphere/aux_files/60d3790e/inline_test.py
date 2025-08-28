#!/usr/bin/env python3
"""Direct inline testing of codeconnections"""

code = """
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Tags
from troposphere.codeconnections import Connection

# Test empty title
print("Testing empty title...")
try:
    conn = Connection("", ConnectionName="test")
    conn.validate_title()
    print("BUG FOUND: Empty title was accepted!")
except ValueError as e:
    if "not alphanumeric" in str(e):
        print("Correctly rejected empty title")
    else:
        print(f"Unexpected error: {e}")
except Exception as e:
    print(f"Unexpected error type: {e}")

# Test title with only spaces
print("\\nTesting space-only title...")
try:
    conn = Connection("   ", ConnectionName="test")
    result = conn.to_dict(validation=True)
    print(f"BUG FOUND: Space-only title was accepted and produced: {result}")
except ValueError as e:
    print(f"Correctly rejected: {e}")
except Exception as e:
    print(f"Error: {e}")

# Test from_dict with empty Properties
print("\\nTesting from_dict with minimal input...")
try:
    conn = Connection.from_dict("TestTitle", {})
    result = conn.to_dict()
    print(f"Created connection without required field, result: {result}")
except Exception as e:
    print(f"Error (expected): {e}")

# Test round-trip with special characters in values
print("\\nTesting round-trip with special characters...")
conn1 = Connection("Test1", ConnectionName="test/connection@123")
d1 = conn1.to_dict()
props1 = d1.get('Properties', {})
conn2 = Connection.from_dict("Test1", props1)
d2 = conn2.to_dict()
if d1 == d2:
    print("Round-trip with special chars: OK")
else:
    print(f"BUG: Round-trip failed! Original: {d1}, After: {d2}")

# Test Tags edge case
print("\\nTesting Tags with empty dict...")
t = Tags()
result = t.to_dict()
print(f"Empty Tags result: {result}")

# Test that validation actually runs
print("\\nTesting that validation runs in to_dict()...")
conn = Connection("Test")
try:
    # Don't set ConnectionName
    result = conn.to_dict(validation=True)
    print(f"BUG: Validation didn't catch missing required field! Result: {result}")
except ValueError as e:
    if "ConnectionName" in str(e) and "required" in str(e):
        print("Validation correctly caught missing required field")
    else:
        print(f"Wrong validation error: {e}")

# Test no validation mode
print("\\nTesting no validation mode...")
conn = Connection("Test")
try:
    result = conn.to_dict(validation=False)
    print(f"No validation mode allowed missing required field, result has keys: {result.keys()}")
except Exception as e:
    print(f"Unexpected error in no-validation mode: {e}")
"""

exec(code)