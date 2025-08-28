#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import inspect
import srsly.ujson as ujson

print("=== ujson Module Exploration ===")
print(f"Module file: {ujson.__file__}")
print()

print("=== Available functions in ujson ===")
members = inspect.getmembers(ujson, inspect.isfunction)
for name, func in members:
    if not name.startswith('_'):
        print(f"\n{name}:")
        try:
            sig = inspect.signature(func)
            print(f"  Signature: {name}{sig}")
        except:
            print(f"  Signature: Could not retrieve")
        if func.__doc__:
            print(f"  Docstring: {func.__doc__[:200]}")

print("\n=== Testing Basic Round-trip Property ===")
import json

test_values = [
    None,
    True,
    False,
    0,
    1,
    -1,
    3.14,
    "",
    "hello",
    [],
    [1, 2, 3],
    {},
    {"key": "value"},
    {"nested": {"deep": "value"}},
]

for val in test_values:
    try:
        encoded = ujson.dumps(val)
        decoded = ujson.loads(encoded)
        print(f"✓ {repr(val)}: encode/decode round-trip successful")
        
        # Compare with standard json
        std_encoded = json.dumps(val)
        std_decoded = json.loads(std_encoded)
        ujson_from_std = ujson.loads(std_encoded)
        std_from_ujson = json.loads(encoded)
        
        if decoded != std_decoded:
            print(f"  ⚠ Different from json module: ujson={decoded}, json={std_decoded}")
        if ujson_from_std != val:
            print(f"  ⚠ ujson can't decode json output correctly")
        if std_from_ujson != val:
            print(f"  ⚠ json can't decode ujson output correctly")
            
    except Exception as e:
        print(f"✗ {repr(val)}: {e}")

print("\n=== Testing Unicode Handling ===")
unicode_tests = [
    "🦄",  # Emoji 
    "αβγ",  # Greek
    "中文",  # Chinese
    "مرحبا",  # Arabic
    "\u0000",  # Null character
    "a\nb",  # Newline
    "a\tb",  # Tab
    'a"b',  # Quote
    "a'b",  # Single quote
    "a\\b",  # Backslash
]

for s in unicode_tests:
    try:
        encoded = ujson.dumps(s)
        decoded = ujson.loads(encoded)
        if decoded == s:
            print(f"✓ {repr(s)}: round-trip successful")
        else:
            print(f"✗ {repr(s)}: round-trip failed - got {repr(decoded)}")
    except Exception as e:
        print(f"✗ {repr(s)}: {e}")