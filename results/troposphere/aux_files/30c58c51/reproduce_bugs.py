#!/usr/bin/env python3
"""Minimal reproductions of the discovered bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer
from troposphere import healthlake

print("=" * 60)
print("Bug 1: Boolean validator accepts float 0.0")
print("=" * 60)
try:
    result = boolean(0.0)
    print(f"boolean(0.0) = {result} (type: {type(result)})")
    print("Expected: ValueError, Got: False")
    print("BUG: boolean validator should only accept bool/int/str, not float")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n" + "=" * 60)
print("Bug 2: Title validation is inconsistent with character categories")
print("=" * 60)
try:
    # ª is Unicode character U+00AA (FEMININE ORDINAL INDICATOR)
    # It's in Unicode category 'Lo' (Letter, other)
    datastore = healthlake.FHIRDatastore("ª", DatastoreTypeVersion="R4")
    print("Created datastore with title 'ª'")
    print("BUG: Title validation should either accept all letters or document limitation")
except ValueError as e:
    print(f"Raised ValueError: {e}")
    
print("\n" + "=" * 60)
print("Bug 3: Integer validator crashes with infinity")
print("=" * 60)
try:
    result = integer(float('inf'))
    print(f"integer(float('inf')) = {result}")
    print("BUG: Should raise ValueError, not OverflowError")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")
except OverflowError as e:
    print(f"Raised OverflowError: {e}")
    print("BUG: Should raise ValueError for invalid input, not OverflowError")

print("\n" + "=" * 60)
print("Bug 3b: Integer validator also crashes with negative infinity")
print("=" * 60)
try:
    result = integer(float('-inf'))
    print(f"integer(float('-inf')) = {result}")
    print("BUG: Should raise ValueError, not OverflowError")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")
except OverflowError as e:
    print(f"Raised OverflowError: {e}")
    print("BUG: Should raise ValueError for invalid input, not OverflowError")

print("\n" + "=" * 60)
print("Bug 3c: Integer validator also crashes with NaN")
print("=" * 60)
try:
    result = integer(float('nan'))
    print(f"integer(float('nan')) = {result}")
    print("BUG: Should raise ValueError, not pass through NaN")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")