"""Reproduce Bug 2: BeforeValidator exception can be masked"""

from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator, AfterValidator


def test_exception_masking():
    """Test if BeforeValidator exceptions can be masked by AfterValidator exceptions"""
    
    def before_validator_fail(v):
        raise ValueError("Before validation failed")
    
    def after_validator_fail(v):
        raise ValueError("After validation failed")
    
    def after_validator_pass(v):
        return v
    
    # Test 1: Both validators fail
    TestType1 = Annotated[
        int,
        BeforeValidator(before_validator_fail),
        AfterValidator(after_validator_fail)
    ]
    
    class TestModel1(BaseModel):
        value: TestType1
    
    print("Test 1: Both BeforeValidator and AfterValidator fail")
    try:
        model = TestModel1(value=5)
        print("  No error raised (unexpected!)")
    except ValidationError as e:
        error_msg = str(e)
        print(f"  Error message: {error_msg[:200]}...")
        if "Before validation failed" in error_msg:
            print("  ✓ BeforeValidator error is visible")
        else:
            print("  ✗ BeforeValidator error is NOT visible")
        if "After validation failed" in error_msg:
            print("  ✓ AfterValidator error is visible")
        else:
            print("  ✗ AfterValidator error is NOT visible")
    print()
    
    # Test 2: Only BeforeValidator fails
    TestType2 = Annotated[
        int,
        BeforeValidator(before_validator_fail),
        AfterValidator(after_validator_pass)
    ]
    
    class TestModel2(BaseModel):
        value: TestType2
    
    print("Test 2: Only BeforeValidator fails")
    try:
        model = TestModel2(value=5)
        print("  No error raised (unexpected!)")
    except ValidationError as e:
        error_msg = str(e)
        print(f"  Error message: {error_msg[:200]}...")
        if "Before validation failed" in error_msg:
            print("  ✓ BeforeValidator error is visible")
        else:
            print("  ✗ BeforeValidator error is NOT visible")
    print()
    
    # Test 3: Check if BeforeValidator actually runs when it should fail
    execution_log = []
    
    def before_validator_log_and_fail(v):
        execution_log.append("before_executed")
        raise ValueError("Before validation failed")
    
    TestType3 = Annotated[
        int,
        BeforeValidator(before_validator_log_and_fail),
        AfterValidator(after_validator_fail)
    ]
    
    class TestModel3(BaseModel):
        value: TestType3
    
    print("Test 3: Check if BeforeValidator actually executes")
    execution_log.clear()
    try:
        model = TestModel3(value=5)
    except ValidationError:
        pass
    
    if "before_executed" in execution_log:
        print("  ✓ BeforeValidator was executed")
    else:
        print("  ✗ BeforeValidator was NOT executed (BUG!)")
    

if __name__ == "__main__":
    test_exception_masking()
    print("\n=== ANALYSIS ===")
    print("If BeforeValidator errors are not visible or BeforeValidator")
    print("is not executed when it should fail, this indicates a bug in")
    print("the validator chain execution.")