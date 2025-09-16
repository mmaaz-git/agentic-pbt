#!/usr/bin/env python3
"""Property-based tests for pydantic.functional_serializers module."""

import json
from typing import Annotated, Any, List, Set
from hypothesis import given, strategies as st, assume, settings
import pytest
from pydantic import BaseModel, field_serializer, model_serializer, ValidationError
from pydantic.functional_serializers import PlainSerializer, WrapSerializer, SerializeAsAny
from pydantic_core import PydanticUndefined


# Property 1: PlainSerializer transformation consistency
# The serializer function should always be applied during serialization
@given(st.text(), st.text())
def test_plain_serializer_always_transforms(input_value, prefix):
    """PlainSerializer should always apply the transformation function."""
    
    def add_prefix(x):
        return f"{prefix}_{x}"
    
    PrefixedStr = Annotated[str, PlainSerializer(add_prefix)]
    
    class Model(BaseModel):
        value: PrefixedStr
    
    model = Model(value=input_value)
    result = model.model_dump()
    
    # Property: The serialized value should always have the prefix
    assert result['value'] == f"{prefix}_{input_value}"
    
    # Also test JSON serialization
    json_result = json.loads(model.model_dump_json())
    assert json_result['value'] == f"{prefix}_{input_value}"


# Property 2: WrapSerializer receives correct handler
# The handler should produce the standard serialization when called
@given(st.text())
def test_wrap_serializer_handler_produces_standard_serialization(value):
    """WrapSerializer's handler should produce standard serialization."""
    
    handler_results = []
    
    def capture_handler_result(val, handler, info):
        standard = handler(val)
        handler_results.append(standard)
        return f"wrapped_{standard}"
    
    WrappedStr = Annotated[str, WrapSerializer(capture_handler_result)]
    
    class Model(BaseModel):
        field: WrappedStr
    
    model = Model(field=value)
    result = model.model_dump()
    
    # Property: The handler should have been called and returned the original value
    assert len(handler_results) == 1
    assert handler_results[0] == value
    assert result['field'] == f"wrapped_{value}"


# Property 3: when_used='json' only applies to JSON serialization
@given(st.text())
def test_when_used_json_parameter(value):
    """Serializers with when_used='json' should only apply during JSON serialization."""
    
    def json_transform(x):
        return f"json_{x}"
    
    JsonOnlyStr = Annotated[str, PlainSerializer(json_transform, when_used='json')]
    
    class Model(BaseModel):
        field: JsonOnlyStr
    
    model = Model(field=value)
    
    # Property: Python serialization should not apply the transformation
    python_result = model.model_dump()
    assert python_result['field'] == value
    
    # Property: JSON serialization should apply the transformation
    json_result = json.loads(model.model_dump_json())
    assert json_result['field'] == f"json_{value}"


# Property 4: when_used='unless-none' skips None values
@given(st.one_of(st.none(), st.text()))
def test_when_used_unless_none(value):
    """Serializers with when_used='unless-none' should skip None values."""
    
    def transform(x):
        if x is None:
            return "ERROR_SHOULD_NOT_BE_CALLED"
        return f"transformed_{x}"
    
    ConditionalStr = Annotated[str | None, PlainSerializer(transform, when_used='unless-none')]
    
    class Model(BaseModel):
        field: ConditionalStr
    
    model = Model(field=value)
    result = model.model_dump()
    
    if value is None:
        # Property: Serializer should not be called for None
        assert result['field'] is None
    else:
        # Property: Serializer should be called for non-None
        assert result['field'] == f"transformed_{value}"


# Property 5: field_serializer idempotence for sorting
@given(st.lists(st.integers()))
def test_field_serializer_sort_idempotence(numbers):
    """Sorting serializer should be idempotent."""
    
    class Model(BaseModel):
        values: List[int]
        
        @field_serializer('values')
        def sort_values(self, v):
            return sorted(v)
    
    model = Model(values=numbers)
    first_dump = model.model_dump()
    
    # Create a new model from the serialized data
    model2 = Model(values=first_dump['values'])
    second_dump = model2.model_dump()
    
    # Property: Applying the serializer twice should give the same result (idempotence)
    assert first_dump['values'] == second_dump['values']
    assert first_dump['values'] == sorted(numbers)


# Property 6: Multiple PlainSerializers compose correctly
@given(st.integers(), st.integers(min_value=1, max_value=10))
def test_plain_serializer_composition(value, multiplier):
    """Multiple serializers should compose in order."""
    
    def multiply(x):
        return x * multiplier
    
    def add_one(x):
        return x + 1
    
    # Apply two transformations
    TransformedInt = Annotated[int, PlainSerializer(multiply), PlainSerializer(add_one)]
    
    class Model(BaseModel):
        field: TransformedInt
    
    model = Model(field=value)
    result = model.model_dump()
    
    # Property: The transformations should be applied in order
    # First multiply, then add one
    expected = (value * multiplier) + 1
    assert result['field'] == expected


# Property 7: SerializeAsAny preserves subclass fields
@given(st.integers(), st.integers())
def test_serialize_as_any_preserves_subclass_fields(x_val, y_val):
    """SerializeAsAny should serialize all fields from subclasses."""
    
    class Parent(BaseModel):
        x: int
    
    class Child(Parent):
        y: int
    
    # Test with SerializeAsAny
    child = Child(x=x_val, y=y_val)
    
    # Annotate as parent but with SerializeAsAny
    class Container(BaseModel):
        item: SerializeAsAny[Parent]
    
    container = Container(item=child)
    result = container.model_dump()
    
    # Property: Both x and y should be in the serialized output
    assert result['item']['x'] == x_val
    assert result['item']['y'] == y_val


# Property 8: model_serializer replaces entire model serialization
@given(st.integers(), st.integers())
def test_model_serializer_complete_replacement(a, b):
    """model_serializer should completely replace model serialization."""
    
    class Model(BaseModel):
        field_a: int
        field_b: int
        
        @model_serializer
        def custom_serialize(self):
            return {"product": self.field_a * self.field_b}
    
    model = Model(field_a=a, field_b=b)
    result = model.model_dump()
    
    # Property: Original fields should not appear, only custom serialization
    assert 'field_a' not in result
    assert 'field_b' not in result
    assert result == {"product": a * b}


# Property 9: WrapSerializer can modify or pass through
@given(st.integers(), st.booleans())
def test_wrap_serializer_conditional_modification(value, should_modify):
    """WrapSerializer can conditionally modify or pass through values."""
    
    def conditional_wrapper(val, handler, info):
        standard = handler(val)
        if val > 0:
            return standard * 2
        else:
            return standard
    
    ConditionalInt = Annotated[int, WrapSerializer(conditional_wrapper)]
    
    class Model(BaseModel):
        field: ConditionalInt
    
    model = Model(field=value)
    result = model.model_dump()
    
    # Property: Positive values are doubled, others pass through
    if value > 0:
        assert result['field'] == value * 2
    else:
        assert result['field'] == value


# Property 10: field_serializer with multiple fields
@given(st.integers(), st.integers())  
def test_field_serializer_multiple_fields(val1, val2):
    """field_serializer can be applied to multiple fields."""
    
    class Model(BaseModel):
        field1: int
        field2: int
        
        @field_serializer('field1', 'field2')
        def double_values(self, v):
            return v * 2
    
    model = Model(field1=val1, field2=val2)
    result = model.model_dump()
    
    # Property: Both fields should be doubled
    assert result['field1'] == val1 * 2
    assert result['field2'] == val2 * 2


# Property 11: PlainSerializer with return_type specification
@given(st.lists(st.integers()))
def test_plain_serializer_return_type(values):
    """PlainSerializer with return_type should produce correct type."""
    
    def list_to_str(lst):
        return ','.join(map(str, lst))
    
    # Explicitly specify return type as str
    ListAsStr = Annotated[List[int], PlainSerializer(list_to_str, return_type=str)]
    
    class Model(BaseModel):
        data: ListAsStr
    
    model = Model(data=values)
    result = model.model_dump()
    
    # Property: Result should be a string representation
    expected = ','.join(map(str, values))
    assert result['data'] == expected
    assert isinstance(result['data'], str)


# Property 12: Nested serializers work correctly
@given(st.lists(st.lists(st.integers())))
def test_nested_serializer_application(nested_lists):
    """Serializers should work on nested structures."""
    
    def sort_list(lst):
        return sorted(lst)
    
    SortedList = Annotated[List[int], PlainSerializer(sort_list)]
    
    class Model(BaseModel):
        data: List[SortedList]
    
    model = Model(data=nested_lists)
    result = model.model_dump()
    
    # Property: Each inner list should be sorted
    for i, inner_list in enumerate(nested_lists):
        assert result['data'][i] == sorted(inner_list)


# Property 13: Check that serializer errors propagate correctly
@given(st.integers())
def test_serializer_error_propagation(value):
    """Errors in serializers should propagate correctly."""
    
    def failing_serializer(x):
        if x < 0:
            raise ValueError(f"Cannot serialize negative: {x}")
        return x * 2
    
    PositiveOnly = Annotated[int, PlainSerializer(failing_serializer)]
    
    class Model(BaseModel):
        field: PositiveOnly
    
    model = Model(field=value)
    
    if value < 0:
        # Property: Serialization should fail for negative values
        with pytest.raises(ValueError, match="Cannot serialize negative"):
            model.model_dump()
    else:
        # Property: Serialization should succeed for non-negative
        result = model.model_dump()
        assert result['field'] == value * 2


# Property 14: JSON mode affects both field and model serializers
@given(st.text())
def test_json_mode_affects_all_serializers(text):
    """JSON mode should affect both field and model serializers."""
    
    class Model(BaseModel):
        field: str
        
        @field_serializer('field', when_used='json')
        def serialize_field(self, v):
            return f"field_{v}"
        
        @model_serializer(mode='wrap', when_used='json')
        def serialize_model(self, handler, info):
            result = handler(self)
            result['extra'] = 'json_only'
            return result
    
    model = Model(field=text)
    
    # Python mode
    python_result = model.model_dump()
    assert python_result == {'field': text}
    assert 'extra' not in python_result
    
    # JSON mode
    json_result = json.loads(model.model_dump_json())
    assert json_result['field'] == f"field_{text}"
    assert json_result['extra'] == 'json_only'


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])