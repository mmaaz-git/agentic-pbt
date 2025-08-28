"""Reproduce the integer overflow bug in ArrayBuilder"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

print("Testing integer limits in ArrayBuilder...")
print(f"Max int64: {2**63 - 1}")
print(f"Problematic value: {2**63}")

builder = ak.ArrayBuilder()

# Test max int64 (should work)
try:
    max_int64 = 2**63 - 1
    builder.integer(max_int64)
    print(f"✓ Successfully added max int64: {max_int64}")
except Exception as e:
    print(f"✗ Failed to add max int64: {e}")

# Test max int64 + 1 (should fail or handle gracefully)
try:
    overflow_value = 2**63
    builder.integer(overflow_value)
    print(f"✓ Successfully added overflow value: {overflow_value}")
    result = builder.snapshot().to_list()
    print(f"  Result: {result}")
    if result[-1] != overflow_value:
        print(f"  WARNING: Value was changed from {overflow_value} to {result[-1]}")
except TypeError as e:
    print(f"✗ TypeError when adding {overflow_value}: {e}")
    print("  BUG: ArrayBuilder.integer() cannot handle Python integers >= 2^63")
except Exception as e:
    print(f"✗ Other error when adding {overflow_value}: {e}")

# Test with Python's arbitrary precision integers
print("\nTesting larger values...")
test_values = [
    2**63,      # Just over int64 max
    2**64,      # uint64 max + 1  
    2**100,     # Very large
    -2**63 - 1, # Just under int64 min
]

for value in test_values:
    try:
        test_builder = ak.ArrayBuilder()
        test_builder.integer(value)
        result = test_builder.snapshot().to_list()[0]
        if result == value:
            print(f"✓ {value}: preserved correctly")
        else:
            print(f"✗ {value}: changed to {result}")
    except TypeError as e:
        print(f"✗ {value}: TypeError - cannot handle this value")
    except Exception as e:
        print(f"✗ {value}: {type(e).__name__}: {e}")

print("\nComparison with append method:")
# Test if append() handles large integers differently
builder2 = ak.ArrayBuilder()
try:
    builder2.append(2**63)
    print(f"✓ append() successfully handled {2**63}")
    print(f"  Result: {builder2.snapshot().to_list()}")
except Exception as e:
    print(f"✗ append() also failed: {e}")

print("\nComparison with direct array construction:")
# Test if awkward arrays can handle large integers
try:
    direct = ak.Array([2**63, 2**64, 2**100])
    print(f"✓ Direct array construction handled large integers")
    print(f"  Result: {direct.to_list()}")
except Exception as e:
    print(f"✗ Direct construction failed: {e}")