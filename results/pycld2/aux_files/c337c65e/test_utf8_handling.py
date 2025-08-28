#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2

print("Testing UTF-8 handling in pycld2:")
print("="*60)

# Test various string inputs that might cause issues
test_cases = [
    # Valid UTF-8 strings
    ("Hello", "Normal ASCII"),
    ("café", "Latin with accent"),
    ("你好", "Chinese"),
    ("🎉", "Emoji"),
    
    # Edge case characters
    ("\x00", "Null byte"),
    ("\x01", "Control char 0x01"),
    ("\x08", "Control char 0x08 (backspace)"),
    ("\x1f", "Control char 0x1f"),
    ("\x7f", "DEL character"),
    
    # Unicode edge cases
    ("\u0000", "Unicode null"),
    ("\u0001", "Unicode SOH"),
    ("\u001f", "Unicode US"),
    ("\uffff", "Unicode max BMP"),
    ("\U0001f600", "Emoji (grinning face)"),
]

for text, description in test_cases:
    print(f"\nTest: {description}")
    print(f"  Text repr: {repr(text)}")
    print(f"  Text bytes: {text.encode('utf-8')}")
    
    try:
        result = pycld2.detect(text)
        print(f"  ✓ Success: {result}")
    except pycld2.error as e:
        print(f"  ✗ pycld2.error: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")

print("\n" + "="*60)
print("Testing bytes input:")

# Test direct bytes input
byte_cases = [
    (b"Hello", "Valid UTF-8 bytes"),
    (b"\xff\xfe", "Invalid UTF-8 (BOM-like)"),
    (b"\x80", "Invalid UTF-8 (continuation byte alone)"),
    (b"\xc0\x80", "Invalid UTF-8 (overlong encoding)"),
    (b"\xed\xa0\x80", "Invalid UTF-8 (surrogate)"),
]

for data, description in byte_cases:
    print(f"\nTest: {description}")
    print(f"  Bytes: {data}")
    
    try:
        result = pycld2.detect(data)
        print(f"  ✓ Success: {result}")
    except pycld2.error as e:
        print(f"  ✓ Expected pycld2.error: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")

print("\n" + "="*60)
print("Key finding about strings vs bytes:")

# The issue seems to be that Python strings with certain control characters
# get rejected even though they're valid Unicode strings
problematic_chars = [chr(i) for i in range(32) if chr(i) not in ['\t', '\n', '\r']]

print(f"\nControl characters that cause pycld2.error:")
for char in problematic_chars:
    try:
        pycld2.detect(char)
    except pycld2.error:
        print(f"  chr({ord(char):3d}) = {repr(char)}")

print("\nConclusion: pycld2 rejects many control characters even in valid Python strings")