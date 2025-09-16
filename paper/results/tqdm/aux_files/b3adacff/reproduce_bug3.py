"""Reproduce Bug 3: BeforeValidator and type conversion order"""

from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator, AfterValidator


def test_type_conversion_order():
    """Test when type conversion happens relative to validators"""
    
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
    
    print("Test 1: Pass integer (no conversion needed)")
    execution_log.clear()
    model = TestModel(value=42)
    print(f"  Input: 42 (int)")
    for stage, type_name, value in execution_log:
        print(f"  {stage}: type={type_name}, value={value}")
    print()
    
    print("Test 2: Pass string that can be converted to int")
    execution_log.clear()
    model = TestModel(value="123")
    print(f"  Input: '123' (str)")
    for stage, type_name, value in execution_log:
        print(f"  {stage}: type={type_name}, value={value}")
    print()
    
    print("Test 3: Pass float without fractional part")
    execution_log.clear()
    model = TestModel(value=42.0)
    print(f"  Input: 42.0 (float)")
    for stage, type_name, value in execution_log:
        print(f"  {stage}: type={type_name}, value={value}")
    print()
    
    print("Test 4: Pass float with fractional part (should fail)")
    execution_log.clear()
    try:
        model = TestModel(value=42.5)
        print(f"  Model created with value: {model.value}")
    except ValidationError as e:
        print(f"  Failed as expected: {str(e)[:100]}...")
        if execution_log:
            print("  Validators that ran before failure:")
            for stage, type_name, value in execution_log:
                print(f"    {stage}: type={type_name}, value={value}")
        else:
            print("  No validators ran before failure")
    print()
    
    print("=== ANALYSIS ===")
    print("BeforeValidator is supposed to run BEFORE type conversion,")
    print("allowing it to see and potentially transform the raw input.")
    print("If BeforeValidator sees the already-converted type, this is a bug.")
    print()
    print("Expected behavior:")
    print("  - BeforeValidator should see: original input type (str, float, etc)")
    print("  - AfterValidator should see: converted target type (int)")
    print()
    print("Actual behavior from tests above:")
    print("  - BeforeValidator sees the ORIGINAL type for strings")
    print("  - But for floats, validation fails BEFORE BeforeValidator runs")
    print("  - This suggests type coercion rules are applied before BeforeValidator")


if __name__ == "__main__":
    test_type_conversion_order()