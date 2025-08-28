"""Property-based tests for pydantic.root_model.RootModel"""

import copy
import pickle
from typing import List, Dict, Any, Union

from hypothesis import given, strategies as st, assume, settings
from pydantic import RootModel, ValidationError
import pytest


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
    
    class JsonModel(RootModel[Any]):
        pass
    
    # Create model instance
    model = JsonModel(data)
    
    # Perform round-trip
    json_str = model.model_dump_json()
    restored = JsonModel.model_validate_json(json_str)
    
    # Check round-trip property
    assert restored.root == model.root
    assert restored == model


# Test 2: Shallow copy shares root object
@given(json_strategy)
def test_shallow_copy_shares_root(data):
    """Test that shallow copy shares the root object"""
    
    class TestModel(RootModel[Any]):
        pass
    
    original = TestModel(data)
    shallow = copy.copy(original)
    
    # Different model instances
    assert original is not shallow
    
    # But same root object (shallow copy)
    assert original.root is shallow.root
    
    # Same fields_set
    assert original.__pydantic_fields_set__ == shallow.__pydantic_fields_set__


# Test 3: Deep copy creates independent root
@given(json_strategy)
def test_deep_copy_independence(data):
    """Test that deep copy creates independent root object"""
    
    class TestModel(RootModel[Any]):
        pass
    
    original = TestModel(data)
    deep = copy.deepcopy(original)
    
    # Different model instances
    assert original is not deep
    
    # Different root objects (deep copy)
    if isinstance(data, (list, dict)):
        assert original.root is not deep.root
    
    # But equal content
    assert original.root == deep.root
    assert original == deep
    
    # Same fields_set (copied, not deep copied as per implementation)
    assert original.__pydantic_fields_set__ == deep.__pydantic_fields_set__


# Test 4: Pickle round-trip property
@given(json_strategy)
def test_pickle_roundtrip(data):
    """Test that pickle.loads(pickle.dumps(x)) == x"""
    
    class PickleModel(RootModel[Any]):
        pass
    
    original = PickleModel(data)
    
    # Pickle and unpickle
    pickled = pickle.dumps(original)
    restored = pickle.loads(pickled)
    
    # Check restoration
    assert restored.root == original.root
    assert restored == original
    assert restored.__pydantic_fields_set__ == original.__pydantic_fields_set__


# Test 5: Initialization contract - dict root with kwargs
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=0,
        max_size=5
    )
)
def test_dict_init_with_kwargs(data):
    """Test that dict RootModel can be initialized with kwargs"""
    
    class DictModel(RootModel[Dict[str, int]]):
        pass
    
    # Initialize with positional argument
    model1 = DictModel(data)
    assert model1.root == data
    
    # Initialize with keyword arguments
    if data:  # Only if dict is not empty
        model2 = DictModel(**data)
        assert model2.root == data
        assert model1 == model2


# Test 6: Initialization error - cannot mix positional and kwargs
@given(
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=1, max_size=3),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=1, max_size=3)
)
def test_init_error_mixed_args(pos_data, kw_data):
    """Test that mixing positional and keyword args raises ValueError"""
    
    class DictModel(RootModel[Dict[str, int]]):
        pass
    
    # This should raise ValueError
    with pytest.raises(ValueError, match="accepts either a single positional argument or arbitrary keyword arguments"):
        DictModel(pos_data, **kw_data)


# Test 7: Equality properties
@given(json_strategy, json_strategy)
def test_equality_properties(data1, data2):
    """Test equality properties of RootModel"""
    
    class TestModel(RootModel[Any]):
        pass
    
    model1a = TestModel(data1)
    model1b = TestModel(data1)
    model2 = TestModel(data2)
    
    # Reflexivity
    assert model1a == model1a
    
    # Models with same data are equal
    assert model1a == model1b
    
    # Models with different data are not equal (unless data is equal)
    if data1 != data2:
        assert model1a != model2
    
    # Not equal to non-RootModel
    assert model1a != data1
    assert (model1a == data1) is False


# Test 8: model_construct bypasses validation but preserves structure
@given(json_strategy)
def test_model_construct_preserves_data(data):
    """Test that model_construct preserves data without validation"""
    
    class TestModel(RootModel[Any]):
        pass
    
    # Construct without validation
    constructed = TestModel.model_construct(data)
    
    # Should have the same data
    assert constructed.root == data
    
    # Should work with round-trip
    if isinstance(data, (bool, int, float, str, list, dict, type(None))):
        json_str = constructed.model_dump_json()
        restored = TestModel.model_validate_json(json_str)
        assert restored.root == data


# Test 9: Complex nested structures
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.lists(st.integers(min_value=-100, max_value=100), max_size=5),
        max_size=5
    )
)
def test_nested_structure_operations(data):
    """Test operations on nested structures"""
    
    class NestedModel(RootModel[Dict[str, List[int]]]):
        pass
    
    original = NestedModel(data)
    
    # Test JSON round-trip
    json_str = original.model_dump_json()
    restored = NestedModel.model_validate_json(json_str)
    assert restored.root == original.root
    
    # Test pickle round-trip
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    assert unpickled.root == original.root
    
    # Test deep copy independence
    deep = copy.deepcopy(original)
    assert deep.root == original.root
    if data:  # Only if not empty
        assert deep.root is not original.root


# Test 10: Type preservation through operations
@given(
    st.one_of(
        st.lists(st.floats(allow_nan=False, allow_infinity=False), max_size=10),
        st.lists(st.integers(), max_size=10),
        st.lists(st.text(max_size=10), max_size=10),
        st.lists(st.booleans(), max_size=10),
    )
)
def test_type_preservation(data):
    """Test that types are preserved through various operations"""
    
    class TypedListModel(RootModel[List[Any]]):
        pass
    
    original = TypedListModel(data)
    
    # Through JSON
    json_str = original.model_dump_json()
    from_json = TypedListModel.model_validate_json(json_str)
    
    # Check types are preserved
    assert type(from_json.root) == type(original.root)
    assert len(from_json.root) == len(original.root)
    
    for orig_item, json_item in zip(original.root, from_json.root):
        # JSON serialization may convert some types
        if isinstance(orig_item, float) and orig_item == int(orig_item):
            # JSON may convert 1.0 to 1
            assert json_item == orig_item
        else:
            assert type(json_item) == type(orig_item)
    
    # Through pickle (should preserve exact types)
    pickled = pickle.dumps(original)
    from_pickle = pickle.loads(pickled)
    
    assert type(from_pickle.root) == type(original.root)
    for orig_item, pickle_item in zip(original.root, from_pickle.root):
        assert type(pickle_item) == type(orig_item)
        assert pickle_item == orig_item


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])