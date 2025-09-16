"""
Investigate the bug found in Range classes accepting floats
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.deadline as deadline

print("Testing AcceleratorCountRange with float value 1.5:")
try:
    range_obj = deadline.AcceleratorCountRange(Min=1.5)
    print(f"  Success! Created object with Min={range_obj.properties.get('Min')}")
    print(f"  Type of stored value: {type(range_obj.properties.get('Min'))}")
    
    # Try to convert to dict (which triggers validation)
    dict_repr = range_obj.to_dict()
    print(f"  to_dict() succeeded: {dict_repr}")
except Exception as e:
    print(f"  Failed with: {type(e).__name__}: {e}")

print("\nTesting direct integer validator with 1.5:")
try:
    result = deadline.integer(1.5)
    print(f"  Success! Result: {result}, type: {type(result)}")
except Exception as e:
    print(f"  Failed with: {type(e).__name__}: {e}")

print("\nTesting AcceleratorCountRange with string '1.5':")
try:
    range_obj = deadline.AcceleratorCountRange(Min="1.5")
    print(f"  Success! Created object with Min={range_obj.properties.get('Min')}")
    print(f"  Type of stored value: {type(range_obj.properties.get('Min'))}")
except Exception as e:
    print(f"  Failed with: {type(e).__name__}: {e}")

print("\nAnalyzing the issue:")
print("The integer validator itself works correctly (rejects 1.5)")
print("But when passing 1.5 to AcceleratorCountRange, it gets accepted!")
print("This suggests the validator might not be called properly during object construction.")

# Let's check what's happening with the validator
print("\nChecking AcceleratorCountRange.props:")
print(f"  Min property: {deadline.AcceleratorCountRange.props.get('Min')}")
print(f"  Max property: {deadline.AcceleratorCountRange.props.get('Max')}")

# The props show that integer function should be used as validator
# Let's see if it's being called
print("\nTesting with obviously invalid input (a list):")
try:
    range_obj = deadline.AcceleratorCountRange(Min=[1, 2, 3])
    print(f"  Success! Created object with Min={range_obj.properties.get('Min')}")
except Exception as e:
    print(f"  Failed with: {type(e).__name__}: {e}")