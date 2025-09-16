"""Test the validation flow more carefully"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline

print("Testing validation flow:")
print("=" * 50)

# Create object without required fields
baseline = EnabledBaseline("TestBaseline", validation=False)

print("1. Object created without required fields")
print(f"   Properties: {baseline.properties}")
print(f"   Props definition has required fields: {[k for k, (t, req) in EnabledBaseline.props.items() if req]}")

# Monkey-patch to trace calls
original_validate_props = baseline._validate_props
called = []

def traced_validate_props():
    called.append("_validate_props")
    print("   _validate_props was called!")
    return original_validate_props()

baseline._validate_props = traced_validate_props

print("\n2. Calling to_dict with validation=True...")
try:
    result = baseline.to_dict(validation=True)
    print(f"   Result: {result}")
    print(f"   _validate_props called: {len(called) > 0}")
except ValueError as e:
    print(f"   Validation error raised: {e}")

# Check the to_dict logic
print("\n3. Checking to_dict logic (line 337-351):")
print("   Line 342: if self.properties:")
print(f"   self.properties is: {baseline.properties}")
print(f"   bool(self.properties) is: {bool(baseline.properties)}")
print("\n   THE BUG: to_dict returns early if properties is empty!")
print("   It never reaches _validate_props when properties dict is empty!")

# Confirm by checking the actual code flow
baseline2 = EnabledBaseline("Test2", validation=False, BaselineIdentifier="test")
print("\n4. With one property set:")
print(f"   Properties: {baseline2.properties}")
try:
    result2 = baseline2.to_dict(validation=True)
    print(f"   Result: {result2}")
except ValueError as e:
    print(f"   ✓ Validation error raised correctly: {e}")