"""Minimal reproduction scripts for discovered bugs"""

# Bug 1: validate_clientvpnendpoint_vpnport error message formatting
print("=== Bug 1: validate_clientvpnendpoint_vpnport ===")
from troposphere.validators.ec2 import validate_clientvpnendpoint_vpnport

try:
    # Try an invalid port (not 443 or 1194)
    validate_clientvpnendpoint_vpnport(8080)
except TypeError as e:
    print(f"TypeError caught: {e}")
    print("Bug confirmed: Error message formatting fails with 'sequence item 0: expected str instance, int found'")
except ValueError as e:
    print(f"ValueError caught (expected): {e}")

print()

# Bug 2: validate_int_to_str error type inconsistency  
print("=== Bug 2: validate_int_to_str ===")
from troposphere.validators.ec2 import validate_int_to_str

# Test empty string
try:
    result = validate_int_to_str("")
    print(f"Result for empty string: {result}")
except TypeError as e:
    print(f"TypeError (expected per docstring): {e}")
except ValueError as e:
    print(f"ValueError (unexpected): {e}")
    print("Bug confirmed: Function raises ValueError instead of TypeError for empty string")

# Test other invalid inputs
print("\nTesting other invalid inputs:")
test_cases = [None, [], {}, "abc", "12.34"]
for test in test_cases:
    try:
        result = validate_int_to_str(test)
        print(f"  {test} -> {result}")
    except TypeError as e:
        print(f"  {test} -> TypeError: {e}")
    except ValueError as e:
        print(f"  {test} -> ValueError: {e}")