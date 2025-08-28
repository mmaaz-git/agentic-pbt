# Bug Report: pydantic.functional_validators PlainValidator Blocks BeforeValidator

**Target**: `pydantic.functional_validators`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When PlainValidator and BeforeValidator are used together in an Annotated type, the BeforeValidator is completely skipped, violating the documented validator execution order.

## Property-Based Test

```python
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
```

**Failing input**: `test_plain_validator_in_chain(input_value=0, before_add=1, after_mult=1, plain_const=0)`

## Reproducing the Bug

```python
from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator, PlainValidator, AfterValidator

execution_order = []

def before_validator(v):
    execution_order.append(f'before: input={v}')
    return v + 100

def plain_validator(v):
    execution_order.append(f'plain: input={v}')
    return 999

def after_validator(v):
    execution_order.append(f'after: input={v}')
    return v + 1

TestType = Annotated[
    int,
    BeforeValidator(before_validator),
    PlainValidator(plain_validator),
    AfterValidator(after_validator)
]

class TestModel(BaseModel):
    value: TestType

execution_order.clear()
model = TestModel(value=5)

print(f"Execution order: {execution_order}")
print(f"Final value: {model.value}")
print(f"Expected: ['before: input=5', 'plain: input=105', 'after: input=999']")
print(f"Actual: {execution_order}")
```

## Why This Is A Bug

According to Pydantic's documentation, the validator execution order should be:
1. BeforeValidators (in reverse order of annotation)
2. Core validation (or PlainValidator replacement)
3. AfterValidators (in forward order)

PlainValidator is documented to replace only the core validation step, not the entire validation pipeline. BeforeValidators should still execute before PlainValidator, allowing input transformation before the replacement validation logic runs.

The current behavior breaks this contract by completely skipping BeforeValidators when PlainValidator is present, making it impossible to pre-process input before applying custom validation logic via PlainValidator.

## Fix

The issue appears to be in how PlainValidator is implemented - it seems to be replacing the entire validation chain rather than just the core validation step. The fix would involve ensuring that BeforeValidators are still executed even when PlainValidator is present.

```diff
# Conceptual fix in the validator chain builder
def build_validator_chain(validators):
    before_validators = [v for v in validators if isinstance(v, BeforeValidator)]
    plain_validator = next((v for v in validators if isinstance(v, PlainValidator)), None)
    after_validators = [v for v in validators if isinstance(v, AfterValidator)]
    
-   if plain_validator:
-       # Current: PlainValidator replaces everything
-       return chain(plain_validator, after_validators)
+   if plain_validator:
+       # Fixed: PlainValidator only replaces core validation
+       return chain(before_validators, plain_validator, after_validators)
    
    return chain(before_validators, core_validation, after_validators)
```