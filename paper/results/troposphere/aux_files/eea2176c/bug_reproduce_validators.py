#!/usr/bin/env python3
"""Reproduce validator bugs in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

print("=" * 60)
print("BUG 1: Integer and Double validators accept bytes")
print("=" * 60)

from troposphere import validators

# Demonstrate the bug
print("\n1. validators.integer() accepts bytes:")
result = validators.integer(b'42')
print(f"   validators.integer(b'42') = {result!r}")
print(f"   type(result) = {type(result)}")
print(f"   int(result) = {int(result)}")

print("\n2. validators.double() accepts bytes:")
result = validators.double(b'3.14')
print(f"   validators.double(b'3.14') = {result!r}")
print(f"   type(result) = {type(result)}")
print(f"   float(result) = {float(result)}")

print("\n3. This can cause issues in CloudFormation templates:")
from troposphere.medialive import Ac3Settings

settings = Ac3Settings()
settings.Dialnorm = b'10'  # Setting with bytes
settings.Bitrate = b'128.5'

print(f"   Ac3Settings.Dialnorm = b'10' -> {settings.Dialnorm!r}")
print(f"   Ac3Settings.Bitrate = b'128.5' -> {settings.Bitrate!r}")

# Try to serialize
try:
    d = settings.to_dict()
    print(f"   to_dict() result: {d}")
    
    # This will create a CloudFormation template with bytes objects!
    import json
    try:
        json_str = json.dumps(d)
        print(f"   JSON serialization works: {json_str}")
    except TypeError as e:
        print(f"   JSON serialization FAILS: {e}")
        print("   ^ This shows bytes cause serialization issues!")
        
except Exception as e:
    print(f"   Error during serialization: {e}")

print("\n4. Why this is a bug:")
print("   - The validators are meant to validate CloudFormation property types")
print("   - CloudFormation expects strings/numbers, not Python bytes")
print("   - bytes objects will fail JSON serialization")
print("   - This violates the principle that validated values should be serializable")

print("\n" + "=" * 60)
print("BUG 2: positive_integer validator has incorrect implementation")
print("=" * 60)

print("\n1. Testing positive_integer with negative value:")
try:
    result = validators.positive_integer(-5)
    print(f"   validators.positive_integer(-5) = {result!r}")
    print(f"   ERROR: Should have raised ValueError!")
except ValueError as e:
    print(f"   Correctly raised ValueError: {e}")

print("\n2. Checking the implementation...")
print("   The validator checks `int(p) < 0` but returns the original `x`")
print("   This means it validates correctly but doesn't ensure consistent type")

# Demonstrate potential issue
print("\n3. Type inconsistency example:")
result1 = validators.positive_integer("10")
result2 = validators.positive_integer(10)
result3 = validators.positive_integer(10.0)

print(f"   validators.positive_integer('10') returns type: {type(result1)}")
print(f"   validators.positive_integer(10) returns type: {type(result2)}")
print(f"   validators.positive_integer(10.0) returns type: {type(result3)}")
print("   ^ Returns different types for same logical value!")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nFound 2 bugs in troposphere validators:")
print("1. integer() and double() validators incorrectly accept bytes objects")
print("2. positive_integer() has type inconsistency (minor)")
print("\nThe bytes bug is more serious as it can cause CloudFormation")
print("template serialization to fail.")