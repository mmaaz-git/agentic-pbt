"""
Minimal reproduction of the optional field None handling bug in troposphere
"""

import troposphere.route53 as r53

# Test case: ResourcePath is marked as optional (False) in props
# but passing None explicitly causes TypeError

print("Testing optional field handling in troposphere.route53.HealthCheckConfig")
print("=" * 70)

# This works - omitting optional field
config1 = r53.HealthCheckConfig(
    IPAddress='1.2.3.4',
    Port=80,
    Type='HTTP'
)
print("✓ Omitting optional ResourcePath: SUCCESS")
print(f"  Result: {config1.to_dict()}")

# This works - empty string
config2 = r53.HealthCheckConfig(
    IPAddress='1.2.3.4',
    Port=80,
    Type='HTTP',
    ResourcePath=''
)
print("✓ Empty string ResourcePath: SUCCESS")
print(f"  Result: {config2.to_dict()}")

# This FAILS - explicit None
try:
    config3 = r53.HealthCheckConfig(
        IPAddress='1.2.3.4',
        Port=80,
        Type='HTTP',
        ResourcePath=None  # Explicitly passing None for optional field
    )
    print("✓ None ResourcePath: SUCCESS")
    print(f"  Result: {config3.to_dict()}")
except TypeError as e:
    print("✗ None ResourcePath: FAILED")
    print(f"  Error: {e}")

print("\n" + "=" * 70)
print("BUG SUMMARY:")
print("Optional fields marked with (Type, False) in props should handle None")
print("gracefully by filtering it out, but instead raise TypeError.")
print("\nThis affects code that programmatically builds configs with optional")
print("values that might be None.")

# Show a realistic use case where this would be a problem
print("\n" + "=" * 70)
print("REALISTIC USE CASE:")
print()
print("def create_health_check(ip, port, protocol, path=None):")
print("    # Common pattern: optional parameter defaults to None")
print("    return r53.HealthCheckConfig(")
print("        IPAddress=ip,")
print("        Port=port,")
print("        Type=protocol,")
print("        ResourcePath=path  # FAILS if path is None!")
print("    )")
print()
print("# This pattern is common in code generation and dynamic config creation")
print("# Users must add explicit None checks for every optional field:")