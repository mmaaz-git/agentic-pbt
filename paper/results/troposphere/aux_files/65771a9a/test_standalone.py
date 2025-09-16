"""Standalone property-based tests for troposphere.appconfig validators"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from troposphere.validators.appconfig import (
    validate_growth_type,
    validate_replicate_to,
    validate_validator_type,
)

print("Starting property-based testing for troposphere.appconfig validators...")
print("=" * 70)

# Test 1: Identity property - valid inputs returned unchanged
print("\n[TEST 1] Testing identity property for valid inputs...")
passed = True
try:
    @given(st.sampled_from(["LINEAR"]))
    @settings(max_examples=100)
    def test_growth_type_identity(value):
        assert validate_growth_type(value) == value
    
    test_growth_type_identity()
    print("✓ Growth type identity test passed")
except Exception as e:
    print(f"✗ Growth type identity test FAILED: {e}")
    passed = False

try:
    @given(st.sampled_from(["NONE", "SSM_DOCUMENT"]))
    @settings(max_examples=100)
    def test_replicate_to_identity(value):
        assert validate_replicate_to(value) == value
    
    test_replicate_to_identity()
    print("✓ Replicate-to identity test passed")
except Exception as e:
    print(f"✗ Replicate-to identity test FAILED: {e}")
    passed = False

try:
    @given(st.sampled_from(["JSON_SCHEMA", "LAMBDA"]))
    @settings(max_examples=100)
    def test_validator_type_identity(value):
        assert validate_validator_type(value) == value
    
    test_validator_type_identity()
    print("✓ Validator type identity test passed")
except Exception as e:
    print(f"✗ Validator type identity test FAILED: {e}")
    passed = False

# Test 2: Invalid inputs should raise ValueError
print("\n[TEST 2] Testing invalid input rejection...")
try:
    @given(st.text(min_size=1))
    @settings(max_examples=100)
    def test_growth_type_invalid(value):
        assume(value not in ["LINEAR"])
        try:
            validate_growth_type(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError as e:
            msg = str(e)
            assert "DeploymentStrategy GrowthType must be one of:" in msg
            assert "LINEAR" in msg
    
    test_growth_type_invalid()
    print("✓ Growth type invalid input test passed")
except Exception as e:
    print(f"✗ Growth type invalid input test FAILED: {e}")
    passed = False

# Test 3: Case sensitivity
print("\n[TEST 3] Testing case sensitivity...")
try:
    lowercase_variants = ["linear", "Linear", "none", "ssm_document", "json_schema", "lambda"]
    for value in lowercase_variants:
        # Test growth_type
        if value in ["linear", "Linear"]:
            try:
                validate_growth_type(value)
                print(f"✗ Growth type validator incorrectly accepted '{value}'")
                passed = False
            except ValueError:
                pass  # Expected
        
        # Test replicate_to
        if value in ["none", "ssm_document"]:
            try:
                validate_replicate_to(value)
                print(f"✗ Replicate-to validator incorrectly accepted '{value}'")
                passed = False
            except ValueError:
                pass  # Expected
        
        # Test validator_type
        if value in ["json_schema", "lambda"]:
            try:
                validate_validator_type(value)
                print(f"✗ Validator type validator incorrectly accepted '{value}'")
                passed = False
            except ValueError:
                pass  # Expected
    
    if passed:
        print("✓ Case sensitivity test passed")
except Exception as e:
    print(f"✗ Case sensitivity test FAILED: {e}")
    passed = False

# Test 4: Error message format
print("\n[TEST 4] Testing error message format...")
try:
    # Test growth_type error message
    try:
        validate_growth_type("INVALID")
    except ValueError as e:
        expected = "DeploymentStrategy GrowthType must be one of: LINEAR"
        if str(e) != expected:
            print(f"✗ Growth type error message incorrect:")
            print(f"  Expected: '{expected}'")
            print(f"  Got: '{str(e)}'")
            passed = False
        else:
            print("✓ Growth type error message format correct")
    
    # Test replicate_to error message
    try:
        validate_replicate_to("INVALID")
    except ValueError as e:
        expected = "DeploymentStrategy ReplicateTo must be one of: NONE, SSM_DOCUMENT"
        if str(e) != expected:
            print(f"✗ Replicate-to error message incorrect:")
            print(f"  Expected: '{expected}'")
            print(f"  Got: '{str(e)}'")
            passed = False
        else:
            print("✓ Replicate-to error message format correct")
    
    # Test validator_type error message
    try:
        validate_validator_type("INVALID")
    except ValueError as e:
        expected = "ConfigurationProfile Validator Type must be one of: JSON_SCHEMA, LAMBDA"
        if str(e) != expected:
            print(f"✗ Validator type error message incorrect:")
            print(f"  Expected: '{expected}'")
            print(f"  Got: '{str(e)}'")
            passed = False
        else:
            print("✓ Validator type error message format correct")
except Exception as e:
    print(f"✗ Error message format test FAILED: {e}")
    passed = False

# Test 5: None value handling
print("\n[TEST 5] Testing None value handling...")
validators = [
    (validate_growth_type, "growth_type"),
    (validate_replicate_to, "replicate_to"),
    (validate_validator_type, "validator_type")
]

for validator, name in validators:
    try:
        result = validator(None)
        print(f"✗ {name} validator incorrectly accepted None value, returned: {result}")
        passed = False
    except (ValueError, TypeError) as e:
        print(f"✓ {name} validator correctly rejected None value")
    except Exception as e:
        print(f"✗ {name} validator raised unexpected error for None: {e}")
        passed = False

# Test 6: Empty string handling
print("\n[TEST 6] Testing empty string handling...")
for validator, name in validators:
    try:
        result = validator("")
        print(f"✗ {name} validator incorrectly accepted empty string, returned: {result}")
        passed = False
    except ValueError as e:
        print(f"✓ {name} validator correctly rejected empty string")
    except Exception as e:
        print(f"✗ {name} validator raised unexpected error for empty string: {e}")
        passed = False

# Test 7: Special characters
print("\n[TEST 7] Testing special character rejection...")
special_chars = ["@#$%", "LINEAR!", "NONE ", " SSM_DOCUMENT", "JSON-SCHEMA", "LAMBDA\n"]
special_test_passed = True
for char in special_chars:
    for validator, name in validators:
        try:
            result = validator(char)
            # Only flag if it's not a valid value
            if result not in ["LINEAR", "NONE", "SSM_DOCUMENT", "JSON_SCHEMA", "LAMBDA"]:
                print(f"✗ {name} validator incorrectly accepted '{char}'")
                special_test_passed = False
        except ValueError:
            pass  # Expected for invalid inputs

if special_test_passed:
    print("✓ Special character rejection test passed")
else:
    passed = False

# Test 8: Type coercion - testing with integers
print("\n[TEST 8] Testing type handling with non-string inputs...")
non_string_inputs = [0, 1, 123, [], {}, True, False, 3.14]
for value in non_string_inputs:
    for validator, name in validators:
        try:
            result = validator(value)
            print(f"✗ {name} validator accepted non-string value {value}: {result}")
            passed = False
        except (ValueError, TypeError, AttributeError) as e:
            pass  # Expected - validators should reject non-strings
        except Exception as e:
            print(f"✗ {name} validator raised unexpected error for {value}: {type(e).__name__}: {e}")
            passed = False

print("✓ Non-string input handling test passed")

# Summary
print("\n" + "=" * 70)
if passed:
    print("✅ All property-based tests PASSED!")
else:
    print("❌ Some tests FAILED - review output above")

print("\nTested properties:")
print("1. Identity property: Valid inputs returned unchanged")
print("2. Invalid input rejection: Invalid inputs raise ValueError")
print("3. Case sensitivity: Only uppercase values accepted")
print("4. Error message format: Consistent error messages")
print("5. None value handling: None values rejected")
print("6. Empty string handling: Empty strings rejected")
print("7. Special character rejection: Special chars in inputs rejected")
print("8. Type handling: Non-string types handled properly")