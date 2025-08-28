"""Advanced property-based tests to find deeper bugs in troposphere.appconfig"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
from hypothesis import given, strategies as st, assume, settings
from troposphere.validators.appconfig import (
    validate_growth_type,
    validate_replicate_to,
    validate_validator_type,
)
from troposphere import appconfig

print("Running advanced property-based tests...")
print("=" * 70)

# Test 1: Test if validators handle substrings of valid values
print("\n[TEST 1] Testing substring handling...")
bugs_found = []

# Growth type substrings
substrings = ["LIN", "EAR", "LINEA", "INEAR", "L", "R"]
for substr in substrings:
    try:
        result = validate_growth_type(substr)
        bugs_found.append(f"Growth type validator accepted substring '{substr}' - returned: {result}")
    except ValueError:
        pass  # Expected

# Replicate to substrings
substrings = ["NON", "ONE", "SSM", "DOCUMENT", "SSM_", "_DOCUMENT", "SSM_DOC"]
for substr in substrings:
    try:
        result = validate_replicate_to(substr)
        bugs_found.append(f"Replicate-to validator accepted substring '{substr}' - returned: {result}")
    except ValueError:
        pass  # Expected

if bugs_found:
    print("✗ Substring handling issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Substring handling test passed")

# Test 2: Test validators with concatenated valid values
print("\n[TEST 2] Testing concatenated valid values...")
bugs_found = []

concatenated = ["LINEARLINEAR", "LINEARNONE", "NONENONE", "SSM_DOCUMENTSSM_DOCUMENT", 
                "JSON_SCHEMALAMBDA", "LAMBDAJSON_SCHEMA"]
validators_map = {
    "LINEARLINEAR": (validate_growth_type, "growth_type"),
    "LINEARNONE": (validate_growth_type, "growth_type"),
    "NONENONE": (validate_replicate_to, "replicate_to"),
    "SSM_DOCUMENTSSM_DOCUMENT": (validate_replicate_to, "replicate_to"),
    "JSON_SCHEMALAMBDA": (validate_validator_type, "validator_type"),
    "LAMBDAJSON_SCHEMA": (validate_validator_type, "validator_type"),
}

for value in concatenated:
    if value in validators_map:
        validator, name = validators_map[value]
        try:
            result = validator(value)
            bugs_found.append(f"{name} validator accepted concatenated value '{value}' - returned: {result}")
        except ValueError:
            pass  # Expected

if bugs_found:
    print("✗ Concatenation handling issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Concatenated values test passed")

# Test 3: Test with Unicode and special strings
print("\n[TEST 3] Testing Unicode and special strings...")
bugs_found = []

# Unicode variations that look like valid values
unicode_tricks = [
    "LІNEAR",  # Using Cyrillic І instead of I
    "LINEΑR",  # Using Greek Α instead of A  
    "ΝONE",    # Using Greek Ν instead of N
    "LAMΒDA",  # Using Greek Β instead of B
    "LINEAR\u200b",  # Zero-width space at end
    "\u200bLINEAR",  # Zero-width space at start
    "LIN\u200bEAR",  # Zero-width space in middle
]

for value in unicode_tricks:
    for validator, name in [(validate_growth_type, "growth_type"),
                           (validate_replicate_to, "replicate_to"),
                           (validate_validator_type, "validator_type")]:
        try:
            result = validator(value)
            # Check if it's actually a valid value
            if result in ["LINEAR", "NONE", "SSM_DOCUMENT", "JSON_SCHEMA", "LAMBDA"]:
                bugs_found.append(f"{name} validator accepted Unicode trick '{repr(value)}' as '{result}'")
        except ValueError:
            pass  # Expected

if bugs_found:
    print("✗ Unicode handling issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Unicode and special strings test passed")

# Test 4: Test class instantiation with validator properties
print("\n[TEST 4] Testing class instantiation with validators...")
bugs_found = []

try:
    # Test creating a Validators object with invalid Type
    validator_obj = appconfig.Validators(
        Content="test content",
        Type="INVALID_TYPE"
    )
    # Try to convert to dict which should trigger validation
    try:
        dict_repr = validator_obj.to_dict()
        bugs_found.append(f"Validators class accepted invalid Type 'INVALID_TYPE'")
    except ValueError:
        pass  # Expected
except Exception as e:
    pass  # May not have to_dict method or may validate on creation

try:
    # Test creating DeploymentStrategy with invalid GrowthType
    strategy = appconfig.DeploymentStrategy(
        "TestStrategy",
        DeploymentDurationInMinutes=1.0,
        GrowthFactor=1.0,
        GrowthType="INVALID",
        Name="test",
        ReplicateTo="NONE"
    )
    # Check if validation happens
    try:
        dict_repr = strategy.to_dict()
        bugs_found.append(f"DeploymentStrategy accepted invalid GrowthType 'INVALID'")
    except ValueError:
        pass  # Expected
except Exception as e:
    pass  # Expected if validation happens on creation

if bugs_found:
    print("✗ Class instantiation issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Class instantiation test passed")

# Test 5: Test with very long strings
print("\n[TEST 5] Testing with very long strings...")
bugs_found = []

# Test with strings that start with valid values
long_strings = [
    "LINEAR" + "x" * 1000,
    "NONE" + "y" * 1000,
    "JSON_SCHEMA" + "z" * 1000,
    "x" * 1000 + "LINEAR",
    "y" * 1000 + "NONE",
]

for value in long_strings:
    for validator, name in [(validate_growth_type, "growth_type"),
                           (validate_replicate_to, "replicate_to"),
                           (validate_validator_type, "validator_type")]:
        try:
            result = validator(value)
            bugs_found.append(f"{name} validator accepted long string containing valid value: '{value[:50]}...' - returned: {result}")
        except ValueError:
            pass  # Expected

if bugs_found:
    print("✗ Long string handling issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Long string test passed")

# Test 6: Test mutation safety - ensure validators don't modify their constants
print("\n[TEST 6] Testing mutation safety of validator constants...")
bugs_found = []

# Get the original values
import troposphere.validators.appconfig as module

# Store original tuples
orig_growth = ("LINEAR",)
orig_replicate = ("NONE", "SSM_DOCUMENT")
orig_validator = ("JSON_SCHEMA", "LAMBDA")

# Run validators multiple times
for _ in range(100):
    try:
        validate_growth_type("INVALID")
    except ValueError:
        pass
    try:
        validate_replicate_to("INVALID")
    except ValueError:
        pass
    try:
        validate_validator_type("INVALID")
    except ValueError:
        pass

# Check if constants are still the same
# We need to check the actual module constants
if hasattr(module, 'VALID_GROWTH_TYPES'):
    if module.VALID_GROWTH_TYPES != orig_growth:
        bugs_found.append(f"VALID_GROWTH_TYPES was mutated: {module.VALID_GROWTH_TYPES}")

if not bugs_found:
    print("✓ Mutation safety test passed")
else:
    print("✗ Mutation safety issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")

# Test 7: Test with valid values but wrong validator
print("\n[TEST 7] Cross-validator value testing...")
bugs_found = []

# Test growth_type validator with replicate_to values
for value in ["NONE", "SSM_DOCUMENT"]:
    try:
        result = validate_growth_type(value)
        bugs_found.append(f"growth_type validator accepted replicate_to value '{value}' - returned: {result}")
    except ValueError:
        pass  # Expected

# Test replicate_to validator with growth_type values  
for value in ["LINEAR"]:
    try:
        result = validate_replicate_to(value)
        bugs_found.append(f"replicate_to validator accepted growth_type value '{value}' - returned: {result}")
    except ValueError:
        pass  # Expected

# Test validator_type with other values
for value in ["LINEAR", "NONE", "SSM_DOCUMENT"]:
    try:
        result = validate_validator_type(value)
        bugs_found.append(f"validator_type validator accepted '{value}' - returned: {result}")
    except ValueError:
        pass  # Expected

if bugs_found:
    print("✗ Cross-validator issues found:")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("✓ Cross-validator test passed")

# Summary
print("\n" + "=" * 70)
if bugs_found:
    print(f"❌ Found potential issues - {len(bugs_found)} problems detected")
else:
    print("✅ All advanced property tests PASSED!")

print("\nAdvanced properties tested:")
print("1. Substring handling: Validators reject substrings of valid values")
print("2. Concatenation: Validators reject concatenated valid values")
print("3. Unicode tricks: Validators handle Unicode lookalikes correctly")
print("4. Class instantiation: Classes use validators correctly")
print("5. Long strings: Validators handle very long strings")
print("6. Mutation safety: Validator constants remain unchanged")
print("7. Cross-validator: Each validator only accepts its own values")