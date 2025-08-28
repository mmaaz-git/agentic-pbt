"""Focused test demonstrating the integer() function bug."""

from hypothesis import given, strategies as st
import troposphere.ssmcontacts as ssmcontacts


@given(st.floats(min_value=-1000, max_value=1000).filter(lambda x: not x.is_integer()))
def test_integer_function_should_convert_floats(x):
    """
    Bug: The integer() function doesn't actually convert to integers.
    
    A function named 'integer' that is used to validate integer fields
    should either:
    1. Convert the input to an integer, OR  
    2. Reject non-integer inputs
    
    Instead, it validates that int(x) doesn't raise an error but
    returns the original float unchanged.
    """
    result = ssmcontacts.integer(x)
    
    # Current behavior: returns float unchanged
    assert result == x
    assert isinstance(result, float)
    
    # Expected behavior (one of these should be true):
    # Option 1: Conversion
    # assert isinstance(result, int)
    # assert result == int(x)
    
    # Option 2: Rejection  
    # Should raise ValueError for non-integer floats
    
    # This causes problems in AWS CloudFormation templates where
    # integer fields accept and preserve float values


if __name__ == "__main__":
    # Demonstrate with specific example
    print("Testing integer(10.5):")
    result = ssmcontacts.integer(10.5)
    print(f"  Result: {result}")
    print(f"  Type: {type(result)}")
    print(f"  Expected: 10 (int) or ValueError")
    print()
    
    print("Testing integer(3.14159):")
    result = ssmcontacts.integer(3.14159)
    print(f"  Result: {result}")
    print(f"  Type: {type(result)}")
    print(f"  Expected: 3 (int) or ValueError")
    print()
    
    # Show the impact on AWS resources
    print("Impact on AWS resources:")
    stage = ssmcontacts.Stage(DurationInMinutes=10.5)
    print(f"  Stage with DurationInMinutes=10.5: {stage.to_dict()}")
    print(f"  CloudFormation will receive: {'DurationInMinutes': 10.5}")
    print(f"  Expected: {'DurationInMinutes': 10} or validation error")