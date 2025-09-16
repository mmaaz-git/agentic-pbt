#!/usr/bin/env python3
"""
Minimal property test to find bugs in awkward.jax
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

print("Testing awkward.jax module for bugs...")

# Test 1: Check if split_buffers has a bug with edge cases
from awkward._connect.jax.trees import split_buffers

# Edge case 1: Key that is exactly "-data"
test_buffers_1 = {"-data": b"test"}
data, other = split_buffers(test_buffers_1)
print(f"Test 1a: Key '-data' -> data={data}, other={other}")
assert "-data" in data, "BUG: Key '-data' not in data_buffers!"

# Edge case 2: Key with no dash before "data"
test_buffers_2 = {"nodedata": b"test", "some-data": b"test2"}  
data, other = split_buffers(test_buffers_2)
print(f"Test 1b: Keys 'nodedata' and 'some-data' -> data={data.keys()}, other={other.keys()}")
# This should show if there's a bug in how the function checks for "-data" suffix

# Edge case 3: Empty key parts
test_buffers_3 = {"": b"test", "-": b"test2", "--data": b"test3"}
try:
    data, other = split_buffers(test_buffers_3)
    print(f"Test 1c: Empty/edge keys -> data={data.keys()}, other={other.keys()}")
except Exception as e:
    print(f"Test 1c: Exception with empty/edge keys: {e}")

# Test 2: Check AuxData with edge cases
from awkward._connect.jax.trees import AuxData
from awkward._layout import HighLevelContext
import awkward as ak

# Edge case: Empty data_buffer_keys tuple
try:
    with HighLevelContext() as ctx:
        form = ak.forms.NumpyForm("bool", form_key="test")
        aux = AuxData(
            data_buffer_keys=(),  # Empty tuple
            other_buffers={},
            form=form,
            length=0,
            ctx=ctx,
            highlevel=True
        )
        # Try to unflatten with empty buffers
        result = aux.unflatten(())
        print(f"Test 2a: Empty buffers unflatten succeeded: {result}")
except Exception as e:
    print(f"Test 2a: Empty buffers unflatten failed: {e}")

# Test 3: Check for potential race condition in registration
from awkward.jax import _registration_lock, _registration_state

# Try to access state without lock (potential bug)
print(f"Test 3: Registration state without lock: {_registration_state}")

# Test 4: Check assert_never edge case
from awkward.jax import assert_never

class WeirdRepr:
    def __repr__(self):
        raise ValueError("Cannot repr this object")

try:
    assert_never(WeirdRepr())
except AssertionError as e:
    print(f"Test 4a: assert_never with weird repr: passed")
except Exception as e:
    print(f"Test 4a: BUG - assert_never failed with: {e}")

# Test 5: Check if registration can be called multiple times
from awkward.jax import _register

try:
    # Try to call _register multiple times
    _register()
    _register()  
    _register()
    print("Test 5: Multiple _register calls succeeded")
except Exception as e:
    print(f"Test 5: Multiple _register calls failed: {e}")

print("\nTests completed. Check output for potential bugs.")