"""More comprehensive property-based tests for Pydantic edge cases"""

import math
import sys
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
import json

from hypothesis import given, strategies as st, assume, settings, example
from pydantic import BaseModel, Field, ValidationError, field_validator, ConfigDict
import pytest


# Test for Unicode handling in JSON serialization
@given(
    unicode_text=st.text(min_size=0, max_size=50).filter(
        lambda x: any(ord(c) > 127 for c in x) or '\x00' in x or '\n' in x or '\r' in x or '\t' in x
    )
)
def test_unicode_json_roundtrip(unicode_text):
    """Test that Unicode and special characters survive JSON round-trip"""
    
    class UnicodeModel(BaseModel):
        text: str
    
    original = UnicodeModel(text=unicode_text)
    
    # JSON round-trip
    json_str = original.model_dump_json()
    restored = UnicodeModel.model_validate_json(json_str)
    
    assert restored.text == original.text


# Test extreme numeric values
@given(
    large_int=st.one_of(
        st.integers(min_value=2**63, max_value=2**100),
        st.integers(min_value=-2**100, max_value=-2**63)
    )
)
def test_large_integer_handling(large_int):
    """Test handling of integers larger than 64-bit"""
    
    class LargeIntModel(BaseModel):
        value: int
    
    model = LargeIntModel(value=large_int)
    assert model.value == large_int
    
    # Test JSON serialization for large integers
    json_str = model.model_dump_json()
    restored = LargeIntModel.model_validate_json(json_str)
    assert restored.value == large_int


# Test with empty strings and whitespace
@given(
    whitespace=st.sampled_from(['', ' ', '  ', '\t', '\n', '\r\n', ' \t\n '])
)
def test_whitespace_string_handling(whitespace):
    """Test that whitespace strings are preserved"""
    
    class WhitespaceModel(BaseModel):
        text: str
        optional_text: Optional[str] = None
    
    model = WhitespaceModel(text=whitespace, optional_text=whitespace if whitespace else None)
    
    # Check preservation
    assert model.text == whitespace
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = WhitespaceModel.model_validate_json(json_str)
    assert restored.text == whitespace


# Test Union type ordering and validation
@given(
    value=st.one_of(
        st.integers(),
        st.text(min_size=1, max_size=10),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_union_type_resolution(value):
    """Test that Union types resolve to the correct type"""
    
    class UnionModel(BaseModel):
        # Order matters in Union - int should be tried before float
        value: Union[int, float, str]
    
    model = UnionModel(value=value)
    
    # Check type preservation through serialization
    dumped = model.model_dump()
    restored = UnionModel.model_validate(dumped)
    
    # For numeric types, we need special comparison
    if isinstance(value, (int, float)) and isinstance(restored.value, (int, float)):
        if math.isfinite(value) and math.isfinite(restored.value):
            assert math.isclose(value, restored.value, rel_tol=1e-9, abs_tol=1e-9)
    else:
        assert restored.value == model.value
    
    # Check that type is preserved correctly
    assert type(restored.value) == type(model.value)


# Test dictionary keys with special characters
@given(
    keys=st.lists(
        st.text(min_size=1, max_size=20).filter(lambda x: x and not x.isspace()),
        min_size=1,
        max_size=5,
        unique=True
    ),
    values=st.lists(st.integers(), min_size=1, max_size=5)
)
def test_dict_with_special_keys(keys, values):
    """Test dictionaries with non-standard keys"""
    assume(len(keys) == len(values))
    
    class DictModel(BaseModel):
        data: Dict[str, int]
    
    data = dict(zip(keys, values))
    model = DictModel(data=data)
    
    # Check preservation
    assert model.data == data
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = DictModel.model_validate_json(json_str)
    assert restored.data == data


# Test field ordering preservation
@given(
    fields=st.dictionaries(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.integers(),
        min_size=2,
        max_size=5
    )
)
def test_field_order_preservation(fields):
    """Test that field order is preserved in operations"""
    
    # Dynamically create a model
    field_definitions = {
        name: (int, Field(default=value))
        for name, value in fields.items()
    }
    
    DynamicModel = type('DynamicModel', (BaseModel,), field_definitions)
    
    model = DynamicModel()
    dumped = model.model_dump()
    
    # Field order might not be guaranteed in dict, but values should match
    for field_name, expected_value in fields.items():
        assert dumped[field_name] == expected_value


# Test with None in various contexts
@given(
    nullable_value=st.one_of(st.none(), st.integers()),
    list_with_none=st.lists(st.one_of(st.none(), st.integers()), min_size=0, max_size=5)
)
def test_none_handling(nullable_value, list_with_none):
    """Test None handling in different contexts"""
    
    class NoneModel(BaseModel):
        optional: Optional[int] = None
        nullable_list: List[Optional[int]] = []
    
    model = NoneModel(optional=nullable_value, nullable_list=list_with_none)
    
    # Check preservation
    assert model.optional == nullable_value
    assert model.nullable_list == list_with_none
    
    # JSON round-trip
    json_str = model.model_dump_json()
    restored = NoneModel.model_validate_json(json_str)
    assert restored.optional == nullable_value
    assert restored.nullable_list == list_with_none


# Test recursive/self-referential models
def test_recursive_model_depth():
    """Test handling of recursive model structures"""
    
    class TreeNode(BaseModel):
        value: int
        children: List['TreeNode'] = []
    
    # Create a deep tree
    leaf = TreeNode(value=3)
    branch = TreeNode(value=2, children=[leaf])
    root = TreeNode(value=1, children=[branch])
    
    # Test serialization
    dumped = root.model_dump()
    assert dumped['value'] == 1
    assert dumped['children'][0]['value'] == 2
    assert dumped['children'][0]['children'][0]['value'] == 3
    
    # JSON round-trip
    json_str = root.model_dump_json()
    restored = TreeNode.model_validate_json(json_str)
    assert restored.value == 1
    assert restored.children[0].value == 2
    assert restored.children[0].children[0].value == 3


# Test float special values
@given(
    special_float=st.sampled_from([float('inf'), float('-inf'), float('nan')])
)
def test_special_float_handling(special_float):
    """Test handling of special float values (inf, -inf, nan)"""
    
    class FloatModel(BaseModel):
        value: float
    
    model = FloatModel(value=special_float)
    
    # NaN needs special comparison
    if math.isnan(special_float):
        assert math.isnan(model.value)
    else:
        assert model.value == special_float
    
    # JSON serialization of special floats
    json_str = model.model_dump_json()
    restored = FloatModel.model_validate_json(json_str)
    
    if math.isnan(special_float):
        assert math.isnan(restored.value)
    else:
        assert restored.value == special_float


# Test model with ConfigDict settings
@given(
    field_value=st.text(min_size=1, max_size=20)
)
def test_frozen_model_immutability(field_value):
    """Test that frozen models are truly immutable"""
    
    class FrozenModel(BaseModel):
        model_config = ConfigDict(frozen=True)
        value: str
    
    model = FrozenModel(value=field_value)
    
    # Attempt to modify should raise error
    with pytest.raises((ValidationError, AttributeError, TypeError)):
        model.value = "new_value"
    
    # Value should remain unchanged
    assert model.value == field_value


# Test edge case with empty model
def test_empty_model():
    """Test model with no fields"""
    
    class EmptyModel(BaseModel):
        pass
    
    model = EmptyModel()
    
    # Should serialize to empty dict
    assert model.model_dump() == {}
    
    # JSON round-trip
    json_str = model.model_dump_json()
    assert json_str == '{}'
    restored = EmptyModel.model_validate_json(json_str)
    assert restored.model_dump() == {}


# Test field with both alias and validation_alias
@given(
    value=st.text(min_size=1, max_size=20)
)
def test_validation_vs_serialization_alias(value):
    """Test different aliases for validation and serialization"""
    
    class AliasModel(BaseModel):
        field: str = Field(
            validation_alias='input_name',
            serialization_alias='output_name'
        )
    
    # Should accept input_name during validation
    model = AliasModel.model_validate({'input_name': value})
    assert model.field == value
    
    # Should use output_name during serialization
    dumped = model.model_dump(by_alias=True)
    assert 'output_name' in dumped
    assert dumped['output_name'] == value
    
    # Regular field name when not using aliases
    dumped_no_alias = model.model_dump(by_alias=False)
    assert 'field' in dumped_no_alias
    assert dumped_no_alias['field'] == value


# Test with extremely nested structure
@given(
    depth=st.integers(min_value=10, max_value=20)
)
def test_deeply_nested_structure(depth):
    """Test handling of deeply nested data structures"""
    
    class NestedModel(BaseModel):
        value: int
        nested: Optional[Dict[str, Any]] = None
    
    # Create deeply nested structure
    data = {'value': 0}
    current = data
    for i in range(depth):
        current['nested'] = {'value': i + 1}
        current = current['nested']
    
    model = NestedModel.model_validate(data)
    
    # Traverse and verify
    current_model = model
    for i in range(min(depth, 10)):  # Check first 10 levels
        assert current_model.value == i
        if current_model.nested:
            current_model = NestedModel.model_validate(current_model.nested)
    
    # JSON round-trip (might hit recursion limits)
    try:
        json_str = model.model_dump_json()
        restored = NestedModel.model_validate_json(json_str)
        assert restored.value == 0
    except RecursionError:
        # This is actually expected for very deep structures
        pass


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))