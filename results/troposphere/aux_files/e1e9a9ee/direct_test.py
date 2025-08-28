#!/usr/bin/env python3
"""Direct test runner to execute tests."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import hypothesis and run a simple test
from hypothesis import given, strategies as st
from troposphere import licensemanager, validators

# Test boolean validator
print("Testing boolean validator...")
test_values = [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]
for val in test_values:
    result1 = validators.boolean(val)
    result2 = validators.boolean(result1)
    assert result1 == result2
    print(f"  {val} -> {result1} (idempotent: OK)")

# Test invalid boolean values
print("\nTesting invalid boolean values...")
invalid_values = ["yes", "no", 2, -1, None, [], {}]
for val in invalid_values:
    try:
        validators.boolean(val)
        print(f"  ERROR: {val} should have raised ValueError but didn't!")
    except ValueError:
        print(f"  {val} -> ValueError (as expected)")

# Test integer validator
print("\nTesting integer validator...")
valid_ints = [0, 1, -1, "42", "-100", 999999]
for val in valid_ints:
    result = validators.integer(val)
    int_val = int(result)
    print(f"  {val} -> {result} -> int({int_val})")

# Test invalid integers
print("\nTesting invalid integer values...")
invalid_ints = ["abc", "", None, [], {}, "1.5"]
for val in invalid_ints:
    try:
        validators.integer(val)
        print(f"  ERROR: {val} should have raised ValueError but didn't!")
    except (ValueError, TypeError):
        print(f"  {val} -> ValueError/TypeError (as expected)")

# Test title validation
print("\nTesting title validation...")
valid_titles = ["Test123", "MyResource", "AWS2020"]
for title in valid_titles:
    grant = licensemanager.Grant(title)
    print(f"  '{title}' -> Valid title")

invalid_titles = ["test-123", "my_resource", "has spaces", "123@aws", ""]
for title in invalid_titles:
    try:
        grant = licensemanager.Grant(title)
        print(f"  ERROR: '{title}' should have raised ValueError but didn't!")
    except ValueError as e:
        print(f"  '{title}' -> ValueError: {e}")

# Test required properties
print("\nTesting required properties...")
try:
    license_obj = licensemanager.License("TestLicense")
    license_obj.to_dict()
    print("  ERROR: License without required properties should have raised ValueError!")
except ValueError as e:
    print(f"  License without required props -> ValueError: {e}")

# Test equality
print("\nTesting object equality...")
grant1 = licensemanager.Grant("TestGrant", GrantName="test", Status="ACTIVE")
grant2 = licensemanager.Grant("TestGrant", GrantName="test", Status="ACTIVE")
grant3 = licensemanager.Grant("DifferentGrant", GrantName="test", Status="ACTIVE")

assert grant1 == grant2
print("  Same properties -> Equal: OK")
assert grant1 != grant3
print("  Different title -> Not Equal: OK")

# Test to_dict/from_dict round-trip
print("\nTesting to_dict/from_dict round-trip...")
grant = licensemanager.Grant(
    "RoundTripTest",
    GrantName="MyGrant",
    HomeRegion="us-east-1",
    Status="ACTIVE",
    Principals=["arn:aws:iam::123456789012:role/MyRole"],
    AllowedOperations=["CreateGrant", "RetireGrant"]
)

dict_repr = grant.to_dict()
props = dict_repr.get("Properties", {})
grant2 = licensemanager.Grant.from_dict("RoundTripTest", props)

assert grant == grant2
print("  Round-trip successful: Objects are equal")

print("\n✅ All basic tests passed!")
print("\nNow running property-based tests with Hypothesis...")

# Import hypothesis for property tests
from hypothesis import given, strategies as st, settings
import traceback

# Property test 1: Boolean validator with all valid values
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
@settings(max_examples=100)
def test_boolean_idempotence(val):
    result1 = validators.boolean(val)
    result2 = validators.boolean(result1)
    assert result1 == result2

try:
    test_boolean_idempotence()
    print("✅ Boolean idempotence property test passed")
except Exception as e:
    print(f"❌ Boolean idempotence test failed: {e}")
    traceback.print_exc()

# Property test 2: Integer validator
@given(st.integers())
@settings(max_examples=100)
def test_integer_validator(val):
    result = validators.integer(val)
    int_val = int(result)
    assert isinstance(int_val, int)

try:
    test_integer_validator()
    print("✅ Integer validator property test passed")
except Exception as e:
    print(f"❌ Integer validator test failed: {e}")
    traceback.print_exc()

# Property test 3: Grant equality
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    grant_name=st.text(min_size=1),
    status=st.text(min_size=1)
)
@settings(max_examples=100)
def test_grant_equality(title, grant_name, status):
    grant1 = licensemanager.Grant(title, GrantName=grant_name, Status=status)
    grant2 = licensemanager.Grant(title, GrantName=grant_name, Status=status)
    assert grant1 == grant2
    assert not (grant1 != grant2)

try:
    test_grant_equality()
    print("✅ Grant equality property test passed")
except Exception as e:
    print(f"❌ Grant equality test failed: {e}")
    traceback.print_exc()

print("\n🎉 All property-based tests completed!")