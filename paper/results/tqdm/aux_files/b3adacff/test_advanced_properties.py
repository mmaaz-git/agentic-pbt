"""Advanced property tests for potential bugs in pydantic.functional_validators"""

import gc
from typing import Any, List
from hypothesis import given, strategies as st, assume, settings, note
from pydantic import BaseModel, ValidationError, field_validator
from typing_extensions import Annotated
from pydantic.functional_validators import (
    AfterValidator, 
    BeforeValidator, 
    PlainValidator, 
    WrapValidator,
    SkipValidation
)


# Test 1: Validator order with same type of validators
@given(st.lists(st.integers(min_value=1, max_value=5), min_size=3, max_size=5))
def test_multiple_before_validators_order(multipliers):
    """Multiple BeforeValidators should apply in reverse order consistently"""
    
    execution_order = []
    
    validators = []
    for i, mult in enumerate(multipliers):
        def make_validator(m, idx):
            def validator(v):
                execution_order.append(f'before_{idx}')
                return v * m
            return validator
        validators.append(BeforeValidator(make_validator(mult, i)))
    
    # Build type with all validators
    TestType = int
    for validator in validators:
        TestType = Annotated[TestType, validator]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Clear execution order and test
    execution_order.clear()
    model = TestModel(value=1)
    
    # Check execution was in reverse order
    expected_order = [f'before_{i}' for i in range(len(multipliers)-1, -1, -1)]
    assert execution_order == expected_order
    
    # Calculate expected value (apply in reverse)
    expected_value = 1
    for mult in reversed(multipliers):
        expected_value *= mult
    assert model.value == expected_value


# Test 2: Complex interleaving of validator types
@given(
    st.integers(min_value=-100, max_value=100),
    st.lists(
        st.tuples(
            st.sampled_from(['before', 'after']),
            st.integers(min_value=1, max_value=10)
        ),
        min_size=2,
        max_size=6
    )
)
def test_interleaved_validators(input_value, operations):
    """Interleaved Before/After validators should maintain correct order"""
    
    execution_log = []
    
    # Create validators based on operations
    validators = []
    for i, (vtype, value) in enumerate(operations):
        if vtype == 'before':
            def make_before(val, idx):
                def validator(v):
                    execution_log.append(('before', idx, v))
                    return v + val
                return validator
            validators.append(BeforeValidator(make_before(value, i)))
        else:  # after
            def make_after(val, idx):
                def validator(v):
                    execution_log.append(('after', idx, v))
                    return v * val
                return validator
            validators.append(AfterValidator(make_after(value, i)))
    
    # Build annotated type
    TestType = int
    for validator in validators:
        TestType = Annotated[TestType, validator]
    
    class TestModel(BaseModel):
        value: TestType
    
    execution_log.clear()
    model = TestModel(value=input_value)
    
    # Verify execution order: all 'before' in reverse, then all 'after' in forward
    before_logs = [log for log in execution_log if log[0] == 'before']
    after_logs = [log for log in execution_log if log[0] == 'after']
    
    # Before validators should execute in reverse order of their indices
    before_indices = [idx for vtype, idx, _ in before_logs]
    before_expected = sorted([i for i, (vtype, _) in enumerate(operations) if vtype == 'before'], reverse=True)
    assert before_indices == before_expected
    
    # After validators should execute in forward order
    after_indices = [idx for vtype, idx, _ in after_logs]
    after_expected = [i for i, (vtype, _) in enumerate(operations) if vtype == 'after']
    assert after_indices == after_expected


# Test 3: PlainValidator interaction with Before/After
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=-50, max_value=50)
)
def test_plain_validator_in_chain(input_value, before_add, after_mult, plain_const):
    """PlainValidator should replace core validation but work with Before/After"""
    
    execution_order = []
    
    def before_validator(v):
        execution_order.append(f'before: {v} -> {v + before_add}')
        return v + before_add
    
    def plain_validator(v):
        execution_order.append(f'plain: {v} -> {plain_const}')
        return plain_const
    
    def after_validator(v):
        execution_order.append(f'after: {v} -> {v * after_mult}')
        return v * after_mult
    
    TestType = Annotated[
        int,
        BeforeValidator(before_validator),
        PlainValidator(plain_validator),
        AfterValidator(after_validator)
    ]
    
    class TestModel(BaseModel):
        value: TestType
    
    execution_order.clear()
    model = TestModel(value=input_value)
    
    # Expected flow: before -> plain -> after
    assert len(execution_order) == 3
    assert execution_order[0].startswith('before:')
    assert execution_order[1].startswith('plain:')
    assert execution_order[2].startswith('after:')
    
    # Value should be: (input + before_add) -> plain_const -> (plain_const * after_mult)
    assert model.value == plain_const * after_mult


# Test 4: WrapValidator interaction with other validators
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=1, max_value=10)
)
def test_wrap_validator_with_before_after(input_value, modifier):
    """WrapValidator should properly wrap the core validation plus Before/After validators"""
    
    execution_order = []
    
    def before_validator(v):
        execution_order.append(f'before: {v}')
        return v + modifier
    
    def wrap_validator(v, handler):
        execution_order.append(f'wrap_start: {v}')
        result = handler(v)
        execution_order.append(f'wrap_end: {result}')
        return result * 2
    
    def after_validator(v):
        execution_order.append(f'after: {v}')
        return v + 100
    
    TestType = Annotated[
        int,
        BeforeValidator(before_validator),
        WrapValidator(wrap_validator),
        AfterValidator(after_validator)
    ]
    
    class TestModel(BaseModel):
        value: TestType
    
    execution_order.clear()
    model = TestModel(value=input_value)
    
    # WrapValidator should wrap everything except AfterValidators that come after it
    # Expected order: wrap_start -> before -> (core validation) -> wrap_end -> after
    assert 'wrap_start' in execution_order[0]
    assert 'before' in execution_order[1]
    assert 'wrap_end' in execution_order[2]
    assert 'after' in execution_order[3]
    
    # Value calculation: 
    # wrap gets input_value
    # handler does: before (+modifier), then core validation
    # wrap multiplies by 2
    # after adds 100
    expected = ((input_value + modifier) * 2) + 100
    assert model.value == expected


# Test 5: Multiple WrapValidators
@given(st.integers(min_value=-10, max_value=10))
def test_multiple_wrap_validators(input_value):
    """Multiple WrapValidators should nest correctly"""
    
    execution_order = []
    
    def wrap1(v, handler):
        execution_order.append('wrap1_start')
        result = handler(v)
        execution_order.append('wrap1_end')
        return result + 1
    
    def wrap2(v, handler):
        execution_order.append('wrap2_start')  
        result = handler(v)
        execution_order.append('wrap2_end')
        return result * 2
    
    TestType = Annotated[int, WrapValidator(wrap1), WrapValidator(wrap2)]
    
    class TestModel(BaseModel):
        value: TestType
    
    execution_order.clear()
    model = TestModel(value=input_value)
    
    # wrap2 should wrap wrap1
    assert execution_order == ['wrap2_start', 'wrap1_start', 'wrap1_end', 'wrap2_end']
    
    # Value: wrap2(wrap1(input_value))
    # wrap1: input_value + 1
    # wrap2: (input_value + 1) * 2
    assert model.value == (input_value + 1) * 2


# Test 6: Validators with side effects (testing purity)
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=5, max_size=10))
def test_validator_side_effects(values):
    """Validators with side effects should not interfere with each other"""
    
    call_count = {'count': 0}
    
    def counting_validator(v):
        call_count['count'] += 1
        return v
    
    TestType = Annotated[int, AfterValidator(counting_validator)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # Create multiple models
    call_count['count'] = 0
    models = []
    for val in values:
        models.append(TestModel(value=val))
    
    # Each value should trigger exactly one call
    assert call_count['count'] == len(values)
    
    # Values should be unchanged
    for model, val in zip(models, values):
        assert model.value == val


# Test 7: Validator with exceptions at different stages
@given(
    st.integers(),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_exception_propagation_stages(input_value, fail_before, fail_plain, fail_after):
    """Exceptions at different validation stages should all become ValidationErrors"""
    
    def before_validator(v):
        if fail_before:
            raise ValueError("Before validation failed")
        return v
    
    def plain_validator(v):
        if fail_plain:
            raise ValueError("Plain validation failed")
        return v
    
    def after_validator(v):
        if fail_after:
            raise ValueError("After validation failed")
        return v
    
    TestType = Annotated[
        int,
        BeforeValidator(before_validator),
        PlainValidator(plain_validator),
        AfterValidator(after_validator)
    ]
    
    class TestModel(BaseModel):
        value: TestType
    
    if fail_before or fail_plain or fail_after:
        try:
            model = TestModel(value=input_value)
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            # Check that the appropriate stage failed
            error_msg = str(e)
            if fail_before:
                assert "Before validation failed" in error_msg
            elif fail_plain:
                assert "Plain validation failed" in error_msg
            elif fail_after:
                assert "After validation failed" in error_msg
    else:
        model = TestModel(value=input_value)
        assert model.value == input_value


# Test 8: Memory and performance with many validators
@given(st.integers(min_value=-10, max_value=10))
@settings(max_examples=20)  # Reduce for performance test
def test_many_validators_performance(input_value):
    """Many validators should not cause memory issues or stack overflow"""
    
    # Create 100 validators
    TestType = int
    for i in range(100):
        TestType = Annotated[TestType, AfterValidator(lambda v, i=i: v)]
    
    class TestModel(BaseModel):
        value: TestType
    
    # This should complete without stack overflow
    model = TestModel(value=input_value)
    assert model.value == input_value
    
    # Force garbage collection to check for memory leaks
    gc.collect()


# Test 9: Validator with complex lambda closures
@given(
    st.lists(st.integers(min_value=1, max_value=10), min_size=3, max_size=5)
)
def test_lambda_closure_behavior(multipliers):
    """Lambda validators with closures should capture variables correctly"""
    
    # This is a common bug pattern - using loop variable in lambda
    TestType = int
    
    # Incorrect way (all lambdas would use last value of mult)
    # for mult in multipliers:
    #     TestType = Annotated[TestType, AfterValidator(lambda v: v * mult)]
    
    # Correct way - capture mult in default argument
    for mult in multipliers:
        TestType = Annotated[TestType, AfterValidator(lambda v, m=mult: v * m)]
    
    class TestModel(BaseModel):
        value: TestType
    
    model = TestModel(value=1)
    
    # Each multiplier should be applied
    expected = 1
    for mult in multipliers:
        expected *= mult
    
    assert model.value == expected


# Test 10: Interaction with Python type conversion
@given(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
def test_type_conversion_with_validators(float_value):
    """Validators should work with Pydantic's type conversion"""
    
    execution_log = []
    
    def before_validator(v):
        execution_log.append(('before', type(v).__name__, v))
        return v
    
    def after_validator(v):
        execution_log.append(('after', type(v).__name__, v))
        return v
    
    TestType = Annotated[int, BeforeValidator(before_validator), AfterValidator(after_validator)]
    
    class TestModel(BaseModel):
        value: TestType
    
    execution_log.clear()
    model = TestModel(value=float_value)
    
    # Before validator sees original type (float)
    assert execution_log[0][0] == 'before'
    assert execution_log[0][1] == 'float'
    
    # After validator sees converted type (int)
    assert execution_log[1][0] == 'after'
    assert execution_log[1][1] == 'int'
    
    # Final value should be int
    assert isinstance(model.value, int)
    assert model.value == int(float_value)