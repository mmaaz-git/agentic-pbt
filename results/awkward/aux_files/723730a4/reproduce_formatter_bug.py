#!/usr/bin/env python3
"""
Minimal reproduction of the Formatter precision bug in awkward.prettyprint
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward.prettyprint as pp
import numpy as np

# Create formatter with precision=2
formatter = pp.Formatter(precision=2)

# Test value
value = 1/3  # 0.3333...

# Format as Python float and NumPy float64
python_float = value
numpy_float = np.float64(value)

print("Formatter precision bug demonstration:")
print(f"Value: {value}")
print(f"Configured precision: 2")
print()
print(f"Python float type: {type(python_float)}")
print(f"Formatted output: '{formatter(python_float)}'")
print(f"Expected output:  '0.33'")
print()
print(f"NumPy float64 type: {type(numpy_float)}")  
print(f"Formatted output: '{formatter(numpy_float)}'")
print(f"Expected output:  '0.33'")
print()
print("BUG: Python's built-in float type ignores the precision parameter!")