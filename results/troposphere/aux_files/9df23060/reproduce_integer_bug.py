"""Minimal reproduction of the integer() function bug in troposphere.ssmcontacts"""

import troposphere.ssmcontacts as ssmcontacts

# The integer() function should convert to int or reject non-integers
# But it actually returns floats unchanged

print("Bug demonstration:")
print("-" * 40)

# Test 1: Float input
result = ssmcontacts.integer(10.5)
print(f"integer(10.5) = {result}")
print(f"type: {type(result).__name__}")
assert result == 10.5  # Bug: Should be 10 or raise error
assert isinstance(result, float)  # Bug: Should be int

# Test 2: Another float
result = ssmcontacts.integer(3.14159)
print(f"\ninteger(3.14159) = {result}")
print(f"type: {type(result).__name__}")

# Test 3: Impact on AWS resources
stage = ssmcontacts.Stage(DurationInMinutes=25.7)
stage_dict = stage.to_dict()
print(f"\nStage(DurationInMinutes=25.7).to_dict():")
print(f"  {stage_dict}")
print(f"  DurationInMinutes type: {type(stage_dict['DurationInMinutes']).__name__}")

# This will send a float to CloudFormation for an integer field
print("\nProblem: CloudFormation expects integer for DurationInMinutes")
print("but receives float value 25.7 instead of 25 or validation error")