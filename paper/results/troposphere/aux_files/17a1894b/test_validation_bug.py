import troposphere.waf as waf

# Minimal test to understand validation behavior
print("Testing validation timing...")

# Test 1: Does validation happen at creation or serialization?
try:
    action = waf.Action(Type="INVALID")
    print("✓ Created Action with invalid Type='INVALID'")
    try:
        action.to_dict()
        print("✓ to_dict() succeeded")
    except ValueError as e:
        print(f"✗ to_dict() failed: {e}")
except ValueError as e:
    print(f"✗ Creation failed immediately: {e}")

print()

# Test 2: Does no_validation() work as expected?
try:
    action = waf.Action(Type="INVALID")
    action.no_validation()
    result = action.to_dict()
    print(f"With no_validation(): {result}")
except Exception as e:
    print(f"no_validation() doesn't prevent validation at creation: {e}")

print()

# Test 3: What about using to_dict(validation=False)?
try:
    # Can't create with invalid value, so this won't work
    pass
except:
    pass

# Test 4: Test the actual implementation expectations
print("Checking when validation actually occurs...")
import troposphere.validators as validators

# Direct validator call
try:
    result = validators.waf_action_type("INVALID")
    print(f"Direct validator call succeeded: {result}")
except ValueError as e:
    print(f"Direct validator call failed as expected: {e}")

print()

# Test 5: Can we bypass validation somehow?
print("Testing if we can bypass validation...")
action = waf.Action.__new__(waf.Action)
action.Type = "INVALID"
print(f"Created Action with Type='INVALID' using __new__")

try:
    result = action.to_dict()
    print(f"to_dict() result: {result}")
except Exception as e:
    print(f"to_dict() failed: {e}")

try:
    result = action.to_dict(validation=False) 
    print(f"to_dict(validation=False) result: {result}")
except Exception as e:
    print(f"to_dict(validation=False) failed: {e}")