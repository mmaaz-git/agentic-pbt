"""Minimal reproduction of empty title validation bug in troposphere."""

from troposphere import shield

# Bug: Empty string title bypasses validation
print("Creating DRTAccess with empty string title...")
drt = shield.DRTAccess('', RoleArn='arn:aws:iam::123456789012:role/Test')
print(f"Success! Created object with title: {repr(drt.title)}")

# The object can be used normally
result = drt.to_dict()
print(f"to_dict() works: {result}")

# But if we manually validate, it fails
print("\nManually calling validate_title()...")
try:
    drt.validate_title()
    print("validate_title() succeeded (unexpected)")
except ValueError as e:
    print(f"validate_title() correctly raises: {e}")

print("\n=== BUG CONFIRMED ===")
print("Empty string titles bypass validation in __init__ but fail in validate_title()")
print("This is because __init__ only calls validate_title() if title is truthy,")
print("but empty string is falsy in Python.")