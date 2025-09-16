import json
import math
import sys
from typing import Optional, List, Dict, Any, Union, Literal
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from hypothesis import given, strategies as st, settings, assume, note
import pydantic
from pydantic import BaseModel, Field, ValidationError, field_validator


# Test for very large numbers and precision
@given(
    large_int=st.integers(min_value=2**53, max_value=2**63-1)
)
def test_large_integer_json_precision(large_int):
    """Test that large integers maintain precision through JSON round-trip"""
    
    class Model(BaseModel):
        value: int
    
    m = Model(value=large_int)
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    # Large integers should maintain exact value
    assert m.value == m2.value
    assert m.value == large_int


# Test field defaults with mutable types
def test_mutable_default_field():
    """Test that mutable default values don't share state between instances"""
    
    class Model(BaseModel):
        items: List[int] = Field(default_factory=list)
    
    m1 = Model()
    m2 = Model()
    
    m1.items.append(1)
    assert m1.items == [1]
    assert m2.items == []  # Should not be affected
    
    # Test JSON round-trip preserves independence
    json1 = m1.model_dump_json()
    json2 = m2.model_dump_json()
    
    m1_restored = Model.model_validate_json(json1)
    m2_restored = Model.model_validate_json(json2)
    
    assert m1_restored.items == [1]
    assert m2_restored.items == []


# Test with None in different contexts
@given(
    value=st.one_of(st.none(), st.text(max_size=10)),
    use_optional=st.booleans()
)
def test_none_handling(value, use_optional):
    """Test None handling in various contexts"""
    
    if use_optional:
        class Model(BaseModel):
            field: Optional[str] = None
    else:
        class Model(BaseModel):
            field: Union[str, None] = None
    
    m = Model(field=value)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    assert m.field == m2.field
    
    # Check JSON representation
    parsed = json.loads(json_str)
    if value is None:
        assert parsed['field'] is None
    else:
        assert parsed['field'] == value


# Test subclass relationships
def test_model_subclass_json():
    """Test that model subclasses handle JSON correctly"""
    
    class BaseModel1(BaseModel):
        base_field: int
    
    class SubModel(BaseModel1):
        sub_field: str
    
    m = SubModel(base_field=42, sub_field="test")
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = SubModel.model_validate_json(json_str)
    
    assert m.base_field == m2.base_field
    assert m.sub_field == m2.sub_field
    
    # Verify all fields are present
    data = json.loads(json_str)
    assert 'base_field' in data
    assert 'sub_field' in data


# Test with property decorators
def test_property_fields():
    """Test models with @property fields"""
    
    class Model(BaseModel):
        _value: int = Field(alias='value')
        
        @property
        def doubled(self) -> int:
            return self._value * 2
    
    m = Model(value=21)
    assert m.doubled == 42
    
    # Properties shouldn't appear in serialization
    dumped = m.model_dump()
    assert 'doubled' not in dumped
    assert '_value' in dumped
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    assert m2.doubled == 42


# Test frozen models
@given(
    value=st.integers()
)
def test_frozen_model_immutability(value):
    """Test that frozen models are truly immutable"""
    
    class FrozenModel(BaseModel):
        model_config = pydantic.ConfigDict(frozen=True)
        value: int
    
    m = FrozenModel(value=value)
    
    # Should not be able to modify
    with pytest.raises(ValidationError):
        m.value = value + 1
    
    # JSON round-trip should preserve value
    json_str = m.model_dump_json()
    m2 = FrozenModel.model_validate_json(json_str)
    assert m.value == m2.value
    
    # Hash should be consistent
    assert hash(m) == hash(m)
    if m == m2:
        assert hash(m) == hash(m2)


# Test extra fields handling
@given(
    defined_value=st.integers(),
    extra_key=st.text(min_size=1, max_size=10),
    extra_value=st.integers()
)
def test_extra_fields_handling(defined_value, extra_key, extra_value):
    """Test how extra fields are handled in different configurations"""
    assume(extra_key != 'defined_field')  # Avoid collision with defined field
    
    class AllowModel(BaseModel):
        model_config = pydantic.ConfigDict(extra='allow')
        defined_field: int
    
    # Create with extra field
    data = {'defined_field': defined_value, extra_key: extra_value}
    m = AllowModel(**data)
    
    assert m.defined_field == defined_value
    assert getattr(m, extra_key, None) == extra_value
    
    # JSON round-trip should preserve extra fields
    json_str = m.model_dump_json()
    m2 = AllowModel.model_validate_json(json_str)
    
    assert m2.defined_field == defined_value
    assert getattr(m2, extra_key, None) == extra_value


# Test validation with complex conditions
@given(
    values=st.lists(st.integers(), min_size=1, max_size=10)
)
def test_list_validation_consistency(values):
    """Test that list validation is consistent"""
    
    class Model(BaseModel):
        values: List[int]
        
        @field_validator('values')
        @classmethod
        def check_non_empty(cls, v):
            if not v:
                raise ValueError('List cannot be empty')
            return v
    
    # Should succeed with non-empty list
    m = Model(values=values)
    assert m.values == values
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    assert m2.values == values
    
    # Empty list should fail
    with pytest.raises(ValidationError):
        Model(values=[])


# Test Union type ordering
@given(
    value=st.one_of(
        st.integers(),
        st.text(max_size=10),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_union_type_resolution(value):
    """Test that Union types resolve correctly"""
    
    # Order matters in Union - int before float
    class Model(BaseModel):
        value: Union[int, float, str]
    
    m = Model(value=value)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    # Type should be preserved correctly
    if isinstance(value, bool):
        # bool is subclass of int in Python
        assert m2.value == value
    elif isinstance(value, int):
        assert isinstance(m2.value, int)
        assert m2.value == value
    elif isinstance(value, float):
        assert isinstance(m2.value, (int, float))  # Might be coerced
        assert m2.value == value or abs(m2.value - value) < 1e-10
    else:
        assert isinstance(m2.value, str)
        assert m2.value == value


# Test timezone-aware datetime
@given(
    year=st.integers(min_value=2000, max_value=2030),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28)
)
def test_timezone_aware_datetime(year, month, day):
    """Test timezone-aware datetime handling"""
    
    class Model(BaseModel):
        dt: datetime
    
    # Create timezone-aware datetime
    dt = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
    m = Model(dt=dt)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    assert m2.dt == dt
    assert m2.dt.tzinfo is not None


# Test Decimal field handling
@given(
    value=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_decimal_json_serialization(value):
    """Test Decimal field JSON serialization"""
    
    class Model(BaseModel):
        value: Decimal
    
    m = Model(value=value)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    
    # Parse JSON to check representation
    parsed = json.loads(json_str)
    
    # Reconstruct
    m2 = Model.model_validate_json(json_str)
    
    # Decimal should be preserved with full precision
    assert m2.value == value


# Test model with __slots__
def test_model_with_slots():
    """Test model behavior with __slots__ defined"""
    
    class SlottedModel(BaseModel):
        __slots__ = ('_internal',)
        value: int
        
        def __init__(self, **data):
            super().__init__(**data)
            self._internal = 'internal'
    
    m = SlottedModel(value=42)
    assert m.value == 42
    assert m._internal == 'internal'
    
    # JSON round-trip (internal state not preserved)
    json_str = m.model_dump_json()
    m2 = SlottedModel.model_validate_json(json_str)
    assert m2.value == 42


if __name__ == "__main__":
    print("Running special case tests...")
    test_mutable_default_field()
    test_model_subclass_json()
    test_property_fields()
    test_model_with_slots()
    print("Basic tests passed!")