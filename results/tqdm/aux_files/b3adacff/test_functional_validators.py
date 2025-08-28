"""Property-based tests for pydantic.functional_validators"""

import math
from typing import Any, List
from hypothesis import given, strategies as st, assume, settings
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
from pydantic.functional_validators import (
    AfterValidator, 
    BeforeValidator, 
    PlainValidator, 
    WrapValidator,
    SkipValidation
)


# Property 1: Validator execution order consistency
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.lists(st.integers(min_value=1, max_value=10), min_size=2, max_size=5)
)
def test_before_validator_execution_order(input_value, multipliers):
    """BeforeValidators should execute in reverse order of annotation"""
    
    # Create BeforeValidator functions
    validators = []
    for i, multiplier in enumerate(multipliers):
        def make_validator(m, idx):
            def validator(v):
                return v * m
            validator.__name__ = f'validator_{idx}'
            return validator
        validators.append(BeforeValidator(make_validator(multiplier, i)))
    
    # Create annotated type with multiple BeforeValidators
    TestType = int
    for validator in validators:
        TestType = Annotated[TestType, validator]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Calculate expected result - validators apply in reverse order
    expected = input_value
    for multiplier in reversed(multipliers):
        expected = expected * multiplier
    
    # Test the model
    model = TestModel(value=input_value)
    assert model.value == expected


@given(
    st.integers(min_value=-1000, max_value=1000),
    st.lists(st.integers(min_value=1, max_value=10), min_size=2, max_size=5)
)
def test_after_validator_execution_order(input_value, adders):
    """AfterValidators should execute in forward order of annotation"""
    
    # Create AfterValidator functions
    validators = []
    for i, adder in enumerate(adders):
        def make_validator(a, idx):
            def validator(v):
                return v + a
            validator.__name__ = f'validator_{idx}'
            return validator
        validators.append(AfterValidator(make_validator(adder, i)))
    
    # Create annotated type with multiple AfterValidators
    TestType = int
    for validator in validators:
        TestType = Annotated[TestType, validator]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Calculate expected result - validators apply in forward order
    expected = input_value
    for adder in adders:
        expected = expected + adder
    
    # Test the model
    model = TestModel(value=input_value)
    assert model.value == expected


# Property 2: PlainValidator replacement behavior
@given(
    st.integers(),
    st.integers(min_value=-100, max_value=100)
)
def test_plain_validator_replaces_core_validation(input_value, replacement_value):
    """PlainValidator should completely replace core validation"""
    
    def replace_with_constant(v):
        # Ignore input and return constant
        return replacement_value
    
    TestType = Annotated[int, PlainValidator(replace_with_constant)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # The output should always be the replacement value, regardless of input
    model = TestModel(value=input_value)
    assert model.value == replacement_value


# Property 3: WrapValidator handler behavior
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=1, max_value=100)
)
def test_wrap_validator_handler_access(input_value, addend):
    """WrapValidator should correctly wrap inner validation"""
    
    handler_called = []
    
    def wrap_validator(v, handler):
        # Record that we got a handler
        handler_called.append(True)
        
        # Call the inner handler
        result = handler(v)
        
        # Verify it did type conversion
        assert isinstance(result, int)
        
        # Modify the result
        return result + addend
    
    TestType = Annotated[int, WrapValidator(wrap_validator)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # Check that handler was called
    assert handler_called == [True]
    
    # Check that the result is modified
    assert model.value == input_value + addend


# Property 4: Mixed validator composition
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=10)
)
def test_mixed_validator_composition(input_value, before_mult, after_add):
    """Mixed Before and After validators should compose correctly"""
    
    def multiply(v):
        return v * before_mult
    
    def add(v):
        return v + after_add
    
    TestType = Annotated[int, BeforeValidator(multiply), AfterValidator(add)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # BeforeValidator applies first (multiply), then AfterValidator (add)
    expected = (input_value * before_mult) + after_add
    assert model.value == expected


# Property 5: SkipValidation behavior
@given(st.text())
def test_skip_validation_bypasses_type_checking(input_value):
    """SkipValidation should bypass type validation"""
    
    # Use SkipValidation to allow any type for an int field
    TestType = Annotated[int, SkipValidation]
    
    class TestModel(BaseModel):
        value: TestType
    
    # This should not raise a validation error even with non-int input
    model = TestModel(value=input_value)
    assert model.value == input_value


# Property 6: Validator function purity
@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=2, max_size=10)
)
def test_validator_function_purity(values):
    """Validators should be pure - same input produces same output"""
    
    def double(v):
        return v * 2
    
    TestType = Annotated[int, AfterValidator(double)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Process the same values multiple times
    results1 = [TestModel(value=v).value for v in values]
    results2 = [TestModel(value=v).value for v in values]
    
    # Results should be identical
    assert results1 == results2
    assert all(r == v * 2 for v, r in zip(values, results1))


# Property 7: Complex validator chains
@given(
    st.floats(min_value=0.1, max_value=100, allow_nan=False, allow_infinity=False),
    st.lists(
        st.sampled_from(['add_one', 'multiply_two', 'subtract_half']),
        min_size=1,
        max_size=5
    )
)
def test_complex_validator_chains(input_value, operations):
    """Complex chains of validators should compose predictably"""
    
    validators = []
    
    for op in operations:
        if op == 'add_one':
            validators.append(AfterValidator(lambda v: v + 1))
        elif op == 'multiply_two':
            validators.append(AfterValidator(lambda v: v * 2))
        elif op == 'subtract_half':
            validators.append(AfterValidator(lambda v: v - 0.5))
    
    # Build annotated type
    TestType = float
    for validator in validators:
        TestType = Annotated[TestType, validator]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # Calculate expected value
    expected = input_value
    for op in operations:
        if op == 'add_one':
            expected = expected + 1
        elif op == 'multiply_two':
            expected = expected * 2
        elif op == 'subtract_half':
            expected = expected - 0.5
    
    assert math.isclose(model.value, expected, rel_tol=1e-7)


# Property 8: PlainValidator with other validators
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-10, max_value=10)
)
def test_plain_validator_with_after_validator(input_value, constant):
    """PlainValidator should work with AfterValidator"""
    
    def replace_with_constant(v):
        return constant
    
    def add_ten(v):
        return v + 10
    
    # PlainValidator replaces core validation, then AfterValidator applies
    TestType = Annotated[int, PlainValidator(replace_with_constant), AfterValidator(add_ten)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=input_value)
    
    # PlainValidator outputs constant, then AfterValidator adds 10
    assert model.value == constant + 10


# Property 9: Error propagation in validators
@given(st.integers())
def test_validator_error_propagation(input_value):
    """Errors in validators should propagate as ValidationError"""
    
    def always_fail(v):
        raise ValueError("Always fails")
    
    TestType = Annotated[int, AfterValidator(always_fail)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Should raise ValidationError, not ValueError
    try:
        model = TestModel(value=input_value)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected
    except Exception as e:
        assert False, f"Should raise ValidationError, not {type(e)}"


# Property 10: WrapValidator can modify or reject
@given(
    st.integers(min_value=-1000, max_value=1000)
)
def test_wrap_validator_can_reject(input_value):
    """WrapValidator can reject values based on inner validation result"""
    
    def wrap_with_range_check(v, handler):
        result = handler(v)
        
        # Reject values outside range
        if not (-100 <= result <= 100):
            raise ValueError(f"Value {result} out of range")
        
        return result
    
    TestType = Annotated[int, WrapValidator(wrap_with_range_check)]
    
    class TestModel(BaseModel):
        value: TestType
    
    if -100 <= input_value <= 100:
        # Should succeed
        model = TestModel(value=input_value)
        assert model.value == input_value
    else:
        # Should fail
        try:
            model = TestModel(value=input_value)
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass  # Expected