#!/usr/bin/env python3
"""
Run property-based tests for awkward.jax module
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import traceback

import awkward as ak
import awkward.jax
from awkward._connect.jax.trees import split_buffers, AuxData
from awkward._layout import HighLevelContext
import awkward._connect.jax as jax_connect


def run_test(test_func, test_name, *args):
    """Run a single test and report results"""
    try:
        test_func(*args)
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed:")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Buffer splitting invariant
def test_buffer_splitting():
    """Test buffer splitting with various inputs"""
    test_cases = [
        # Empty dict
        {},
        # Only data buffers
        {"key1-data": b"test", "key2-data": b"data"},
        # Only other buffers
        {"key1-index": b"test", "key2-offsets": b"data"},
        # Mixed buffers
        {"key1-data": b"test", "key2-index": b"idx", "key3-data": b"more"},
        # Edge case: keys with multiple dashes
        {"some-long-key-data": b"test", "other-key-index": b"idx"},
    ]
    
    for i, buffers in enumerate(test_cases):
        data_buffers, other_buffers = split_buffers(buffers)
        
        # Check invariants
        for key in data_buffers:
            assert key.endswith("-data"), f"Test case {i}: Key {key} in data_buffers doesn't end with '-data'"
        
        for key in other_buffers:
            assert not key.endswith("-data"), f"Test case {i}: Key {key} in other_buffers ends with '-data'"
        
        # Check completeness
        assert set(data_buffers.keys()) | set(other_buffers.keys()) == set(buffers.keys())
        assert set(data_buffers.keys()) & set(other_buffers.keys()) == set()
    
    print("  All buffer splitting test cases passed")


# Test 2: Registration state
def test_registration_state():
    """Test registration state machine"""
    from awkward.jax import _RegistrationState, _registration_state, _registration_lock
    
    with _registration_lock:
        valid_states = [
            _RegistrationState.INIT,
            _RegistrationState.SUCCESS, 
            _RegistrationState.FAILED
        ]
        assert _registration_state in valid_states, f"Invalid state: {_registration_state}"
        print(f"  Registration state is valid: {_registration_state}")


# Test 3: AuxData equality
def test_auxdata_equality():
    """Test AuxData equality properties"""
    # Create test data
    form1 = ak.forms.NumpyForm("bool", form_key="test1")
    form2 = ak.forms.NumpyForm("bool", form_key="test2")
    form3 = ak.forms.NumpyForm("int32", form_key="test3")
    
    with HighLevelContext() as ctx:
        aux1 = AuxData(
            data_buffer_keys=("key1",),
            other_buffers={"key2": b"test"},
            form=form1,
            length=100,
            ctx=ctx,
            highlevel=True
        )
        
        # Test reflexivity
        assert aux1 == aux1, "Reflexivity failed: aux1 != aux1"
        assert not (aux1 != aux1), "Reflexivity failed: aux1 != aux1 returned True"
        
        # Create another identical AuxData
        aux2 = AuxData(
            data_buffer_keys=("key1",),
            other_buffers={"key2": b"test"},
            form=form1,
            length=100,
            ctx=ctx,
            highlevel=True
        )
        
        # Test equality with same form
        assert aux1 == aux2, "Same form equality failed"
        
        # Create AuxData with different form
        aux3 = AuxData(
            data_buffer_keys=("key1",),
            other_buffers={"key2": b"test"},
            form=form2,
            length=100,
            ctx=ctx,
            highlevel=True
        )
        
        # Should not be equal (different form key)
        assert aux1 != aux3, "Different form keys should not be equal"
        
        # Create AuxData with different length
        aux4 = AuxData(
            data_buffer_keys=("key1",),
            other_buffers={"key2": b"test"},
            form=form1,
            length=200,
            ctx=ctx,
            highlevel=True
        )
        
        # Should not be equal (different length)
        assert aux1 != aux4, "Different lengths should not be equal"
        
        print("  All AuxData equality tests passed")


# Test 4: assert_never function
def test_assert_never():
    """Test that assert_never always raises"""
    from awkward.jax import assert_never
    
    test_values = [None, 0, "", "test", 42, [], {}]
    
    for value in test_values:
        try:
            assert_never(value)
            assert False, f"assert_never({value}) didn't raise"
        except AssertionError as e:
            assert f"this should never be run: {value}" in str(e)
    
    print("  assert_never tests passed")


# Test 5: Float0 dtype rejection
def test_float0_rejection():
    """Test that float0 dtypes are rejected"""
    class MockBuffer:
        dtype = np.dtype([("float0", "V")])
    
    form = ak.forms.NumpyForm("bool", form_key="test")
    
    with HighLevelContext() as ctx:
        aux = AuxData(
            data_buffer_keys=("test-data",),
            other_buffers={},
            form=form,
            length=1,
            ctx=ctx,
            highlevel=True
        )
        
        try:
            aux.unflatten((MockBuffer(),))
            assert False, "float0 dtype should have been rejected"
        except TypeError as e:
            assert "float0" in str(e)
            assert "tangents" in str(e)
            print("  float0 rejection test passed")


# Test 6: Import JAX function
def test_import_jax():
    """Test import_jax and assert_registered functions"""
    from awkward.jax import assert_registered, _registration_state, _RegistrationState
    
    try:
        assert_registered()
        print(f"  JAX is registered (state: {_registration_state})")
    except RuntimeError as e:
        if _registration_state == _RegistrationState.INIT:
            assert "JAX features require `ak.jax.register_and_check()`" in str(e)
            print("  JAX not registered (INIT state) - expected error")
        elif _registration_state == _RegistrationState.FAILED:
            assert "but the last call to `ak.jax.register_and_check()` did not succeed" in str(e)
            print("  JAX registration failed - expected error")


def main():
    """Run all tests"""
    print("Running property-based tests for awkward.jax module\n")
    
    results = []
    
    # Run each test
    results.append(run_test(test_buffer_splitting, "Buffer splitting invariant"))
    results.append(run_test(test_registration_state, "Registration state validity"))
    results.append(run_test(test_auxdata_equality, "AuxData equality properties"))
    results.append(run_test(test_assert_never, "assert_never always raises"))
    results.append(run_test(test_float0_rejection, "Float0 dtype rejection"))
    results.append(run_test(test_import_jax, "Import JAX registration check"))
    
    # Summary
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed - no bugs found in awkward.jax")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)