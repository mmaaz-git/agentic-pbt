#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import awkward.prettyprint as pp
import numpy as np

print("=== Investigating Formatter precision bug ===\n")

# Test default formatter behavior
formatter_default = pp.Formatter()
formatter_prec1 = pp.Formatter(precision=1)
formatter_prec3 = pp.Formatter(precision=3)
formatter_prec5 = pp.Formatter(precision=5)

test_values = [
    0.1 + 0.2,  # Should be 0.3 but is 0.30000000000000004
    1/3,        # Should respect precision
    np.float64(1/3),
    np.float32(1/3),
    float(1/3),
    1.23456789,
    0.000123456789,
    123456.789,
]

print("Testing float formatting with different precisions:\n")
for value in test_values:
    print(f"Value: {value} (type: {type(value).__name__})")
    print(f"  Default (prec=3): {formatter_prec3(value)}")
    print(f"  Precision=1:      {formatter_prec1(value)}")
    print(f"  Precision=5:      {formatter_prec5(value)}")
    # Also test the internal format methods directly
    print(f"  _format_real:     {formatter_prec3._format_real(value)}")
    print()

# Test what types actually go through the formatter
print("\n=== Testing which types use float formatting ===\n")

int_val = 123
float_val = 123.456
np_float32_val = np.float32(123.456)
np_float64_val = np.float64(123.456)
np_int32_val = np.int32(123)

for val in [int_val, float_val, np_float32_val, np_float64_val, np_int32_val]:
    print(f"{val} (type: {type(val).__name__})")
    result = formatter_prec3(val)
    print(f"  Result: {result}")
    print()

# Let's trace through the actual formatter logic
print("\n=== Tracing formatter implementation ===\n")

class DebugFormatter(pp.Formatter):
    def __call__(self, obj):
        print(f"  Formatting {obj} of type {type(obj).__name__}")
        result = super().__call__(obj)
        print(f"  -> Result: {result}")
        return result
    
    def _find_formatter_impl(self, cls):
        print(f"  Finding formatter for {cls.__name__}")
        impl = super()._find_formatter_impl(cls)
        print(f"  -> Using: {impl.__name__ if hasattr(impl, '__name__') else impl}")
        return impl

debug_formatter = DebugFormatter(precision=2)

test_objs = [
    123,
    123.456,
    np.float32(123.456),
    np.float64(123.456),
    np.int32(123),
    1/3,
]

for obj in test_objs:
    print(f"Processing: {obj}")
    result = debug_formatter(obj)
    print()

# Now let's check if this is the issue - Python's float type not being recognized
print("\n=== Type hierarchy check ===\n")
print(f"float is subclass of np.float64: {issubclass(float, np.float64)}")
print(f"float is subclass of np.float32: {issubclass(float, np.float32)}")
print(f"np.float64 is subclass of float: {issubclass(np.float64, float)}")
print(f"np.float32 is subclass of float: {issubclass(np.float32, float)}")