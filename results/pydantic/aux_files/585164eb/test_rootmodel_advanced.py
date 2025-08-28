"""Advanced property-based tests for pydantic.root_model.RootModel - hunting for bugs"""

import copy
import pickle
import json
from typing import List, Dict, Any, Union, Optional

from hypothesis import given, strategies as st, assume, settings, note
from pydantic import RootModel, ValidationError, BaseModel
import pytest


# Test 1: Subclassing and inheritance edge cases
class ParentRootModel(RootModel[Dict[str, int]]):
    """Parent RootModel for testing inheritance"""
    pass


class ChildRootModel(ParentRootModel):
    """Child RootModel - should inherit behavior"""
    pass


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=5))
def test_inheritance_behavior(data):
    """Test that RootModel subclasses work correctly"""
    
    parent = ParentRootModel(data)
    child = ChildRootModel(data)
    
    # Both should have the same root
    assert parent.root == child.root
    
    # JSON round-trip should work for both
    parent_json = parent.model_dump_json()
    child_json = child.model_dump_json()
    
    # Can cross-validate between parent and child
    restored_parent = ParentRootModel.model_validate_json(child_json)
    restored_child = ChildRootModel.model_validate_json(parent_json)
    
    assert restored_parent.root == data
    assert restored_child.root == data


# Test 2: RootModel with BaseModel as root type
class InnerModel(BaseModel):
    value: int
    name: str


class BaseModelRootModel(RootModel[InnerModel]):
    pass


@given(st.integers(), st.text(min_size=1, max_size=10))
def test_basemodel_as_root(value, name):
    """Test RootModel with BaseModel as the root type"""
    
    # Create via dict
    model1 = BaseModelRootModel({'value': value, 'name': name})
    assert model1.root.value == value
    assert model1.root.name == name
    
    # Create via BaseModel instance
    inner = InnerModel(value=value, name=name)
    model2 = BaseModelRootModel(inner)
    assert model2.root == inner
    
    # JSON round-trip
    json_str = model1.model_dump_json()
    restored = BaseModelRootModel.model_validate_json(json_str)
    assert restored.root.value == value
    assert restored.root.name == name
    
    # model_dump should return dict when root is BaseModel
    dumped = model1.model_dump()
    assert isinstance(dumped, dict)
    assert dumped == {'value': value, 'name': name}


# Test 3: RootModel with Optional types
class OptionalRootModel(RootModel[Optional[List[int]]]):
    pass


@given(st.one_of(st.none(), st.lists(st.integers(), max_size=10)))
def test_optional_root_type(data):
    """Test RootModel with Optional root type"""
    
    model = OptionalRootModel(data)
    assert model.root == data
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = OptionalRootModel.model_validate_json(json_str)
    assert restored.root == data
    
    # None should serialize as null
    if data is None:
        assert json_str == 'null'


# Test 4: Multiple levels of RootModel nesting
class Level1RootModel(RootModel[List[int]]):
    pass


class Level2RootModel(RootModel[Level1RootModel]):
    pass


@given(st.lists(st.integers(), max_size=10))
def test_nested_rootmodels(data):
    """Test RootModel containing another RootModel"""
    
    level1 = Level1RootModel(data)
    
    # This should work - creating Level2 with Level1 instance
    level2 = Level2RootModel(level1)
    assert isinstance(level2.root, Level1RootModel)
    assert level2.root.root == data
    
    # Can also create from raw data
    level2_direct = Level2RootModel(data)
    assert isinstance(level2_direct.root, Level1RootModel)
    assert level2_direct.root.root == data


# Test 5: RootModel with Union types
class UnionRootModel(RootModel[Union[int, str, List[int]]]):
    pass


@given(
    st.one_of(
        st.integers(),
        st.text(min_size=1, max_size=10),
        st.lists(st.integers(), max_size=5)
    )
)
def test_union_root_type(data):
    """Test RootModel with Union root type"""
    
    model = UnionRootModel(data)
    assert model.root == data
    
    # Type should be preserved
    assert type(model.root) == type(data)
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = UnionRootModel.model_validate_json(json_str)
    
    # Check type preservation through JSON
    if isinstance(data, list):
        assert isinstance(restored.root, list)
        assert restored.root == data
    elif isinstance(data, str):
        assert isinstance(restored.root, str)
        assert restored.root == data
    else:  # int
        assert isinstance(restored.root, int)
        assert restored.root == data


# Test 6: RootModel equality with type mismatch
@given(st.integers(), st.text(min_size=1, max_size=10))
def test_equality_type_mismatch(int_val, str_val):
    """Test equality between RootModels with different generic types"""
    
    class IntRootModel(RootModel[int]):
        pass
    
    class StrRootModel(RootModel[str]):
        pass
    
    int_model = IntRootModel(int_val)
    str_model = StrRootModel(str_val)
    
    # Different types should not be equal even if __eq__ is called
    assert int_model != str_model
    assert not (int_model == str_model)


# Test 7: model_construct with _fields_set edge cases
@given(
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=5),
    st.sets(st.sampled_from(['root', 'other', 'invalid']))
)
def test_model_construct_fields_set(data, fields_set):
    """Test model_construct with various _fields_set values"""
    
    class TestModel(RootModel[Dict[str, int]]):
        pass
    
    # model_construct should accept any fields_set
    model = TestModel.model_construct(data, _fields_set=fields_set)
    assert model.root == data
    
    # Only 'root' should be preserved in fields_set
    if 'root' in fields_set:
        assert 'root' in model.__pydantic_fields_set__
    
    # Other fields should be ignored (RootModel only has 'root')
    assert model.__pydantic_fields_set__ <= {'root'}


# Test 8: Mutation detection after creation
@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_mutation_detection(data):
    """Test if mutations to root are reflected in the model"""
    
    class MutableListModel(RootModel[List[int]]):
        pass
    
    model = MutableListModel(data.copy())
    original_root = model.root
    original_len = len(model.root)
    
    # Mutate the root directly
    model.root.append(999)
    
    # The mutation should be reflected
    assert len(model.root) == original_len + 1
    assert model.root[-1] == 999
    assert model.root is original_root  # Same object
    
    # JSON serialization should include the mutation
    json_str = model.model_dump_json()
    restored = MutableListModel.model_validate_json(json_str)
    assert 999 in restored.root


# Test 9: RootModel with custom validation
class ValidatedRootModel(RootModel[List[int]]):
    def model_validate(cls, obj):
        # This override should not break anything
        return super().model_validate(obj)


@given(st.lists(st.integers(), max_size=10))
def test_custom_validation(data):
    """Test RootModel with custom validation method"""
    
    model = ValidatedRootModel(data)
    assert model.root == data
    
    # Validation should still work
    validated = ValidatedRootModel.model_validate(data)
    assert validated.root == data


# Test 10: RootModel with extreme nesting depth
def create_deeply_nested_data(depth, value=1):
    """Create deeply nested dict structure"""
    if depth == 0:
        return value
    return {'nested': create_deeply_nested_data(depth - 1, value)}


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=20)  # Reduce for performance
def test_deep_nesting(value):
    """Test RootModel with deeply nested structures"""
    
    class DeepModel(RootModel[Any]):
        pass
    
    # Create deeply nested structure
    depth = 50  # Fixed reasonable depth
    data = create_deeply_nested_data(depth, value)
    
    model = DeepModel(data)
    
    # JSON round-trip should handle deep nesting
    json_str = model.model_dump_json()
    restored = DeepModel.model_validate_json(json_str)
    
    # Verify the deepest value
    current = restored.root
    for _ in range(depth):
        current = current['nested']
    assert current == value


# Test 11: RootModel with recursive types
@given(st.integers(min_value=-100, max_value=100))
def test_recursive_structure(value):
    """Test RootModel with self-referential structures"""
    
    class RecursiveModel(RootModel[Dict[str, Any]]):
        pass
    
    # Create self-referential structure (be careful!)
    data = {'value': value, 'children': []}
    # Add a child that references similar structure
    data['children'].append({'value': value + 1, 'children': []})
    
    model = RecursiveModel(data)
    assert model.root['value'] == value
    assert len(model.root['children']) == 1
    assert model.root['children'][0]['value'] == value + 1


# Test 12: RootModel __repr__ with various data types
@given(
    st.one_of(
        st.integers(),
        st.text(max_size=50),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=3)
    )
)
def test_repr_output(data):
    """Test __repr__ output format"""
    
    class ReprModel(RootModel[Any]):
        pass
    
    model = ReprModel(data)
    repr_str = repr(model)
    
    # __repr__ should contain 'root=' prefix
    assert 'root=' in repr_str
    
    # The data should be represented in the repr
    assert str(data) in repr_str or repr(data) in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])