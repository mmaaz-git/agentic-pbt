"""Investigate root cause of validation bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline

print("Investigating validation flow:")
print("=" * 50)

# Test 1: Check if validate_title is called
print("\n1. Testing title validation:")
baseline = EnabledBaseline("", BaselineIdentifier="id", BaselineVersion="1.0", TargetIdentifier="target")
print(f"   Empty title accepted in __init__: title='{baseline.title}'")

# Check if title is None or empty string
print(f"   Title is None: {baseline.title is None}")
print(f"   Title is empty string: {baseline.title == ''}")
print(f"   Bool of title: {bool(baseline.title)}")

# Check the validation condition in code (line 183-184 of __init__.py):
# if self.title:
#     self.validate_title()
print("\n   The bug is in __init__.py line 183-184:")
print("   if self.title:  # Empty string is falsy!")
print("       self.validate_title()")
print("   -> Empty string bypasses validation!")

print("\n2. Testing required field validation:")
baseline2 = EnabledBaseline("Test", validation=False)
print(f"   Created object without required fields")
print(f"   Properties: {baseline2.properties}")

# The to_dict method should call _validate_props
dict_result = baseline2.to_dict(validation=True)
print(f"   to_dict returned: {dict_result}")
print("\n   The bug is that _validate_props checks self.properties")
print("   but an empty properties dict doesn't trigger validation!")

# Check what happens when properties is empty
print("\n3. Checking _validate_props behavior:")
print(f"   Object props definition: {EnabledBaseline.props}")
print(f"   Required fields: {[k for k, (t, req) in EnabledBaseline.props.items() if req]}")
print(f"   Object properties dict: {baseline2.properties}")
print("\n   _validate_props iterates over self.props and checks if required")
print("   fields are in self.properties, but if properties is empty,")
print("   it returns the resource dict WITHOUT Properties key!")

# Verify the actual bug
print("\n4. Confirming the issue:")
print("   When properties dict is empty, to_dict returns resource WITHOUT 'Properties' key")
print("   This is the actual behavior that bypasses validation failure")