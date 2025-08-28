"""Final test to understand the validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline

print("Understanding the validation bug:")
print("=" * 50)

# Test directly calling _validate_props
baseline = EnabledBaseline("TestBaseline", validation=False)
print("1. Created EnabledBaseline without required fields")
print(f"   Properties dict: {baseline.properties}")
print(f"   Required fields: {[k for k, (t, req) in EnabledBaseline.props.items() if req]}")

print("\n2. Directly calling _validate_props()...")
try:
    # This should raise ValueError for missing required fields
    baseline._validate_props()
    print("   ✗ BUG CONFIRMED: _validate_props did not raise an error!")
except ValueError as e:
    print(f"   ✓ _validate_props raised error as expected: {e}")
except AttributeError as e:
    # The method might not be accessible
    print(f"   Cannot access _validate_props: {e}")
    
print("\n3. Looking at the _validate_props logic (line 411-419):")
print("   for k, (_, required) in self.props.items():")
print("       if required and k not in self.properties:")
print("           raise ValueError(...)")

print("\n4. The validation SHOULD work. Let me check if props is set correctly:")
print(f"   EnabledBaseline.props = {EnabledBaseline.props}")
print(f"   baseline.props = {baseline.props}")

print("\n5. Testing the actual condition:")
for k, (_, required) in baseline.props.items():
    if required:
        in_properties = k in baseline.properties
        print(f"   Field '{k}': required={required}, in properties={in_properties}")
        if not in_properties:
            print(f"      -> Should raise ValueError for missing '{k}'!")

# The issue might be with how validation is setup
print("\n6. Checking do_validation flag:")
print(f"   baseline.do_validation = {baseline.do_validation}")

baseline2 = EnabledBaseline("Test2", validation=True)
print(f"   baseline2 (validation=True).do_validation = {baseline2.do_validation}")