#!/usr/bin/env python
"""Simple test runner for finspace module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import troposphere.finspace as finspace

# Test 1: Invalid title should be rejected
print("Test 1: Testing invalid title rejection...")
try:
    # Test with a title containing special characters
    env = finspace.Environment("test-invalid", Name="TestEnv")
    print("ERROR: Invalid title 'test-invalid' was accepted but should have been rejected!")
except ValueError as e:
    if 'not alphanumeric' in str(e):
        print("PASS: Invalid title correctly rejected")
    else:
        print(f"ERROR: Wrong error message: {e}")

# Test 2: Valid title should be accepted
print("\nTest 2: Testing valid title acceptance...")
try:
    env = finspace.Environment("ValidTitle123", Name="TestEnv")
    print("PASS: Valid title accepted")
except Exception as e:
    print(f"ERROR: Valid title rejected: {e}")

# Test 3: Name property is required
print("\nTest 3: Testing required Name property...")
try:
    env = finspace.Environment("TestEnv")
    env.to_dict()
    print("ERROR: Environment without Name was accepted")
except ValueError as e:
    if "required" in str(e).lower():
        print("PASS: Missing Name property correctly detected")
    else:
        print(f"ERROR: Wrong error message: {e}")

# Test 4: Round-trip to_dict/from_dict
print("\nTest 4: Testing round-trip conversion...")
env1 = finspace.Environment("Test", Name="TestEnv", Description="Test Description")
dict1 = env1.to_dict()
props = dict1.get('Properties', {})
env2 = finspace.Environment.from_dict("Test", props)
dict2 = env2.to_dict()
if dict1 == dict2:
    print("PASS: Round-trip conversion works correctly")
else:
    print("ERROR: Round-trip conversion failed")
    print(f"Dict1: {dict1}")
    print(f"Dict2: {dict2}")

# Test 5: Equality testing
print("\nTest 5: Testing equality...")
env1 = finspace.Environment("Test", Name="TestEnv")
env2 = finspace.Environment("Test", Name="TestEnv")
if env1 == env2:
    print("PASS: Equal environments are equal")
else:
    print("ERROR: Equal environments are not equal")

# Test 6: Hash consistency
print("\nTest 6: Testing hash consistency...")
env1 = finspace.Environment("Test", Name="TestEnv")
env2 = finspace.Environment("Test", Name="TestEnv")
if hash(env1) == hash(env2):
    print("PASS: Equal environments have same hash")
else:
    print("ERROR: Equal environments have different hashes")

print("\n=== Test Summary ===")
print("All basic tests completed. Running Hypothesis tests...")

# Now run some hypothesis tests
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=255).filter(lambda s: not s.isalnum()))
def test_invalid_titles(title):
    """Test that non-alphanumeric titles are rejected"""
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    try:
        env = finspace.Environment(title, Name="TestEnv")
        # If we get here, check if it's actually invalid
        if not valid_names.match(title):
            raise AssertionError(f"BUG FOUND: Invalid title '{title}' was accepted but should have been rejected")
    except ValueError as e:
        if 'not alphanumeric' not in str(e):
            raise AssertionError(f"Wrong error message: {e}")

# Run the hypothesis test
print("\nRunning property-based test for title validation...")
try:
    test_invalid_titles()
    print("PASS: Title validation property holds")
except AssertionError as e:
    print(f"FAILURE: {e}")

print("\n=== All tests completed ===")