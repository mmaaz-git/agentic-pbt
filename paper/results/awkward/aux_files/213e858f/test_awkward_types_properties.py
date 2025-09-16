#!/usr/bin/env python3
"""Property-based tests for awkward.types module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import hypothesis


# Strategies for generating types
@st.composite
def numpy_type_strategy(draw):
    """Generate valid NumpyType instances."""
    primitives = ["bool", "int8", "uint8", "int16", "uint16", 
                  "int32", "uint32", "int64", "uint64", 
                  "float32", "float64", "complex64", "complex128"]
    primitive = draw(st.sampled_from(primitives))
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10), 
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.NumpyType(primitive, parameters=params)
    else:
        return ak.types.NumpyType(primitive)


@st.composite  
def list_type_strategy(draw, max_depth=3):
    """Generate ListType instances."""
    if max_depth <= 0:
        content = draw(numpy_type_strategy())
    else:
        content = draw(type_strategy(max_depth - 1))
    
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10),
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.ListType(content, parameters=params)
    else:
        return ak.types.ListType(content)


@st.composite
def regular_type_strategy(draw, max_depth=3):
    """Generate RegularType instances."""
    if max_depth <= 0:
        content = draw(numpy_type_strategy())
    else:
        content = draw(type_strategy(max_depth - 1))
    size = draw(st.integers(min_value=0, max_value=100))
    
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10),
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.RegularType(content, size, parameters=params)
    else:
        return ak.types.RegularType(content, size)


@st.composite
def option_type_strategy(draw, max_depth=3):
    """Generate OptionType instances."""
    if max_depth <= 0:
        content = draw(numpy_type_strategy())
    else:
        content = draw(type_strategy(max_depth - 1))
    
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10),
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.OptionType(content, parameters=params)
    else:
        return ak.types.OptionType(content)


@st.composite
def record_type_strategy(draw, max_depth=3):
    """Generate RecordType instances."""
    num_fields = draw(st.integers(min_value=0, max_value=5))
    
    if max_depth <= 0:
        contents = [draw(numpy_type_strategy()) for _ in range(num_fields)]
    else:
        contents = [draw(type_strategy(max_depth - 1)) for _ in range(num_fields)]
    
    # Decide between tuple (fields=None) or record (fields=list)
    is_tuple = draw(st.booleans())
    if is_tuple:
        fields = None
    else:
        # Generate unique field names
        fields = draw(st.lists(st.text(min_size=1, max_size=10), 
                                min_size=num_fields, max_size=num_fields, unique=True))
    
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10),
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.RecordType(contents, fields, parameters=params)
    else:
        return ak.types.RecordType(contents, fields)


@st.composite
def union_type_strategy(draw, max_depth=3):
    """Generate UnionType instances."""
    num_contents = draw(st.integers(min_value=1, max_value=4))
    
    if max_depth <= 0:
        contents = [draw(numpy_type_strategy()) for _ in range(num_contents)]
    else:
        contents = [draw(type_strategy(max_depth - 1)) for _ in range(num_contents)]
    
    include_params = draw(st.booleans())
    if include_params:
        params = draw(st.dictionaries(st.text(min_size=1, max_size=10),
                                       st.one_of(st.none(), st.text(), st.integers(), st.booleans())))
        return ak.types.UnionType(contents, parameters=params)
    else:
        return ak.types.UnionType(contents)


@st.composite
def type_strategy(draw, max_depth=3):
    """Generate any Type instance."""
    if max_depth <= 0:
        return draw(numpy_type_strategy())
    
    return draw(st.one_of(
        numpy_type_strategy(),
        list_type_strategy(max_depth),
        regular_type_strategy(max_depth),
        option_type_strategy(max_depth),
        record_type_strategy(max_depth),
        union_type_strategy(max_depth)
    ))


# Property 1: from_datashape round-trip
@given(type_strategy(max_depth=2))
@settings(max_examples=200)
def test_from_datashape_round_trip(type_obj):
    """Test that from_datashape(str(type)) == type."""
    type_str = str(type_obj)
    
    # Skip types with categorical parameters as they might need special handling
    if "__categorical__" in str(type_obj._parameters if hasattr(type_obj, '_parameters') else {}):
        assume(False)
    
    # Skip types with special array parameters that might affect string representation
    if hasattr(type_obj, '_parameters') and type_obj._parameters:
        if "__array__" in type_obj._parameters:
            assume(False)
            
    # Skip named record types as they have special string representations
    if isinstance(type_obj, ak.types.RecordType) and type_obj.parameter("__record__"):
        assume(False)
    
    try:
        parsed = ak.types.from_datashape(type_str, highlevel=False)
        assert type_obj.is_equal_to(parsed), f"Round-trip failed: {type_str} -> {parsed} != {type_obj}"
    except Exception as e:
        # Some types might not be parseable, that's a potential bug
        raise AssertionError(f"Failed to parse type string '{type_str}': {e}")


# Property 2: UnionType equality is order-invariant
@given(union_type_strategy(max_depth=2))
@settings(max_examples=100)
def test_union_type_order_invariance(union_type):
    """Test that UnionType equality is invariant to content order."""
    import random
    
    contents = list(union_type.contents)
    if len(contents) > 1:
        # Create a shuffled version
        shuffled_contents = contents.copy()
        random.shuffle(shuffled_contents)
        
        shuffled_union = ak.types.UnionType(shuffled_contents, parameters=union_type._parameters)
        
        assert union_type.is_equal_to(shuffled_union), \
            f"UnionType equality should be order-invariant: {union_type} != {shuffled_union}"


# Property 3: RecordType equality for records is field-order independent
@given(record_type_strategy(max_depth=2))
@settings(max_examples=100)
def test_record_type_field_order_independence(record_type):
    """Test that RecordType equality for records is field-order independent."""
    if not record_type.is_tuple and len(record_type.fields) > 1:
        import random
        
        # Create a permutation of fields and contents
        indices = list(range(len(record_type.fields)))
        random.shuffle(indices)
        
        shuffled_fields = [record_type.fields[i] for i in indices]
        shuffled_contents = [record_type.contents[i] for i in indices]
        
        shuffled_record = ak.types.RecordType(shuffled_contents, shuffled_fields, 
                                               parameters=record_type._parameters)
        
        assert record_type.is_equal_to(shuffled_record), \
            f"RecordType equality should be field-order independent: {record_type} != {shuffled_record}"


# Property 4: RecordType field_to_index and index_to_field are inverses
@given(record_type_strategy(max_depth=1))
@settings(max_examples=100)
def test_record_type_field_index_inverses(record_type):
    """Test that field_to_index and index_to_field are inverses."""
    # Test index -> field -> index
    for i in range(len(record_type.contents)):
        field = record_type.index_to_field(i)
        index = record_type.field_to_index(field)
        assert index == i, f"index_to_field({i}) = {field}, field_to_index({field}) = {index}, expected {i}"
    
    # Test field -> index -> field (for non-tuple records)
    if not record_type.is_tuple:
        for field in record_type.fields:
            index = record_type.field_to_index(field)
            recovered_field = record_type.index_to_field(index)
            assert recovered_field == field, \
                f"field_to_index({field}) = {index}, index_to_field({index}) = {recovered_field}, expected {field}"


# Property 5: Type copy() creates equal objects
@given(type_strategy(max_depth=2))
@settings(max_examples=100)
def test_type_copy_creates_equal(type_obj):
    """Test that copy() creates equal objects."""
    copied = type_obj.copy()
    assert type_obj.is_equal_to(copied), f"Copy should be equal: {type_obj} != {copied}"
    
    # Also test with all_parameters=True
    assert type_obj.is_equal_to(copied, all_parameters=True), \
        f"Copy should be equal with all_parameters=True: {type_obj} != {copied}"


def run_all_tests():
    # Run all tests
    print("Testing property 1: from_datashape round-trip...")
    test_from_datashape_round_trip()
    
    print("Testing property 2: UnionType equality is order-invariant...")
    test_union_type_order_invariance()
    
    print("Testing property 3: RecordType equality for records is field-order independent...")
    test_record_type_field_order_independence()
    
    print("Testing property 4: RecordType field_to_index and index_to_field are inverses...")
    test_record_type_field_index_inverses()
    
    print("Testing property 5: Type copy() creates equal objects...")
    test_type_copy_creates_equal()
    
    print("All tests completed!")

if __name__ == "__main__":
    run_all_tests()