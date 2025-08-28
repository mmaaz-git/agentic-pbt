"""Property-based tests for numpy.rec module"""

import numpy as np
import numpy.rec as rec
from hypothesis import given, strategies as st, assume, settings
from collections import Counter
import math
import warnings


@given(st.lists(st.one_of(st.integers(), st.text(), st.floats(allow_nan=False))))
def test_find_duplicate_properties(lst):
    """Test that find_duplicate correctly identifies all duplicates"""
    result = rec.find_duplicate(lst)
    
    # Property 1: All items in result should appear more than once in original list
    for item in result:
        assert lst.count(item) > 1, f"Item {item} is not a duplicate"
    
    # Property 2: All items that appear more than once should be in result
    counts = Counter(lst)
    expected_dups = [item for item, count in counts.items() if count > 1]
    assert set(result) == set(expected_dups), f"Mismatch: got {result}, expected {expected_dups}"
    
    # Property 3: No duplicates in the result itself
    assert len(result) == len(set(result)), f"Result contains duplicates: {result}"


@given(st.lists(st.sampled_from(['i4', 'f8', 'S5', 'u1', 'i8', 'f4']), min_size=1, max_size=10))
def test_format_parser_with_default_names(formats):
    """Test format_parser generates correct default field names"""
    parser = rec.format_parser(formats, names=None, titles=None)
    
    # Property: Default names should be f0, f1, f2, ...
    expected_names = [f'f{i}' for i in range(len(formats))]
    assert parser._names == expected_names
    assert parser.dtype.names == tuple(expected_names)


@given(
    st.lists(st.sampled_from(['i4', 'f8', 'S5']), min_size=1, max_size=5),
    st.lists(st.text(min_size=1, max_size=10).filter(lambda x: ',' not in x), min_size=1, max_size=5)
)
def test_format_parser_name_assignment(formats, names):
    """Test format_parser handles names correctly"""
    # Ensure we have at least as many formats as names or vice versa
    if len(names) > len(formats):
        names = names[:len(formats)]
    
    # Ensure no duplicate names
    names = list(dict.fromkeys(names))  # Remove duplicates while preserving order
    
    parser = rec.format_parser(formats, names=names, titles=None)
    
    # Property: Names should be used first, then default names
    expected_names = names.copy()
    expected_names += [f'f{i}' for i in range(len(names), len(formats))]
    
    assert parser._names == expected_names


@given(st.lists(st.sampled_from(['i4', 'f8']), min_size=1, max_size=5))
def test_format_parser_comma_separated_names(formats):
    """Test format_parser handles comma-separated name strings"""
    # Generate names
    names_list = [f'col{i}' for i in range(len(formats))]
    names_str = ', '.join(names_list)
    
    parser = rec.format_parser(formats, names=names_str, titles=None)
    
    # Property: Comma-separated string should be split correctly
    assert parser._names == names_list


@given(
    st.lists(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=5), 
             min_size=1, max_size=3),
    st.lists(st.text(min_size=1, max_size=5).filter(lambda x: ',' not in x), min_size=1, max_size=3)
)
def test_fromarrays_fromrecords_round_trip(arrays_data, field_names):
    """Test round-trip conversion between fromarrays and record access"""
    # Ensure consistent shapes and unique field names
    if not arrays_data:
        return
    
    common_length = len(arrays_data[0])
    arrays = [np.array(arr[:common_length] if len(arr) >= common_length else arr + [0]*(common_length - len(arr))) 
              for arr in arrays_data]
    
    # Make field names unique and match array count
    field_names = list(dict.fromkeys(field_names))[:len(arrays)]
    if len(field_names) < len(arrays):
        field_names += [f'f{i}' for i in range(len(field_names), len(arrays))]
    
    # Create record array
    rec_array = rec.fromarrays(arrays, names=field_names)
    
    # Property 1: Field access should match original arrays
    for i, name in enumerate(field_names):
        np.testing.assert_array_equal(rec_array[name], arrays[i])
    
    # Property 2: Length should be preserved
    assert len(rec_array) == common_length


@given(st.lists(st.tuples(st.integers(), st.floats(allow_nan=False)), min_size=1, max_size=10))
def test_fromrecords_preserves_data(records):
    """Test that fromrecords preserves input data"""
    rec_array = rec.fromrecords(records, names='x,y')
    
    # Property: Data should be preserved
    for i, (x, y) in enumerate(records):
        assert rec_array[i]['x'] == x
        if not math.isnan(y):
            assert math.isclose(rec_array[i]['y'], y, rel_tol=1e-7)


@given(st.integers(min_value=0, max_value=100))
def test_recarray_attribute_vs_index_access(size):
    """Test that attribute access matches index access in recarrays"""
    if size == 0:
        return
        
    # Create a simple recarray
    dtype = np.dtype([('x', 'i4'), ('y', 'f8')])
    arr = np.zeros(size, dtype=dtype)
    rec_arr = arr.view(rec.recarray)
    
    # Fill with some data
    rec_arr.x[:] = np.arange(size)
    rec_arr.y[:] = np.arange(size) * 1.5
    
    # Property: Attribute access should match field access
    np.testing.assert_array_equal(rec_arr.x, rec_arr['x'])
    np.testing.assert_array_equal(rec_arr.y, rec_arr['y'])


@given(st.data())
def test_format_parser_duplicate_names_detection(data):
    """Test that format_parser detects duplicate field names"""
    formats = ['i4', 'f8', 'S5']
    
    # Generate names with at least one duplicate
    base_name = data.draw(st.text(min_size=1, max_size=5).filter(lambda x: ',' not in x))
    names = [base_name, base_name, 'other']
    
    # Property: Should raise ValueError for duplicate names
    try:
        parser = rec.format_parser(formats, names=names, titles=None)
        assert False, "Should have raised ValueError for duplicate names"
    except ValueError as e:
        assert "Duplicate field names" in str(e)


@given(
    st.lists(st.sampled_from(['i1', 'i2', 'i4', 'i8', 'u1', 'u2', 'u4', 'u8', 'f4', 'f8']), 
             min_size=1, max_size=5),
    st.sampled_from(['<', '>', '=', '|'])
)
def test_format_parser_byteorder(formats, byteorder):
    """Test that format_parser correctly handles byteorder specification"""
    parser = rec.format_parser(formats, names=None, titles=None, byteorder=byteorder)
    
    # Property: dtype should have the specified byteorder (when applicable)
    dtype = parser.dtype
    
    # For numeric types, check byteorder is applied
    if byteorder != '|':  # '|' means not applicable (1-byte types)
        for field_name in dtype.names:
            field_dtype = dtype.fields[field_name][0]
            # Only check for multi-byte numeric types
            if field_dtype.itemsize > 1 and field_dtype.kind in 'iuf':
                expected_order = byteorder if byteorder != '=' else '='
                actual_order = field_dtype.byteorder
                # Native order ('=') may appear as '<' or '>' depending on system
                if expected_order == '=' and actual_order in '<>':
                    continue  # This is acceptable
                if actual_order == '=' and expected_order in '<>':
                    continue  # Also acceptable for native
                if expected_order != '=' and actual_order != '=':
                    assert actual_order == expected_order, f"Byteorder mismatch: expected {expected_order}, got {actual_order}"


@given(st.lists(st.integers(min_value=-1000, max_value=1000), min_size=10, max_size=100))
def test_fromarrays_shape_preservation(data):
    """Test that fromarrays preserves shape information correctly"""
    # Create arrays with specific shape
    arr1 = np.array(data).reshape(-1, 2) if len(data) % 2 == 0 else np.array(data[:-1]).reshape(-1, 2)
    arr2 = np.array(data[:len(arr1)]).reshape(arr1.shape)
    
    if arr1.size == 0:
        return
    
    # Create record array
    rec_array = rec.fromarrays([arr1, arr2], names='a,b')
    
    # Property: Shape should be preserved
    assert rec_array.shape == arr1.shape
    assert rec_array['a'].shape == arr1.shape
    assert rec_array['b'].shape == arr2.shape


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run the tests
    exit_code = pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])
    sys.exit(exit_code)