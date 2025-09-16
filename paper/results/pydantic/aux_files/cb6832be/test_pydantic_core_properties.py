import json
import math
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st, settings, assume, note, example
import pydantic
from pydantic import BaseModel, Field, ValidationError


# Core property: model_validate(model_dump()) should equal original for valid models
@given(
    int_val=st.integers(),
    str_val=st.text(max_size=100),
    list_val=st.lists(st.integers(), max_size=10),
    dict_val=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
)
def test_dump_validate_roundtrip(int_val, str_val, list_val, dict_val):
    """Core property: model_validate(model_dump()) = original"""
    
    class Model(BaseModel):
        a: int
        b: str
        c: List[int]
        d: Dict[str, int]
    
    m = Model(a=int_val, b=str_val, c=list_val, d=dict_val)
    
    # Dump and validate should round-trip
    dumped = m.model_dump()
    m2 = Model.model_validate(dumped)
    
    assert m == m2
    assert m.model_dump() == m2.model_dump()


# Test model_dump_json mode parameter behavior
@given(
    value=st.text(max_size=50),
    mode=st.sampled_from(['json', 'python'])
)
def test_dump_mode_parameter(value, mode):
    """Test that model_dump with mode parameter works correctly"""
    
    class Model(BaseModel):
        text: str
    
    m = Model(text=value)
    
    # Both modes should produce valid output
    if mode == 'json':
        dumped = m.model_dump(mode='json')
        # JSON mode should produce JSON-serializable output
        json.dumps(dumped)  # Should not raise
    else:
        dumped = m.model_dump(mode='python')
    
    # Should be able to reconstruct
    m2 = Model.model_validate(dumped)
    assert m.text == m2.text


# Test that model equality is properly defined
@given(
    val1=st.integers(),
    val2=st.integers(),
    val3=st.text(max_size=50)
)
def test_model_equality(val1, val2, val3):
    """Test model equality behavior"""
    
    class Model(BaseModel):
        x: int
        y: str
    
    m1 = Model(x=val1, y=val3)
    m2 = Model(x=val1, y=val3)
    m3 = Model(x=val2, y=val3)
    
    # Same values should be equal
    assert m1 == m2
    
    # Different values should not be equal
    if val1 != val2:
        assert m1 != m3
    
    # JSON round-trip should preserve equality
    m1_restored = Model.model_validate_json(m1.model_dump_json())
    assert m1 == m1_restored


# Test exclude_unset behavior
@given(
    provide_optional=st.booleans(),
    optional_value=st.one_of(st.none(), st.integers())
)
def test_exclude_unset_behavior(provide_optional, optional_value):
    """Test that exclude_unset works as documented"""
    
    class Model(BaseModel):
        required: int
        optional: Optional[int] = None
    
    if provide_optional:
        m = Model(required=1, optional=optional_value)
        dumped = m.model_dump(exclude_unset=True)
        # Should include optional since it was explicitly set
        assert 'optional' in dumped
        assert dumped['optional'] == optional_value
    else:
        m = Model(required=1)
        dumped = m.model_dump(exclude_unset=True)
        # Should not include optional since it wasn't set
        assert 'optional' not in dumped
    
    # Regular dump should always include all fields
    regular_dump = m.model_dump(exclude_unset=False)
    assert 'required' in regular_dump
    assert 'optional' in regular_dump


# Test model_copy deep copy behavior
@given(
    values=st.lists(st.integers(), min_size=1, max_size=5)
)
def test_model_copy_deep(values):
    """Test that model_copy with deep=True creates independent copies"""
    
    class Model(BaseModel):
        items: List[int]
    
    m1 = Model(items=values.copy())
    
    # Shallow copy - should share references
    m2 = m1.model_copy(deep=False)
    assert m2.items is m1.items  # Same object
    
    # Deep copy - should be independent
    m3 = m1.model_copy(deep=True)
    assert m3.items is not m1.items  # Different object
    assert m3.items == m1.items  # But same values
    
    # Modifying deep copy shouldn't affect original
    if len(m3.items) > 0:
        m3.items[0] = m3.items[0] + 1000
        assert m3.items != m1.items


# Test JSON encoder with custom types
@given(
    dt=st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1))
)
def test_datetime_json_encoding(dt):
    """Test that datetime fields are properly JSON encoded"""
    
    class Model(BaseModel):
        timestamp: datetime
    
    m = Model(timestamp=dt)
    
    # Should be able to JSON encode
    json_str = m.model_dump_json()
    
    # Should be ISO format string in JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed['timestamp'], str)
    
    # Should round-trip correctly
    m2 = Model.model_validate_json(json_str)
    
    # Datetimes should be equal (might lose microsecond precision)
    if dt.microsecond == 0:
        assert m2.timestamp == dt
    else:
        # Check they're close enough (within 1 second)
        diff = abs((m2.timestamp - dt).total_seconds())
        assert diff < 1


# Test field serialization with aliases in by_alias mode
@given(
    value=st.integers(),
    by_alias=st.booleans()
)
def test_alias_serialization_modes(value, by_alias):
    """Test that by_alias parameter works correctly in serialization"""
    
    class Model(BaseModel):
        model_config = pydantic.ConfigDict(populate_by_name=True)
        internal: int = Field(alias='external')
    
    m = Model(external=value)
    
    dumped = m.model_dump(by_alias=by_alias)
    
    if by_alias:
        assert 'external' in dumped
        assert dumped['external'] == value
        assert 'internal' not in dumped
    else:
        assert 'internal' in dumped
        assert dumped['internal'] == value
        assert 'external' not in dumped


# Test that validators are called in the right order
@given(
    value=st.integers(min_value=-100, max_value=100)
)
def test_validator_execution_order(value):
    """Test that field validators execute in the expected order"""
    
    calls = []
    
    class Model(BaseModel):
        value: int
        
        @pydantic.field_validator('value', mode='before')
        @classmethod
        def before_validator(cls, v):
            calls.append('before')
            return v
        
        @pydantic.field_validator('value', mode='after')
        @classmethod
        def after_validator(cls, v):
            calls.append('after')
            return v
    
    calls.clear()
    m = Model(value=value)
    
    # Validators should have been called in order
    assert calls == ['before', 'after']
    assert m.value == value


# Test exclude_none behavior
@given(
    include_none=st.booleans(),
    none_value=st.one_of(st.none(), st.integers())
)
def test_exclude_none_serialization(include_none, none_value):
    """Test exclude_none in model_dump"""
    
    class Model(BaseModel):
        always: int = 1
        maybe_none: Optional[int] = None
    
    m = Model(always=1, maybe_none=none_value)
    
    dumped = m.model_dump(exclude_none=True)
    
    assert 'always' in dumped
    
    if none_value is None:
        # Should be excluded when None
        assert 'maybe_none' not in dumped
    else:
        # Should be included when not None
        assert 'maybe_none' in dumped
        assert dumped['maybe_none'] == none_value


# Test model_validate with strict mode
@given(
    int_as_str=st.booleans()
)
def test_strict_mode_validation(int_as_str):
    """Test strict mode in model_validate"""
    
    class Model(BaseModel):
        value: int
    
    if int_as_str:
        # String that looks like int
        data = {'value': '123'}
        
        # Non-strict should coerce
        m1 = Model.model_validate(data, strict=False)
        assert m1.value == 123
        
        # Strict should fail
        with pytest.raises(ValidationError):
            Model.model_validate(data, strict=True)
    else:
        # Actual int
        data = {'value': 123}
        
        # Both should work
        m1 = Model.model_validate(data, strict=False)
        m2 = Model.model_validate(data, strict=True)
        assert m1.value == 123
        assert m2.value == 123


# Test JSON schema generation
@given(
    default_val=st.one_of(st.none(), st.integers())
)
def test_json_schema_generation(default_val):
    """Test that JSON schema generation works correctly"""
    
    class Model(BaseModel):
        required_field: int
        optional_field: Optional[int] = default_val
    
    schema = Model.model_json_schema()
    
    # Should have proper structure
    assert 'properties' in schema
    assert 'required_field' in schema['properties']
    assert 'optional_field' in schema['properties']
    
    # Required field should be in required list
    assert 'required' in schema
    assert 'required_field' in schema['required']
    
    # Optional field should not be required
    if default_val is None:
        # When default is None, field is optional
        assert 'optional_field' not in schema.get('required', [])


if __name__ == "__main__":
    print("Running core property tests...")
    test_dump_validate_roundtrip(1, "test", [1, 2], {"a": 1})
    test_model_equality(1, 2, "test")
    print("Basic tests passed!")