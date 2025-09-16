#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import copy
import numpy as np
import awkward as ak
from hypothesis import given, strategies as st, assume, settings, example
import traceback


@st.composite  
def complex_record_strategy(draw):
    """Generate records with more complex data types."""
    length = draw(st.integers(min_value=1, max_value=20))
    n_fields = draw(st.integers(min_value=1, max_value=5))
    
    contents = []
    for _ in range(n_fields):
        # Mix different array types
        array_type = draw(st.sampled_from(["int", "float", "bool", "complex"]))
        
        if array_type == "int":
            data = np.array(draw(st.lists(
                st.integers(min_value=-2**31, max_value=2**31-1),
                min_size=length, max_size=length
            )), dtype=np.int32)
        elif array_type == "float":
            data = np.array(draw(st.lists(
                st.floats(allow_nan=True, allow_infinity=True),
                min_size=length, max_size=length
            )), dtype=np.float64)
        elif array_type == "bool":
            data = np.array(draw(st.lists(
                st.booleans(),
                min_size=length, max_size=length
            )), dtype=bool)
        else:  # complex
            real_parts = draw(st.lists(
                st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=length, max_size=length
            ))
            imag_parts = draw(st.lists(
                st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=length, max_size=length
            ))
            data = np.array([complex(r, i) for r, i in zip(real_parts, imag_parts)])
        
        contents.append(ak.contents.NumpyArray(data))
    
    fields = [f"f{i}" for i in range(n_fields)] if draw(st.booleans()) else None
    array = ak.contents.RecordArray(contents, fields=fields)
    at = draw(st.integers(min_value=0, max_value=length-1))
    
    return ak.record.Record(array, at)


# Debug the materialize_idempotence failure
@given(complex_record_strategy())
@settings(max_examples=10)
def test_materialize_idempotence_debug(record):
    """Test that materialize is idempotent."""
    print(f"\nTesting record at={record.at}, fields={record.fields}")
    
    try:
        mat1 = record.materialize()
        print(f"  First materialize: at={mat1.at}")
        
        mat2 = mat1.materialize()
        print(f"  Second materialize: at={mat2.at}")
        
        # Should be equivalent
        assert mat1.at == mat2.at
        assert mat1.fields == mat2.fields
        
        list1 = mat1.to_list()
        list2 = mat2.to_list()
        
        print(f"  List1: {list1}")
        print(f"  List2: {list2}")
        
        assert list1 == list2
        
    except AssertionError as e:
        print(f"  ASSERTION FAILED: {e}")
        raise
    except AttributeError as e:
        print(f"  ATTRIBUTE ERROR: {e}")
        print(f"  mat1 type: {type(mat1)}")
        print(f"  mat1 dir: {[x for x in dir(mat1) if not x.startswith('_')]}")
        raise


# Debug the intensive_property_combinations failure
@given(complex_record_strategy())
@settings(max_examples=10)
def test_intensive_debug(record):
    """Debug intensive test combining multiple operations."""
    print(f"\nTesting record at={record.at}, is_tuple={record.is_tuple}")
    
    try:
        r1 = record.copy()
        print(f"  After copy: at={r1.at}")
        
        r2 = r1.to_tuple()
        print(f"  After to_tuple: at={r2.at}, is_tuple={r2.is_tuple}")
        
        r3 = r2.materialize()
        print(f"  After materialize: at={r3.at}")
        
        r4 = r3.to_packed()
        print(f"  After to_packed: at={r4.at}")
        
        # All should maintain the same position
        assert r4.at == record.at or (record.array.length == 1 and r4.at == 0)
        
        # to_list should give equivalent results (accounting for tuple conversion)
        original = record.to_list()
        final = r4.to_list()
        
        print(f"  Original to_list: {original}")
        print(f"  Final to_list: {final}")
        
        if not record.is_tuple and r4.is_tuple:
            # Converted to tuple, so compare values
            assert isinstance(final, tuple)
            if isinstance(original, dict):
                assert len(final) == len(original)
        
    except AttributeError as e:
        print(f"  ATTRIBUTE ERROR: {e}")
        traceback.print_exc()
        # Try to understand what went wrong
        print(f"  Current object type: {type(locals().get('r4', locals().get('r3', locals().get('r2', locals().get('r1', record)))))}")
        raise
    except Exception as e:
        print(f"  OTHER ERROR: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    print("Debugging test failures...")
    print("=" * 50)
    
    print("\nDebugging materialize_idempotence:")
    try:
        test_materialize_idempotence_debug()
        print("✓ All tests passed")
    except Exception as e:
        print(f"✗ Failed with: {e}")
    
    print("\n" + "=" * 50)
    print("\nDebugging intensive_property_combinations:")
    try:
        test_intensive_debug()
        print("✓ All tests passed")
    except Exception as e:
        print(f"✗ Failed with: {e}")