import json
import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st, settings, assume
import pydantic
from pydantic import BaseModel, Field, field_validator, ValidationError


# Strategy for generating valid field types
field_types = st.sampled_from([int, str, float, bool, Optional[int], Optional[str], List[int], Dict[str, int]])


# Test 1: JSON round-trip property
@given(
    x=st.integers(),
    y=st.text(min_size=0, max_size=100),
    z=st.floats(allow_nan=False, allow_infinity=False),
    b=st.booleans()
)
def test_json_roundtrip_basic_types(x, y, z, b):
    """Test that JSON serialization/deserialization is a round-trip for basic types"""
    
    class Model(BaseModel):
        int_field: int
        str_field: str
        float_field: float
        bool_field: bool
    
    original = Model(int_field=x, str_field=y, float_field=z, bool_field=b)
    json_str = original.model_dump_json()
    reconstructed = Model.model_validate_json(json_str)
    
    assert original == reconstructed
    assert original.model_dump() == reconstructed.model_dump()


# Test 2: Complex nested structures
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text(min_size=0, max_size=50), st.booleans()),
        min_size=0,
        max_size=5
    )
)
def test_json_roundtrip_nested_dict(data):
    """Test JSON round-trip with nested dictionary structures"""
    
    class Model(BaseModel):
        data: Dict[str, Any]
    
    original = Model(data=data)
    json_str = original.model_dump_json()
    reconstructed = Model.model_validate_json(json_str)
    
    assert original == reconstructed
    assert original.data == reconstructed.data


# Test 3: Optional fields and None handling
@given(
    x=st.one_of(st.none(), st.integers()),
    y=st.one_of(st.none(), st.text(max_size=50)),
    z=st.lists(st.integers(), min_size=0, max_size=5)
)
def test_optional_fields_roundtrip(x, y, z):
    """Test that optional fields correctly handle None values in round-trip"""
    
    class Model(BaseModel):
        opt_int: Optional[int] = None
        opt_str: Optional[str] = None
        list_field: List[int]
    
    original = Model(opt_int=x, opt_str=y, list_field=z)
    
    # Test JSON round-trip
    json_str = original.model_dump_json()
    reconstructed = Model.model_validate_json(json_str)
    assert original == reconstructed
    
    # Test dict round-trip
    dict_data = original.model_dump()
    reconstructed2 = Model.model_validate(dict_data)
    assert original == reconstructed2


# Test 4: Model copy properties
@given(
    x=st.integers(),
    y=st.text(max_size=50),
    update_x=st.integers()
)
def test_model_copy_properties(x, y, update_x):
    """Test that model_copy creates independent copies"""
    
    class Model(BaseModel):
        x: int
        y: str
    
    original = Model(x=x, y=y)
    
    # Test basic copy
    copy1 = original.model_copy()
    assert copy1 == original
    assert copy1 is not original
    
    # Test copy with update
    copy2 = original.model_copy(update={'x': update_x})
    assert copy2.x == update_x
    assert copy2.y == original.y
    assert original.x == x  # Original unchanged


# Test 5: Field aliases and serialization
@given(
    value=st.integers(),
    alias_mode=st.sampled_from(['by_alias', 'by_field_name'])
)
def test_field_alias_consistency(value, alias_mode):
    """Test that field aliases work consistently in serialization"""
    
    class Model(BaseModel):
        internal_name: int = Field(alias='externalName')
    
    # Can create with alias
    m1 = Model(externalName=value)
    assert m1.internal_name == value
    
    # Can create with field name in dict
    m2 = Model.model_validate({'internal_name': value})
    assert m2.internal_name == value
    
    # Serialization respects mode
    if alias_mode == 'by_alias':
        dumped = m1.model_dump(by_alias=True)
        assert 'externalName' in dumped
        assert dumped['externalName'] == value
    else:
        dumped = m1.model_dump(by_alias=False)
        assert 'internal_name' in dumped
        assert dumped['internal_name'] == value


# Test 6: Validation consistency
@given(
    x=st.one_of(
        st.integers(),
        st.text(max_size=10),
        st.floats(allow_nan=False),
        st.booleans()
    )
)
def test_validation_consistency(x):
    """Test that validation is consistent across multiple attempts"""
    
    class StrictModel(BaseModel):
        value: int
    
    # Try to validate the same value multiple times
    results = []
    for _ in range(3):
        try:
            m = StrictModel(value=x)
            results.append(('success', m.value))
        except ValidationError as e:
            results.append(('error', str(e)))
    
    # All attempts should have the same result
    assert all(r == results[0] for r in results)


# Test 7: Special numeric values
@given(
    x=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.decimals(allow_nan=False, allow_infinity=False)
    )
)
def test_numeric_type_coercion_roundtrip(x):
    """Test that numeric type coercion in round-trips maintains value"""
    
    class Model(BaseModel):
        num: float
    
    original = Model(num=x)
    
    # JSON round-trip
    json_str = original.model_dump_json()
    reconstructed = Model.model_validate_json(json_str)
    
    # Values should be approximately equal (accounting for float precision)
    if isinstance(x, (int, Decimal)):
        assert reconstructed.num == float(x)
    else:
        assert abs(reconstructed.num - x) < 1e-10


# Test 8: Unicode and special characters
@given(
    text=st.text(
        alphabet=st.characters(blacklist_categories=('Cs',)),  # All unicode except surrogates
        min_size=0,
        max_size=100
    )
)
def test_unicode_string_roundtrip(text):
    """Test that unicode strings survive JSON round-trip"""
    
    class Model(BaseModel):
        text: str
    
    original = Model(text=text)
    json_str = original.model_dump_json()
    
    # Verify it's valid JSON
    json.loads(json_str)
    
    reconstructed = Model.model_validate_json(json_str)
    assert original.text == reconstructed.text


# Test 9: Empty and edge case collections
@given(
    lst=st.lists(st.integers(), min_size=0, max_size=0),
    dct=st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=0),
    st_set=st.sets(st.integers(), min_size=0, max_size=0)
)
def test_empty_collections_roundtrip(lst, dct, st_set):
    """Test that empty collections are preserved in round-trips"""
    
    from typing import Set
    
    class Model(BaseModel):
        list_field: List[int]
        dict_field: Dict[str, int]
        set_field: Set[int]
    
    original = Model(list_field=lst, dict_field=dct, set_field=st_set)
    
    # JSON round-trip
    json_str = original.model_dump_json()
    reconstructed = Model.model_validate_json(json_str)
    
    assert original.list_field == reconstructed.list_field
    assert original.dict_field == reconstructed.dict_field
    assert original.set_field == reconstructed.set_field


# Test 10: model_construct vs normal construction
@given(
    x=st.integers(min_value=-1000, max_value=1000),
    validate=st.booleans()
)
def test_model_construct_validation(x, validate):
    """Test model_construct with and without validation"""
    
    class Model(BaseModel):
        value: int
        
        @field_validator('value')
        @classmethod
        def value_must_be_positive(cls, v):
            if v < 0:
                raise ValueError('must be positive')
            return v
    
    if validate:
        # With validation, should behave like normal construction
        if x < 0:
            with pytest.raises(ValidationError):
                Model.model_construct(value=x, _validate=True)
        else:
            m = Model.model_construct(value=x, _validate=True)
            assert m.value == x
    else:
        # Without validation, should accept any value
        m = Model.model_construct(value=x, _validate=False)
        assert m.value == x


if __name__ == "__main__":
    # Run a quick test to verify everything works
    test_json_roundtrip_basic_types(1, "test", 1.5, True)
    print("Basic test passed!")