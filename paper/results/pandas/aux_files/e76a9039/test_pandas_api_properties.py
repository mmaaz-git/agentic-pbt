import math
import random
import string
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from hypothesis import assume, given, settings, strategies as st
from pandas.api import types
from pandas.api.indexers import check_array_indexer


# Test 1: is_dtype_equal should be reflexive
@given(st.sampled_from(['int32', 'int64', 'float32', 'float64', 'object', 'string', 'bool', 'datetime64[ns]', 'timedelta64[ns]']))
def test_is_dtype_equal_reflexive(dtype_str):
    """Property: is_dtype_equal(x, x) should always be True (reflexivity)"""
    dtype = np.dtype(dtype_str) if not dtype_str.startswith('datetime') and not dtype_str.startswith('timedelta') else dtype_str
    assert types.is_dtype_equal(dtype, dtype)


# Test 2: is_dtype_equal should be symmetric
@given(
    st.sampled_from(['int32', 'int64', 'float32', 'float64', 'object', 'bool']),
    st.sampled_from(['int32', 'int64', 'float32', 'float64', 'object', 'bool'])
)
def test_is_dtype_equal_symmetric(dtype1_str, dtype2_str):
    """Property: is_dtype_equal(x, y) == is_dtype_equal(y, x) (symmetry)"""
    dtype1 = np.dtype(dtype1_str)
    dtype2 = np.dtype(dtype2_str)
    assert types.is_dtype_equal(dtype1, dtype2) == types.is_dtype_equal(dtype2, dtype1)


# Test 3: infer_dtype consistency with numpy arrays
@given(st.lists(st.integers(), min_size=1))
def test_infer_dtype_integer_arrays(int_list):
    """Property: infer_dtype should consistently identify integer arrays"""
    arr = np.array(int_list)
    inferred = types.infer_dtype(arr)
    assert inferred in ['integer', 'int64', 'int32', 'int16', 'int8']


# Test 4: infer_dtype with mixed types
@given(st.lists(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()), min_size=2))
def test_infer_dtype_mixed(mixed_list):
    """Property: mixed type lists should be inferred as 'mixed' or specific type if uniform"""
    # Filter to ensure we have at least one element
    assume(len(mixed_list) > 0)
    
    inferred = types.infer_dtype(mixed_list)
    
    # Check if all elements are same type
    types_set = set(type(x) for x in mixed_list)
    if len(types_set) == 1:
        # All same type - should not be 'mixed'
        assert inferred != 'mixed'
    # If different types, could be 'mixed' or a common super type


# Test 5: union_categoricals preserves all unique values
@given(
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=10),
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=10)
)
def test_union_categoricals_preserves_values(list1, list2):
    """Property: union_categoricals should preserve all unique categories"""
    cat1 = pd.Categorical(list1)
    cat2 = pd.Categorical(list2)
    
    result = types.union_categoricals([cat1, cat2])
    
    # All values from both categoricals should be in the result
    all_values = list(cat1) + list(cat2)
    for val in all_values:
        assert val in result.values


# Test 6: check_array_indexer with boolean masks
@given(
    st.lists(st.integers(), min_size=1, max_size=100),
    st.lists(st.booleans(), min_size=1, max_size=100)
)
def test_check_array_indexer_boolean_mask(array_data, bool_mask):
    """Property: Boolean masks must have same length as array"""
    array = np.array(array_data)
    mask = np.array(bool_mask)
    
    if len(array) == len(mask):
        # Should work without error
        result = check_array_indexer(array, mask)
        assert result is not None
    else:
        # Should raise an error for mismatched lengths
        with pytest.raises((IndexError, ValueError)):
            check_array_indexer(array, mask)


# Test 7: Type checking functions consistency
@given(st.integers())
def test_type_checking_consistency_integers(val):
    """Property: Type checking functions should be consistent for integers"""
    # is_integer should return True for all integers
    assert types.is_integer(val) == True
    # is_float should return False for integers
    assert types.is_float(val) == False
    # is_number should return True
    assert types.is_number(val) == True
    # is_scalar should return True
    assert types.is_scalar(val) == True


# Test 8: Type checking functions consistency for floats
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_type_checking_consistency_floats(val):
    """Property: Type checking functions should be consistent for floats"""
    # is_float should return True for all floats
    assert types.is_float(val) == True
    # is_integer should return False for floats
    assert types.is_integer(val) == False
    # is_number should return True
    assert types.is_number(val) == True
    # is_scalar should return True
    assert types.is_scalar(val) == True


# Test 9: is_list_like consistency
@given(st.one_of(
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_is_list_like_containers(container):
    """Property: is_list_like should identify common container types"""
    assert types.is_list_like(container) == True


# Test 10: is_dict_like consistency
@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_is_dict_like_dicts(d):
    """Property: is_dict_like should identify dictionaries"""
    assert types.is_dict_like(d) == True
    # Also should be list_like
    assert types.is_list_like(d) == True


# Test 11: pandas_dtype round-trip
@given(st.sampled_from(['int32', 'int64', 'float32', 'float64', 'object', 'bool']))
def test_pandas_dtype_roundtrip(dtype_str):
    """Property: pandas_dtype should handle numpy dtype strings correctly"""
    dtype = types.pandas_dtype(dtype_str)
    # Should be able to convert back
    assert str(dtype) == dtype_str or dtype.name == dtype_str


# Test 12: is_hashable consistency
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.tuples(st.integers()),
    st.frozensets(st.integers())
))
def test_is_hashable_true_cases(val):
    """Property: is_hashable should return True for hashable types"""
    assert types.is_hashable(val) == True


@given(st.one_of(
    st.lists(st.integers()),
    st.sets(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_is_hashable_false_cases(val):
    """Property: is_hashable should return False for unhashable types"""
    assert types.is_hashable(val) == False


# Test 13: is_iterator consistency
@given(st.lists(st.integers()))
def test_is_iterator_consistency(lst):
    """Property: iter() should create iterators, lists should not be iterators"""
    # Lists are not iterators
    assert types.is_iterator(lst) == False
    # iter(list) creates an iterator
    assert types.is_iterator(iter(lst)) == True


# Test 14: infer_dtype with skipna parameter
@given(
    st.lists(st.one_of(st.integers(), st.none()), min_size=1, max_size=20),
    st.booleans()
)
def test_infer_dtype_skipna(values, skipna):
    """Property: skipna parameter should affect inference with None values"""
    has_none = None in values
    result = types.infer_dtype(values, skipna=skipna)
    
    if has_none and not skipna:
        # When None is present and skipna=False, might affect type inference
        # Just verify it doesn't crash
        assert isinstance(result, str)
    else:
        # Should return a valid type string
        assert isinstance(result, str)


# Test 15: Complex number type checking
@given(st.complex_numbers(allow_nan=False, allow_infinity=False))
def test_is_complex_consistency(val):
    """Property: is_complex should identify complex numbers"""
    assert types.is_complex(val) == True
    assert types.is_number(val) == True
    assert types.is_scalar(val) == True
    assert types.is_float(val) == False
    assert types.is_integer(val) == False


# Test 16: Testing special string pattern checks
@given(st.text())
def test_is_re_compilable(text):
    """Property: is_re_compilable should not crash on any string"""
    result = types.is_re_compilable(text)
    assert isinstance(result, bool)
    
    # If it's compilable, we should be able to compile it
    if result:
        import re
        try:
            re.compile(text)
        except:
            # This would be a bug - is_re_compilable said it's compilable but it's not
            assert False, f"is_re_compilable returned True but pattern '{text}' cannot be compiled"


# Test 17: Array-like detection
@given(st.one_of(
    st.lists(st.integers()),
    st.binary(),
    st.text()
))
def test_is_array_like_edge_cases(val):
    """Property: is_array_like should handle various types consistently"""
    result = types.is_array_like(val)
    assert isinstance(result, bool)
    
    # Strings should be array-like (they're sequences)
    if isinstance(val, str):
        assert result == True
    # Lists should be array-like
    elif isinstance(val, list):
        assert result == True
    # Bytes should be array-like
    elif isinstance(val, bytes):
        assert result == True


# Test 18: Named tuple detection
@given(st.tuples(st.integers(), st.text()))
def test_is_named_tuple_regular_tuples(tup):
    """Property: Regular tuples should not be named tuples"""
    assert types.is_named_tuple(tup) == False


# Test 19: File-like object detection
@given(st.text())
def test_is_file_like_strings(s):
    """Property: Strings should not be file-like"""
    assert types.is_file_like(s) == False


# Test 20: Sparse array detection
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False)))
def test_is_sparse_regular_arrays(lst):
    """Property: Regular lists and numpy arrays should not be sparse"""
    assert types.is_sparse(lst) == False
    assert types.is_sparse(np.array(lst)) == False