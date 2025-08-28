import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloud9 as cloud9

# Bug: integer validator crashes with infinity
print("Testing integer validator with infinity...")
try:
    env = cloud9.EnvironmentEC2(
        "TestEnv",
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        AutomaticStopTimeMinutes=float('inf')
    )
    print("ERROR: Should have raised ValueError, but succeeded")
except OverflowError as e:
    print(f"BUG CONFIRMED: OverflowError instead of ValueError: {e}")
except ValueError as e:
    print(f"Expected ValueError: {e}")

# Test with negative infinity
print("\nTesting with negative infinity...")
try:
    env = cloud9.EnvironmentEC2(
        "TestEnv2",
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        AutomaticStopTimeMinutes=float('-inf')
    )
    print("ERROR: Should have raised ValueError, but succeeded")
except OverflowError as e:
    print(f"BUG CONFIRMED: OverflowError instead of ValueError: {e}")
except ValueError as e:
    print(f"Expected ValueError: {e}")

# Test with NaN
print("\nTesting with NaN...")
try:
    env = cloud9.EnvironmentEC2(
        "TestEnv3",
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        AutomaticStopTimeMinutes=float('nan')
    )
    print("ERROR: Should have raised ValueError, but succeeded")
except (OverflowError, ValueError) as e:
    print(f"Error type: {type(e).__name__}: {e}")