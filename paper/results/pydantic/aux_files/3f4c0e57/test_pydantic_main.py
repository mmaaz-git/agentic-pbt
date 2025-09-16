import json
import math
from typing import Optional, List, Dict, Any
from hypothesis import given, strategies as st, assume, settings
from pydantic import BaseModel, create_model, ValidationError
import pytest


# Strategy for valid field names in Python
field_name_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_',
    min_size=1,
    max_size=20
).filter(lambda x: x.isidentifier() and not x.startswith('__'))

# Strategy for simple JSON-serializable values
json_value_strategy = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e10, max_value=1e10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(max_size=100)
)

# Strategy for creating dynamic model definitions
model_fields_strategy = st.dictionaries(
    field_name_strategy,
    st.tuples(
        st.sampled_from([int, str, bool, float, type(None)]),
        json_value_strategy
    ),
    min_size=1,
    max_size=5
)


@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=150),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.one_of(st.none(), st.text(max_size=50))
)
def test_basemodel_json_roundtrip(name, age, active, score, optional):
    """Test that JSON serialization and deserialization is a round-trip."""
    
    class TestModel(BaseModel):
        name: str
        age: int
        active: bool
        score: float
        optional: Optional[str] = None
    
    # Create model instance
    model = TestModel(name=name, age=age, active=active, score=score, optional=optional)
    
    # Test JSON round-trip
    json_str = model.model_dump_json()
    reconstructed = TestModel.model_validate_json(json_str)
    
    assert model == reconstructed
    assert model.model_dump() == reconstructed.model_dump()


@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=-1000000, max_value=1000000),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=5)
)
def test_basemodel_dict_roundtrip(text_field, int_field, list_field, dict_field):
    """Test that dict dump and model_validate is a round-trip."""
    
    class ComplexModel(BaseModel):
        text: str
        number: int
        items: List[int]
        mapping: Dict[str, int]
    
    model = ComplexModel(
        text=text_field,
        number=int_field,
        items=list_field,
        mapping=dict_field
    )
    
    # Test dict round-trip
    dumped = model.model_dump()
    reconstructed = ComplexModel.model_validate(dumped)
    
    assert model == reconstructed
    assert model.model_dump() == reconstructed.model_dump()


@given(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.booleans()
)
def test_model_copy_equality(field1, field2, field3):
    """Test that model_copy creates equal but distinct objects."""
    
    class CopyTestModel(BaseModel):
        field1: str
        field2: int
        field3: bool
    
    original = CopyTestModel(field1=field1, field2=field2, field3=field3)
    copied = original.model_copy()
    
    # Should be equal but different objects
    assert original == copied
    assert original is not copied
    assert original.model_dump() == copied.model_dump()


@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=-1000, max_value=1000),
    st.text(min_size=1, max_size=100),
    st.integers(min_value=-1000, max_value=1000)
)
def test_model_copy_update(original_str, original_int, updated_str, updated_int):
    """Test that model_copy with update correctly updates fields."""
    
    class UpdateTestModel(BaseModel):
        string_field: str
        int_field: int
    
    original = UpdateTestModel(string_field=original_str, int_field=original_int)
    
    # Test partial update
    updated1 = original.model_copy(update={'string_field': updated_str})
    assert updated1.string_field == updated_str
    assert updated1.int_field == original_int
    
    # Test full update
    updated2 = original.model_copy(update={'string_field': updated_str, 'int_field': updated_int})
    assert updated2.string_field == updated_str
    assert updated2.int_field == updated_int
    
    # Original should be unchanged
    assert original.string_field == original_str
    assert original.int_field == original_int


@given(
    st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
    field_name_strategy,
    st.integers(min_value=-1000, max_value=1000),
    st.text(max_size=50)
)
def test_create_model_field_preservation(model_name, field1_name, field1_default, field2_default):
    """Test that create_model correctly preserves field definitions."""
    assume(field1_name != 'model_config')
    assume(field1_name != 'model_fields')
    
    # Create dynamic model
    DynamicModel = create_model(
        model_name,
        **{
            field1_name: (int, field1_default),
            'field2': (str, field2_default)
        }
    )
    
    # Test with default values
    instance1 = DynamicModel()
    assert getattr(instance1, field1_name) == field1_default
    assert instance1.field2 == field2_default
    
    # Test with custom values
    custom_int = 999
    custom_str = "custom"
    instance2 = DynamicModel(**{field1_name: custom_int, 'field2': custom_str})
    assert getattr(instance2, field1_name) == custom_int
    assert instance2.field2 == custom_str
    
    # Test that model_fields contains the expected fields
    assert field1_name in DynamicModel.model_fields
    assert 'field2' in DynamicModel.model_fields


@given(
    st.lists(
        st.tuples(
            field_name_strategy,
            st.sampled_from([int, str, bool, float]),
            json_value_strategy
        ),
        min_size=1,
        max_size=5
    ).filter(lambda lst: len(set(t[0] for t in lst)) == len(lst))  # Ensure unique field names
)
def test_create_model_roundtrip(field_definitions):
    """Test that dynamically created models support serialization round-trips."""
    
    # Build field dict for create_model
    fields = {}
    values = {}
    for field_name, field_type, default_value in field_definitions:
        if field_type == float and default_value is not None:
            # Ensure float defaults are actually floats
            try:
                default_value = float(default_value)
            except (TypeError, ValueError):
                default_value = 0.0
        
        # Ensure type compatibility
        if default_value is not None:
            if field_type == int and not isinstance(default_value, (int, bool)):
                default_value = 0
            elif field_type == str and not isinstance(default_value, str):
                default_value = str(default_value)
            elif field_type == bool and not isinstance(default_value, bool):
                default_value = bool(default_value)
            elif field_type == float and not isinstance(default_value, (int, float)):
                default_value = 0.0
        
        fields[field_name] = (field_type, default_value)
        values[field_name] = default_value
    
    # Create dynamic model
    DynamicModel = create_model('TestDynamic', **fields)
    
    # Create instance
    instance = DynamicModel()
    
    # Test JSON round-trip
    json_str = instance.model_dump_json()
    reconstructed = DynamicModel.model_validate_json(json_str)
    assert instance == reconstructed
    
    # Test dict round-trip
    dict_data = instance.model_dump()
    reconstructed2 = DynamicModel.model_validate(dict_data)
    assert instance == reconstructed2


@given(
    st.dictionaries(
        field_name_strategy,
        json_value_strategy,
        min_size=1,
        max_size=10
    )
)
def test_model_extra_field_handling(extra_data):
    """Test how models handle extra fields during validation."""
    
    class StrictModel(BaseModel):
        required_field: str = "default"
        
        class Config:
            extra = 'forbid'
    
    class AllowModel(BaseModel):
        required_field: str = "default"
        
        class Config:
            extra = 'allow'
    
    # Test with extra='allow'
    allow_data = {'required_field': 'test', **extra_data}
    allow_instance = AllowModel.model_validate(allow_data)
    assert allow_instance.required_field == 'test'
    
    # Check if extra fields are accessible
    for key, value in extra_data.items():
        if hasattr(allow_instance, key):
            assert getattr(allow_instance, key) == value
    
    # Test with extra='forbid'
    if extra_data:
        with pytest.raises(ValidationError):
            StrictModel.model_validate(allow_data)
    else:
        # Should work if no extra data
        strict_instance = StrictModel.model_validate(allow_data)
        assert strict_instance.required_field == 'test'


@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=1000)
)
def test_model_validate_strings(text_val, int_val, float_val):
    """Test model_validate_strings parses string representations correctly."""
    
    class StringParseModel(BaseModel):
        text: str
        number: int
        decimal: float
    
    # Create string representations
    string_data = {
        'text': text_val,
        'number': str(int_val),
        'decimal': str(float_val)
    }
    
    # Parse with model_validate_strings
    parsed = StringParseModel.model_validate_strings(string_data)
    
    assert parsed.text == text_val
    assert parsed.number == int_val
    assert math.isclose(parsed.decimal, float_val, rel_tol=1e-9, abs_tol=1e-9)
    
    # Verify round-trip through JSON
    json_str = parsed.model_dump_json()
    reconstructed = StringParseModel.model_validate_json(json_str)
    assert parsed == reconstructed