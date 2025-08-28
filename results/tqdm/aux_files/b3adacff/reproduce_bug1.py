"""Reproduce Bug 1: PlainValidator prevents BeforeValidator execution"""

from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator, PlainValidator, AfterValidator


def test_plain_validator_blocks_before():
    """PlainValidator prevents BeforeValidator from executing"""
    
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
    
    # Test 1: With PlainValidator
    TestType1 = Annotated[
        int,
        BeforeValidator(before_validator),
        PlainValidator(plain_validator),
        AfterValidator(after_validator)
    ]
    
    class TestModel1(BaseModel):
        value: TestType1
    
    execution_order.clear()
    model1 = TestModel1(value=5)
    print("With PlainValidator:")
    print(f"  Execution order: {execution_order}")
    print(f"  Final value: {model1.value}")
    print(f"  Expected: 5 -> 105 (before) -> 999 (plain) -> 1000 (after)")
    print(f"  Actual: {model1.value}")
    print()
    
    # Test 2: Without PlainValidator
    TestType2 = Annotated[
        int,
        BeforeValidator(before_validator),
        AfterValidator(after_validator)
    ]
    
    class TestModel2(BaseModel):
        value: TestType2
    
    execution_order.clear()
    model2 = TestModel2(value=5)
    print("Without PlainValidator:")
    print(f"  Execution order: {execution_order}")
    print(f"  Final value: {model2.value}")
    print(f"  Expected: 5 -> 105 (before) -> 106 (after)")
    print(f"  Actual: {model2.value}")
    print()
    
    # Bug confirmation
    # Check if BeforeValidator was skipped in the first test
    return 'before' not in str(execution_order)


if __name__ == "__main__":
    has_bug = test_plain_validator_blocks_before()
    if has_bug:
        print("\n=== BUG SUMMARY ===")
        print("When PlainValidator is used in combination with BeforeValidator,")
        print("the BeforeValidator is skipped entirely. This violates the documented")
        print("behavior that BeforeValidators should run before core validation,")
        print("and PlainValidator should only replace the core validation step.")