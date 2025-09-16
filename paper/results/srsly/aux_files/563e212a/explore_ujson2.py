#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.ujson as ujson
import inspect

print("=== Available attributes in ujson ===")
for name in dir(ujson):
    if not name.startswith('_'):
        obj = getattr(ujson, name)
        print(f"{name}: {type(obj)}")

print("\n=== Checking encode/decode/dumps/loads ===")
# These are the functions we saw in __init__.py
funcs = ['decode', 'encode', 'dump', 'dumps', 'load', 'loads']
for fname in funcs:
    if hasattr(ujson, fname):
        func = getattr(ujson, fname)
        print(f"\n{fname}:")
        # These are C extension functions, so we can't get signature easily
        if hasattr(func, '__doc__') and func.__doc__:
            print(f"  Docstring: {func.__doc__}")

print("\n=== Testing for potential properties ===")

# Test 1: Round-trip property
print("\n1. Testing encode/decode round-trip with complex data:")
complex_data = {
    "int": 42,
    "float": 3.14159,
    "string": "Hello, 世界! 🌍",
    "list": [1, 2, [3, 4]],
    "dict": {"nested": {"deep": True}},
    "null": None,
    "bool_true": True,
    "bool_false": False,
}

encoded = ujson.dumps(complex_data)
decoded = ujson.loads(encoded)
print(f"  Original == Decoded: {complex_data == decoded}")

# Test 2: Compatibility with standard json
import json
print("\n2. Testing compatibility with standard json module:")
json_encoded = json.dumps(complex_data)
ujson_decoded_from_json = ujson.loads(json_encoded)
print(f"  ujson can decode json output: {complex_data == ujson_decoded_from_json}")

ujson_encoded = ujson.dumps(complex_data) 
json_decoded_from_ujson = json.loads(ujson_encoded)
print(f"  json can decode ujson output: {complex_data == json_decoded_from_ujson}")

# Test 3: Testing edge cases
print("\n3. Testing edge cases:")
edge_cases = [
    ("Empty string", ""),
    ("Single space", " "),
    ("Escaped characters", "\\n\\t\\r"),
    ("Unicode emoji", "🦄🌈✨"),
    ("Large integer", 2**63 - 1),
    ("Small integer", -(2**63)),
    ("Float with many decimals", 3.141592653589793),
    ("Scientific notation", 1.23e-10),
    ("Empty list", []),
    ("Empty dict", {}),
    ("Nested empty structures", {"a": [], "b": {}, "c": [{}]}),
]

for name, value in edge_cases:
    try:
        encoded = ujson.dumps(value)
        decoded = ujson.loads(encoded)
        if value == decoded:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}: {value} != {decoded}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# Test 4: Check for any special behaviors
print("\n4. Testing special behaviors:")

# Dictionary with unicode keys
unicode_dict = {"🦄": "unicorn", "中文": "Chinese"}
try:
    encoded = ujson.dumps(unicode_dict)
    decoded = ujson.loads(encoded)
    print(f"  Unicode keys: {unicode_dict == decoded}")
except Exception as e:
    print(f"  Unicode keys failed: {e}")

# Mixed type lists
mixed_list = [1, "two", 3.0, None, True, {"five": 5}]
try:
    encoded = ujson.dumps(mixed_list)
    decoded = ujson.loads(encoded)
    print(f"  Mixed type list: {mixed_list == decoded}")
except Exception as e:
    print(f"  Mixed type list failed: {e}")