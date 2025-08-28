import sys
import troposphere.rds as rds

# Minimal reproduction of the floating-point precision bug
print("Minimal reproduction of validate_v2_capacity floating-point bug")
print("="*60)

# This value is mathematically 1.0 but has tiny FP error
value = 1.0 + sys.float_info.epsilon
print(f"Testing value: {value}")
print(f"This is 1.0 + smallest float increment")
print(f"Actual value: {value:.20f}")

try:
    rds.validate_v2_capacity(value)
    print("Result: Accepted")
except ValueError as e:
    print(f"Result: Rejected with error:\n  {e}")
    print("\nBUG: Value extremely close to 1.0 (valid half-step) was rejected!")