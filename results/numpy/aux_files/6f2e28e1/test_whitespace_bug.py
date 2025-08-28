"""Minimal test demonstrating whitespace field name bug in numpy.rec"""

import numpy as np
import numpy.rec as rec

# Demonstrate the bug
print("Bug demonstration: whitespace-only field names get stripped")
print("="*60)

# Test 1: format_parser strips whitespace names
formats = ['i4', 'f8']
names = [' ', '\t']  # Whitespace-only names

parser = rec.format_parser(formats, names=names, titles=None)
print(f"Input names: {names!r}")
print(f"Parser output: {parser._names!r}")
print(f"Expected: [' ', '\\t'] or at least unique names")
print(f"Actual: Both become empty string: {parser._names}")
print()

# Test 2: This causes field access problems
print("Problem: Cannot access fields by original name")
print("-"*40)
arr1 = np.array([1, 2, 3])
arr2 = np.array([4.0, 5.0, 6.0])

rec_arr = rec.fromarrays([arr1, arr2], names=[' ', 'y'])
print(f"Created recarray with names: [' ', 'y']")

# Try to access the field with space name
try:
    value = rec_arr[' ']
    print(f"Accessing rec_arr[' ']: SUCCESS - {value}")
except Exception as e:
    print(f"Accessing rec_arr[' ']: FAILED - {e}")

# The field can only be accessed by empty string
try:
    value = rec_arr['']
    print(f"Accessing rec_arr['']: SUCCESS - {value}")
except Exception as e:
    print(f"Accessing rec_arr['']: FAILED - {e}")

print()
print("This violates the API contract:")
print("- User provides ' ' as field name")
print("- Cannot access field using ' '")
print("- Must use '' instead (implementation detail leaked)")