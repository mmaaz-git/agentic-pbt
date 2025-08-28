import troposphere.waf as waf
import troposphere.validators as validators

print("Testing no_validation() method behavior...")
print()

# Test 1: Can we use no_validation() to bypass validation?
print("Test 1: Using no_validation() on class before creation")
try:
    # Try calling no_validation on the class first
    NoValidationAction = waf.Action
    NoValidationAction.no_validation = lambda self: self  # Try to override
    action = NoValidationAction(Type="INVALID")
    print("✓ Created with invalid type after modifying class")
except Exception as e:
    print(f"✗ Still failed: {e}")

print()

# Test 2: Check if validation can be disabled at all
print("Test 2: Checking if there's a way to disable validation globally")
import troposphere

# Check if there's a global validation flag
if hasattr(troposphere, 'validation'):
    print(f"troposphere.validation = {troposphere.validation}")
else:
    print("No global validation flag found")

print()

# Test 3: Test the documented behavior - no_validation should work
print("Test 3: Testing correct usage of no_validation()")
try:
    # The correct way according to most AWS CloudFormation libraries
    action = waf.Action(Type="ALLOW")  # Start with valid
    action.Type = "INVALID"  # Change to invalid
    action.no_validation()  # Disable validation
    result = action.to_dict()
    print(f"✓ to_dict() succeeded with invalid type after no_validation(): {result}")
except Exception as e:
    print(f"✗ Failed: {e}")

print()

# Test 4: What does no_validation actually do?
print("Test 4: Investigating no_validation() implementation")
action = waf.Action(Type="ALLOW")
print(f"Before no_validation: do_validation = {getattr(action, 'do_validation', 'not found')}")
action.no_validation()
print(f"After no_validation: do_validation = {getattr(action, 'do_validation', 'not found')}")

print()

# Test 5: Check validation flag behavior in to_dict
print("Test 5: Testing to_dict with different validation flags")
action = waf.Action(Type="ALLOW")
action.Type = "INVALID"  # Manually change to invalid

try:
    result = action.to_dict(validation=True)
    print(f"to_dict(validation=True) with invalid: {result}")
except Exception as e:
    print(f"to_dict(validation=True) failed as expected: {type(e).__name__}")

try:
    result = action.to_dict(validation=False)
    print(f"to_dict(validation=False) with invalid: {result}")
except Exception as e:
    print(f"to_dict(validation=False) also failed: {type(e).__name__}")