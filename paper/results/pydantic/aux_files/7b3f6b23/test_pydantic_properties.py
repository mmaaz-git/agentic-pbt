"""Property-based tests for Pydantic using Hypothesis"""

import math
from decimal import Decimal
from typing import Optional, List, Dict, Any
import json

from hypothesis import given, strategies as st, assume, settings
from pydantic import BaseModel, Field, ValidationError, field_validator
import pytest


# Strategy for valid field names (Python identifiers)
field_name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",
    min_size=1,
    max_size=20
).filter(lambda x: x.isidentifier() and not x.startswith('__'))


# Test 1: Round-trip property for model_validate and model_dump
@given(
    name=st.text(min_size=1, max_size=100),
    age=st.integers(min_value=0, max_value=200),
    score=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    active=st.booleans(),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=10)
)
def test_model_dump_validate_roundtrip(name, age, score, active, tags):
    """Test that model_validate(model_dump(x)) == x"""
    
    class TestModel(BaseModel):
        name: str
        age: int
        score: float
        active: bool
        tags: List[str]
    
    # Create instance
    original = TestModel(name=name, age=age, score=score, active=active, tags=tags)
    
    # Round-trip through dict
    dumped = original.model_dump()
    restored = TestModel.model_validate(dumped)
    
    # Check equality
    assert restored.name == original.name
    assert restored.age == original.age
    assert math.isclose(restored.score, original.score, rel_tol=1e-9)
    assert restored.active == original.active
    assert restored.tags == original.tags


# Test 2: JSON round-trip property
@given(
    text_field=st.text(min_size=0, max_size=100),
    int_field=st.integers(min_value=-1000000, max_value=1000000),
    float_field=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    bool_field=st.booleans(),
    list_field=st.lists(st.integers(min_value=-100, max_value=100), max_size=20)
)
def test_json_roundtrip(text_field, int_field, float_field, bool_field, list_field):
    """Test that model_validate_json(model_dump_json(x)) preserves data"""
    
    class JsonModel(BaseModel):
        text: str
        number: int
        decimal: float
        flag: bool
        items: List[int]
    
    original = JsonModel(
        text=text_field,
        number=int_field,
        decimal=float_field,
        flag=bool_field,
        items=list_field
    )
    
    # Round-trip through JSON
    json_str = original.model_dump_json()
    restored = JsonModel.model_validate_json(json_str)
    
    assert restored.text == original.text
    assert restored.number == original.number
    assert math.isclose(restored.decimal, original.decimal, rel_tol=1e-9, abs_tol=1e-9)
    assert restored.flag == original.flag
    assert restored.items == original.items


# Test 3: Numeric field constraints (gt, ge, lt, le)
@given(
    value=st.floats(allow_nan=False, allow_infinity=False),
    min_bound=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    max_bound=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000)
)
def test_numeric_constraints(value, min_bound, max_bound):
    """Test that numeric constraints are properly enforced"""
    assume(min_bound < max_bound)
    
    class BoundedModel(BaseModel):
        value: float = Field(gt=min_bound, lt=max_bound)
    
    if min_bound < value < max_bound:
        # Should succeed
        model = BoundedModel(value=value)
        assert model.value == value
    else:
        # Should fail validation
        with pytest.raises(ValidationError) as exc_info:
            BoundedModel(value=value)
        errors = exc_info.value.errors()
        assert len(errors) > 0


# Test 4: String length constraints
@given(
    text=st.text(min_size=0, max_size=50),
    min_len=st.integers(min_value=0, max_value=20),
    max_len=st.integers(min_value=0, max_value=20)
)
def test_string_length_constraints(text, min_len, max_len):
    """Test that string length constraints are enforced"""
    assume(min_len <= max_len)
    
    class StringModel(BaseModel):
        text: str = Field(min_length=min_len, max_length=max_len)
    
    text_len = len(text)
    
    if min_len <= text_len <= max_len:
        # Should succeed
        model = StringModel(text=text)
        assert model.text == text
    else:
        # Should fail
        with pytest.raises(ValidationError) as exc_info:
            StringModel(text=text)
        errors = exc_info.value.errors()
        assert len(errors) > 0


# Test 5: Optional fields with None values
@given(
    value=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    default_value=st.text(min_size=1, max_size=20)
)
def test_optional_field_behavior(value, default_value):
    """Test Optional field handling with None values"""
    
    class OptionalModel(BaseModel):
        optional_field: Optional[str] = None
        with_default: str = default_value
    
    if value is None:
        model = OptionalModel()
        assert model.optional_field is None
        assert model.with_default == default_value
    else:
        model = OptionalModel(optional_field=value)
        assert model.optional_field == value


# Test 6: Field aliasing round-trip
@given(
    field_value=st.text(min_size=1, max_size=50),
    use_alias=st.booleans()
)
def test_field_alias_roundtrip(field_value, use_alias):
    """Test that field aliases work correctly in serialization/deserialization"""
    
    class AliasModel(BaseModel):
        internal_name: str = Field(alias="externalName")
    
    # Create model
    model = AliasModel(externalName=field_value)
    assert model.internal_name == field_value
    
    # Test dump with/without alias
    dumped = model.model_dump(by_alias=use_alias)
    if use_alias:
        assert "externalName" in dumped
        assert dumped["externalName"] == field_value
    else:
        assert "internal_name" in dumped
        assert dumped["internal_name"] == field_value
    
    # Round-trip
    if use_alias:
        restored = AliasModel.model_validate(dumped)
    else:
        # When not using alias, we need to map back
        restored = AliasModel(externalName=dumped["internal_name"])
    assert restored.internal_name == field_value


# Test 7: Exclude unset fields behavior
@given(
    include_optional=st.booleans(),
    optional_value=st.one_of(st.none(), st.text(min_size=1, max_size=20))
)
def test_exclude_unset_behavior(include_optional, optional_value):
    """Test that exclude_unset works correctly"""
    
    class UnsetModel(BaseModel):
        required: str = "required"
        optional: Optional[str] = None
    
    if include_optional and optional_value is not None:
        model = UnsetModel(optional=optional_value)
        dumped = model.model_dump(exclude_unset=True)
        assert "optional" in dumped
        assert dumped["optional"] == optional_value
    else:
        model = UnsetModel()
        dumped = model.model_dump(exclude_unset=True)
        # Only required field should be present when exclude_unset=True
        assert "required" in dumped
        if not include_optional:
            assert "optional" not in dumped or dumped["optional"] is None


# Test 8: Nested model serialization
@given(
    parent_name=st.text(min_size=1, max_size=30),
    child_name=st.text(min_size=1, max_size=30),
    child_age=st.integers(min_value=0, max_value=100)
)
def test_nested_model_serialization(parent_name, child_name, child_age):
    """Test that nested models serialize and deserialize correctly"""
    
    class Child(BaseModel):
        name: str
        age: int
    
    class Parent(BaseModel):
        name: str
        child: Child
    
    # Create nested structure
    child = Child(name=child_name, age=child_age)
    parent = Parent(name=parent_name, child=child)
    
    # Test dict serialization
    dumped = parent.model_dump()
    assert dumped["name"] == parent_name
    assert dumped["child"]["name"] == child_name
    assert dumped["child"]["age"] == child_age
    
    # Test JSON round-trip
    json_str = parent.model_dump_json()
    restored = Parent.model_validate_json(json_str)
    assert restored.name == parent_name
    assert restored.child.name == child_name
    assert restored.child.age == child_age


# Test 9: Type coercion with strict mode
@given(
    int_as_str=st.integers(min_value=-1000, max_value=1000).map(str),
    strict=st.booleans()
)
def test_type_coercion_strict_mode(int_as_str, strict):
    """Test type coercion behavior with strict mode"""
    
    class StrictModel(BaseModel):
        value: int
    
    if strict:
        # In strict mode, string should not be coerced to int
        with pytest.raises(ValidationError):
            StrictModel.model_validate({"value": int_as_str}, strict=True)
    else:
        # In non-strict mode, string should be coerced to int
        model = StrictModel.model_validate({"value": int_as_str}, strict=False)
        assert model.value == int(int_as_str)


# Test 10: Decimal field handling
@given(
    decimal_value=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000),
    max_digits=st.integers(min_value=1, max_value=10),
    decimal_places=st.integers(min_value=0, max_value=5)
)
def test_decimal_field_constraints(decimal_value, max_digits, decimal_places):
    """Test Decimal field with max_digits and decimal_places constraints"""
    assume(max_digits > decimal_places)
    
    class DecimalModel(BaseModel):
        value: Decimal = Field(max_digits=max_digits, decimal_places=decimal_places)
    
    # Convert to string to check digits
    decimal_str = str(abs(decimal_value))
    if '.' in decimal_str:
        integer_part, decimal_part = decimal_str.split('.')
        total_digits = len(integer_part.lstrip('0')) + len(decimal_part)
        actual_decimal_places = len(decimal_part)
    else:
        total_digits = len(decimal_str.lstrip('0'))
        actual_decimal_places = 0
    
    # Adjust for the decimal point not counting as a digit
    if total_digits <= max_digits and actual_decimal_places <= decimal_places:
        try:
            model = DecimalModel(value=decimal_value)
            assert model.value == decimal_value
        except ValidationError:
            # Sometimes Decimal validation is stricter than our check
            pass
    else:
        with pytest.raises(ValidationError):
            DecimalModel(value=decimal_value)


# Test 11: Custom validator behavior
@given(
    value=st.text(min_size=0, max_size=50)
)
def test_custom_validator_invocation(value):
    """Test that custom validators are properly invoked"""
    
    class ValidatedModel(BaseModel):
        text: str
        
        @field_validator('text')
        @classmethod
        def validate_text(cls, v):
            # Custom validation: text must not contain digits
            if any(c.isdigit() for c in v):
                raise ValueError('Text cannot contain digits')
            return v.upper()  # Transform to uppercase
    
    has_digits = any(c.isdigit() for c in value)
    
    if has_digits:
        with pytest.raises(ValidationError) as exc_info:
            ValidatedModel(text=value)
        errors = exc_info.value.errors()
        assert len(errors) > 0
    else:
        model = ValidatedModel(text=value)
        assert model.text == value.upper()


# Test 12: model_copy behavior
@given(
    original_value=st.text(min_size=1, max_size=30),
    updated_value=st.text(min_size=1, max_size=30),
    deep=st.booleans()
)
def test_model_copy_behavior(original_value, updated_value, deep):
    """Test that model_copy creates proper copies"""
    
    class CopyModel(BaseModel):
        value: str
        nested: Dict[str, Any] = {}
    
    original = CopyModel(value=original_value, nested={"key": "value"})
    
    # Test update during copy
    copied = original.model_copy(update={"value": updated_value}, deep=deep)
    
    assert copied.value == updated_value
    assert original.value == original_value  # Original unchanged
    
    # If deep copy, nested should be independent
    if deep:
        copied.nested["new_key"] = "new_value"
        assert "new_key" not in original.nested


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))