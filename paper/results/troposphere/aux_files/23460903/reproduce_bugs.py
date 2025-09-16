#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Reproduce and validate the bugs found in troposphere validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, double, boolean

print("=" * 60)
print("Bug 1: integer validator accepts floats")
print("=" * 60)

# Test with float values
test_floats = [0.5, 1.5, -2.7, 3.14159]
for f in test_floats:
    try:
        result = integer(f)
        print(f"integer({f}) = {result} (type: {type(result).__name__})")
        # Verify it actually converts correctly
        int_result = int(result)
        print(f"  int(result) = {int_result}")
        if int_result != f:
            print(f"  WARNING: Data loss! {f} became {int_result}")
    except ValueError as e:
        print(f"integer({f}) raised ValueError: {e}")

print("\n" + "=" * 60)
print("Bug 2: double validator accepts 'Inf' string")
print("=" * 60)

# Test with special float strings
test_strings = ['Inf', '-Inf', 'inf', '-inf', 'Infinity', 'NaN', 'nan']
for s in test_strings:
    try:
        result = double(s)
        print(f"double('{s}') = {result}")
        float_result = float(result)
        print(f"  float(result) = {float_result}")
    except ValueError as e:
        print(f"double('{s}') raised ValueError: {e}")

print("\n" + "=" * 60)
print("Bug 3: boolean validator accepts float 0.0")
print("=" * 60)

# Test with float values
test_float_bools = [0.0, 1.0, -0.0, 2.0, 0.5]
for f in test_float_bools:
    try:
        result = boolean(f)
        print(f"boolean({f}) = {result} (type: {type(result).__name__})")
    except ValueError as e:
        print(f"boolean({f}) raised ValueError")

print("\n" + "=" * 60)
print("Testing impact on actual GameLift resources")
print("=" * 60)

import troposphere.gamelift as gamelift

# Test 1: Can we create port ranges with float values?
try:
    port_range = gamelift.ConnectionPortRange(
        FromPort=1024.5,
        ToPort=2048.7
    )
    result = port_range.to_dict()
    print(f"ConnectionPortRange with floats: {result}")
    print("  This could cause CloudFormation template issues!")
except (TypeError, ValueError) as e:
    print(f"ConnectionPortRange with floats raised: {e}")

# Test 2: Can we create LocationCapacity with infinity?
try:
    capacity = gamelift.LocationCapacity(
        DesiredEC2Instances=float('inf'),
        MinSize=1,
        MaxSize=10
    )
    result = capacity.to_dict()
    print(f"LocationCapacity with infinity: {result}")
    print("  This would create an invalid CloudFormation template!")
except (TypeError, ValueError) as e:
    print(f"LocationCapacity with infinity raised: {e}")

# Test 3: Check if validation happens in to_dict()
print("\n" + "=" * 60)
print("Checking validation in to_dict()")
print("=" * 60)

try:
    port_range = gamelift.ConnectionPortRange(
        FromPort=1024.5,
        ToPort=2048.7
    )
    # Try with validation
    result_with_validation = port_range.to_dict(validation=True)
    print(f"to_dict(validation=True): {result_with_validation}")
    
    # Try without validation
    result_no_validation = port_range.to_dict(validation=False)
    print(f"to_dict(validation=False): {result_no_validation}")
    
except Exception as e:
    print(f"Error during to_dict(): {e}")