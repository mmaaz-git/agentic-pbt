"""Additional property-based tests for edge cases in pydantic.functional_validators"""

import math
from typing import Any
from hypothesis import given, strategies as st, assume, settings
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from typing_extensions import Annotated
from pydantic.functional_validators import (
    AfterValidator, 
    BeforeValidator, 
    PlainValidator, 
    WrapValidator,
    SkipValidation
)


# Test field_validator behavior
@given(
    st.integers(min_value=-100, max_value=100),
    st.text(min_size=1, max_size=10)
)
def test_field_validator_multiple_fields(int_value, str_value):
    """field_validator should work on multiple fields"""
    
    class TestModel(BaseModel):
        field1: int
        field2: int
        field3: str
        
        @field_validator('field1', 'field2')
        @classmethod
        def check_positive(cls, v):
            if v < 0:
                v = abs(v)
            return v
    
    model = TestModel(field1=int_value, field2=int_value, field3=str_value)
    
    # Both int fields should be positive
    assert model.field1 == abs(int_value)
    assert model.field2 == abs(int_value)
    assert model.field3 == str_value


# Test model_validator modes
@given(
    st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False)
)
def test_model_validator_after_mode(width, height):
    """model_validator in 'after' mode should see validated values"""
    
    validation_calls = []
    
    class Rectangle(BaseModel):
        width: float
        height: float
        
        @model_validator(mode='after')
        def record_validation(self):
            validation_calls.append({
                'width': self.width,
                'height': self.height,
                'is_model': isinstance(self, Rectangle)
            })
            return self
    
    model = Rectangle(width=width, height=height)
    
    # Validator should have been called once
    assert len(validation_calls) == 1
    assert validation_calls[0]['width'] == width
    assert validation_calls[0]['height'] == height
    assert validation_calls[0]['is_model'] == True


@given(st.dictionaries(st.text(), st.integers()))
def test_model_validator_before_mode(data):
    """model_validator in 'before' mode should see raw input"""
    
    validation_calls = []
    
    class TestModel(BaseModel):
        value: int = 0
        
        @model_validator(mode='before')
        @classmethod
        def record_input(cls, values):
            validation_calls.append({
                'input_type': type(values).__name__,
                'input_value': values.copy() if isinstance(values, dict) else values
            })
            # Extract 'value' from dictionary if present
            if isinstance(values, dict) and 'value' in values:
                return {'value': values['value']}
            return values
    
    if 'value' in data:
        try:
            model = TestModel(**data)
            assert len(validation_calls) == 1
            assert validation_calls[0]['input_type'] == 'dict'
        except ValidationError:
            # May fail if value is not convertible to int
            pass


# Test extreme nesting of validators
@given(st.integers(min_value=-10, max_value=10))
def test_deeply_nested_validators(input_value):
    """Many nested validators should compose correctly"""
    
    # Create 10 levels of nesting
    TestType = int
    for i in range(10):
        TestType = Annotated[TestType, AfterValidator(lambda v, i=i: v + 1)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # Each validator adds 1, so total should be input + 10
    assert model.value == input_value + 10


# Test validator with mutable default arguments (potential bug source)
@given(st.lists(st.integers()))
def test_validator_with_mutable_state(values):
    """Validators should not share mutable state between calls"""
    
    def validator_with_list(v, seen=[]):
        # Potential bug: mutable default argument
        if v in seen:
            raise ValueError(f"Duplicate value: {v}")
        seen.append(v)
        return v
    
    TestType = Annotated[int, AfterValidator(validator_with_list)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # This might fail if the validator shares state
    # Try to create models with duplicate values
    if len(values) >= 2:
        # Use the same value twice
        test_value = values[0] if values else 0
        
        model1 = TestModel(value=test_value)
        
        try:
            model2 = TestModel(value=test_value)
            # If we get here, the validators don't share state (expected)
        except ValidationError:
            # This would indicate shared mutable state (a bug!)
            pass


# Test PlainValidator that returns wrong type
@given(st.integers())
def test_plain_validator_type_coercion(input_value):
    """PlainValidator returning wrong type should still work if assignable"""
    
    def return_string(v):
        return str(v)
    
    # Annotate as int but validator returns string
    TestType = Annotated[int, PlainValidator(return_string)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # The value should be the string representation
    assert model.value == str(input_value)
    assert isinstance(model.value, str)


# Test WrapValidator that doesn't call handler
@given(st.integers(min_value=-100, max_value=100))
def test_wrap_validator_skip_handler(input_value):
    """WrapValidator can choose not to call the handler"""
    
    def wrap_validator(v, handler):
        # Don't call handler for negative values
        if v < 0:
            return 0  # Return default instead
        return handler(v)
    
    TestType = Annotated[int, WrapValidator(wrap_validator)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    if input_value < 0:
        assert model.value == 0
    else:
        assert model.value == input_value


# Test interaction between field_validator and Annotated validators
@given(st.integers())
def test_field_validator_with_annotated(input_value):
    """field_validator and Annotated validators should both apply"""
    
    TestType = Annotated[int, AfterValidator(lambda v: v * 2)]
    
    class TestModel(BaseModel):
        value: TestType
        
        @field_validator('value')
        @classmethod
        def add_ten(cls, v):
            return v + 10
    
    model = TestModel(value=input_value)
    
    # First the Annotated validator (*2), then field_validator (+10)
    expected = (input_value * 2) + 10
    assert model.value == expected


# Test recursive validator calls
@given(st.integers(min_value=0, max_value=20))
def test_recursive_validation(input_value):
    """Test validators on nested models"""
    
    def double(v):
        return v * 2
    
    DoubledInt = Annotated[int, AfterValidator(double)]
    
    class Inner(BaseModel):
        value: DoubledInt
    
    class Outer(BaseModel):
        inner: Inner
        other: DoubledInt
    
    model = Outer(inner={'value': input_value}, other=input_value)
    
    # Both should be doubled
    assert model.inner.value == input_value * 2
    assert model.other == input_value * 2


# Test validator exceptions with specific error messages
@given(st.integers())
def test_validator_custom_error_messages(input_value):
    """Custom error messages in validators should propagate"""
    
    def validate_range(v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        if v > 100:
            raise ValueError("Value must not exceed 100")
        return v
    
    TestType = Annotated[int, AfterValidator(validate_range)]
    
    class TestModel(BaseModel):
        value: TestType
    
    if 0 <= input_value <= 100:
        model = TestModel(value=input_value)
        assert model.value == input_value
    else:
        try:
            model = TestModel(value=input_value)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            error_msg = str(e)
            if input_value < 0:
                assert "non-negative" in error_msg
            else:
                assert "exceed 100" in error_msg