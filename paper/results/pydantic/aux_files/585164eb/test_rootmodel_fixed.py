"""Property-based tests for pydantic.root_model.RootModel - Fixed version"""

import copy
import pickle
from typing import List, Dict, Any, Union

from hypothesis import given, strategies as st, assume, settings
from pydantic import RootModel, ValidationError
import pytest


# Define global RootModel classes for pickle testing
class GlobalJsonModel(RootModel[Any]):
    pass


class GlobalDictModel(RootModel[Dict[str, int]]):
    pass


class GlobalNestedModel(RootModel[Dict[str, List[int]]]):
    pass


class GlobalTypedListModel(RootModel[List[Any]]):
    pass


# Strategy for generating valid JSON-serializable data
json_strategy = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10),
    ),
    max_leaves=50,
)


# Test 1: JSON round-trip property
@given(json_strategy)
def test_json_roundtrip_property(data):
    """Test that model_validate_json(model_dump_json(x)) == x"""
    
    model = GlobalJsonModel(data)
    json_str = model.model_dump_json()
    restored = GlobalJsonModel.model_validate_json(json_str)
    
    assert restored.root == model.root
    assert restored == model


# Test 2: Pickle round-trip property (fixed)
@given(json_strategy)
def test_pickle_roundtrip(data):
    """Test that pickle.loads(pickle.dumps(x)) == x"""
    
    original = GlobalJsonModel(data)
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    assert restored.root == original.root
    assert restored == original
    assert restored.__pydantic_fields_set__ == original.__pydantic_fields_set__


# Test 3: Complex nested structures with pickle
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.lists(st.integers(min_value=-100, max_value=100), max_size=5),
        max_size=5
    )
)
def test_nested_structure_operations(data):
    """Test operations on nested structures"""
    
    original = GlobalNestedModel(data)
    
    # Test JSON round-trip
    json_str = original.model_dump_json()
    restored = GlobalNestedModel.model_validate_json(json_str)
    assert restored.root == original.root
    
    # Test pickle round-trip
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    assert unpickled.root == original.root
    
    # Test deep copy independence
    deep = copy.deepcopy(original)
    assert deep.root == original.root
    if data:
        assert deep.root is not original.root


# Test 4: Special edge cases with nested dicts
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['Lu', 'Ll', 'Nd'])),
        st.recursive(
            st.one_of(st.integers(), st.text(max_size=10), st.none()),
            lambda children: st.dictionaries(
                st.text(min_size=1, max_size=5),
                children,
                max_size=3
            ),
            max_leaves=10
        ),
        min_size=0,
        max_size=5
    )
)
def test_nested_dict_validation(data):
    """Test validation and round-trips with nested dictionaries"""
    
    class NestedDictModel(RootModel[Dict[str, Any]]):
        pass
    
    model = NestedDictModel(data)
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = NestedDictModel.model_validate_json(json_str)
    assert restored.root == model.root
    
    # model_dump should return the root directly
    dumped = model.model_dump()
    assert dumped == data
    
    # model_validate should accept the dumped data
    revalidated = NestedDictModel.model_validate(dumped)
    assert revalidated.root == model.root


# Test 5: Unicode and special characters
@given(
    st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(min_codepoint=0x80, max_codepoint=0x10ffff)),
        st.one_of(
            st.text(alphabet=st.characters(min_codepoint=0x80, max_codepoint=0x10ffff)),
            st.integers(),
            st.lists(st.text(max_size=5), max_size=3)
        ),
        max_size=5
    )
)
def test_unicode_handling(data):
    """Test handling of Unicode and special characters"""
    
    class UnicodeModel(RootModel[Dict[str, Any]]):
        pass
    
    model = UnicodeModel(data)
    
    # JSON round-trip with Unicode
    json_str = model.model_dump_json()
    restored = UnicodeModel.model_validate_json(json_str)
    assert restored.root == model.root


# Test 6: Empty and edge case values
@given(
    st.one_of(
        st.just({}),
        st.just([]),
        st.just(""),
        st.just(0),
        st.just(0.0),
        st.just(False),
        st.dictionaries(st.text(min_size=1, max_size=1), st.just(None)),
        st.lists(st.none(), min_size=1, max_size=5)
    )
)
def test_edge_case_values(data):
    """Test edge case values like empty containers and falsy values"""
    
    model = GlobalJsonModel(data)
    
    # These edge cases should all work
    json_str = model.model_dump_json()
    restored = GlobalJsonModel.model_validate_json(json_str)
    assert restored.root == model.root
    
    # Check that model_dump preserves the value
    dumped = model.model_dump()
    assert dumped == data


# Test 7: model_construct with invalid data
@given(json_strategy)
def test_model_construct_bypass_validation(data):
    """Test that model_construct truly bypasses validation"""
    
    class StrictIntListModel(RootModel[List[int]]):
        pass
    
    # model_construct should accept any data without validation
    constructed = StrictIntListModel.model_construct(data)
    assert constructed.root == data
    
    # If data is not actually a list of ints, normal construction should fail
    if not (isinstance(data, list) and all(isinstance(x, int) for x in data)):
        with pytest.raises(ValidationError):
            StrictIntListModel(data)


# Test 8: Round-trip with model_dump modes
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.floats(allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=5
    )
)
def test_model_dump_modes(data):
    """Test model_dump with different modes"""
    
    class FloatDictModel(RootModel[Dict[str, float]]):
        pass
    
    model = FloatDictModel(data)
    
    # Python mode (default)
    python_dump = model.model_dump(mode='python')
    assert python_dump == data
    
    # JSON mode 
    json_dump = model.model_dump(mode='json')
    # JSON mode should be JSON-serializable
    import json
    json_str = json.dumps(json_dump)
    json_loaded = json.loads(json_str)
    
    # Round-trip through JSON mode
    restored = FloatDictModel.model_validate(json_loaded)
    assert restored.root == model.root


# Test 9: Initialization with very large dictionaries as kwargs
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=3, alphabet=st.characters(categories=['Ll'])),
        st.integers(min_value=0, max_value=100),
        min_size=50,
        max_size=100
    )
)
@settings(max_examples=10)  # Reduce for performance
def test_large_kwargs_init(data):
    """Test initialization with many keyword arguments"""
    
    # Initialize with kwargs
    model = GlobalDictModel(**data)
    
    # Should work the same as positional
    model2 = GlobalDictModel(data)
    
    assert model.root == data
    assert model == model2


# Test 10: State preservation through copy operations
@given(json_strategy)
def test_copy_state_preservation(data):
    """Test that __pydantic_fields_set__ is preserved correctly through copies"""
    
    # Create with model_construct to control fields_set
    original = GlobalJsonModel.model_construct(data, _fields_set=set())
    assert original.__pydantic_fields_set__ == set()
    
    # Shallow copy should preserve fields_set
    shallow = copy.copy(original)
    assert shallow.__pydantic_fields_set__ == set()
    
    # Deep copy should preserve fields_set
    deep = copy.deepcopy(original)
    assert deep.__pydantic_fields_set__ == set()
    
    # Now with fields_set={'root'}
    original2 = GlobalJsonModel.model_construct(data, _fields_set={'root'})
    assert original2.__pydantic_fields_set__ == {'root'}
    
    shallow2 = copy.copy(original2)
    assert shallow2.__pydantic_fields_set__ == {'root'}
    
    deep2 = copy.deepcopy(original2)
    assert deep2.__pydantic_fields_set__ == {'root'}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])