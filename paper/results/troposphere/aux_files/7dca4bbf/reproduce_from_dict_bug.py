"""Reproduce the from_dict validation bug in troposphere.billingconductor."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.billingconductor import BillingGroup

print("Testing BillingGroup.from_dict() with missing required fields")
print("=" * 70)

# Test 1: Complete valid dict - this should work
print("\nTest 1: Valid complete dict")
valid_dict = {
    "Name": "TestGroup",
    "PrimaryAccountId": "123456789012",
    "AccountGrouping": {
        "LinkedAccountIds": ["123456789012"]
    },
    "ComputationPreference": {
        "PricingPlanArn": "arn:aws:pricing::123456789012:plan/test"
    }
}

try:
    bg = BillingGroup.from_dict("ValidBG", valid_dict)
    print(f"✅ SUCCESS: Created BillingGroup with all required fields")
    print(f"   Name: {bg.Name}")
    print(f"   PrimaryAccountId: {bg.PrimaryAccountId}")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")

# Test 2-5: Missing each required field one at a time
required_fields = ["Name", "PrimaryAccountId", "AccountGrouping", "ComputationPreference"]

for field in required_fields:
    print(f"\nTest: Missing required field '{field}'")
    incomplete_dict = valid_dict.copy()
    del incomplete_dict[field]
    
    try:
        bg = BillingGroup.from_dict(f"Missing{field}", incomplete_dict)
        print(f"❌ BUG CONFIRMED: Created BillingGroup without required field '{field}'")
        
        # Try to use to_dict() which should validate
        try:
            result = bg.to_dict()
            print(f"   to_dict() also succeeded (returned Type: {result.get('Type')})")
        except ValueError as e:
            print(f"   to_dict() correctly raised error: {e}")
            
    except (ValueError, AttributeError, KeyError) as e:
        print(f"✅ CORRECT: Raised error for missing '{field}': {type(e).__name__}")

# Test 6: Empty dict
print(f"\nTest: Completely empty dict")
try:
    bg = BillingGroup.from_dict("EmptyBG", {})
    print(f"❌ BUG CONFIRMED: Created BillingGroup from empty dict!")
    
    # This should definitely fail in to_dict()
    try:
        result = bg.to_dict()
        print(f"   to_dict() also succeeded: {result}")
    except ValueError as e:
        print(f"   to_dict() correctly raised error: {e}")
        
except Exception as e:
    print(f"✅ CORRECT: Raised error for empty dict: {type(e).__name__}")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("-" * 70)
print("The from_dict() method does not validate required fields at creation time.")
print("This allows creating invalid AWS CloudFormation resources that will fail")
print("when deployed. The validation only happens when to_dict() is called,")
print("which means errors are caught too late in the process.")
print("\nThis violates the principle of 'fail fast' and could lead to runtime")
print("errors in production when invalid templates are generated.")