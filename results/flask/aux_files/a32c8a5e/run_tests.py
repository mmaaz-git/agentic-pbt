#!/usr/bin/env python3
"""Standalone test runner for troposphere.bedrock property tests"""

import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
from troposphere.validators import boolean, integer, double
from troposphere import bedrock


def run_test(test_func, test_name):
    """Run a single property test and report results"""
    print(f"\nTesting: {test_name}")
    print("-" * 60)
    
    try:
        test_func()
        print(f"✓ PASSED")
        return True
    except Exception as e:
        print(f"✗ FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Boolean validator with valid inputs
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_valid(value):
    result = boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True, f"Expected True for {value!r}, got {result!r}"
    else:
        assert result is False, f"Expected False for {value!r}, got {result!r}"


# Test 2: Boolean validator with invalid inputs
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.one_of(
    st.none(),
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(allow_nan=False),
    st.lists(st.integers())
))
def test_boolean_invalid(value):
    try:
        result = boolean(value)
        # If we get here without exception, it's a bug
        raise AssertionError(f"Expected ValueError for {value!r}, but got {result!r}")
    except ValueError:
        pass  # Expected


# Test 3: Integer validator with valid integers
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.integers())
def test_integer_valid(value):
    result = integer(value)
    assert result == value
    assert int(result) == value


# Test 4: Integer validator with string integers
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.text(min_size=1).filter(lambda x: x.strip().lstrip('-').isdigit() if x.strip() else False))
def test_integer_string_valid(value):
    result = integer(value)
    assert result == value
    int(result)  # Should not raise


# Test 5: Double validator with floats
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_float_valid(value):
    result = double(value)
    assert result == value
    assert float(result) == value


# Test 6: Double validator with integers
@settings(max_examples=100, verbosity=Verbosity.quiet)
@given(st.integers())
def test_double_integer_valid(value):
    result = double(value)
    assert result == value
    assert float(result) == value


# Test 7: Title validation - valid alphanumeric
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1))
def test_title_valid(title):
    try:
        obj = bedrock.Agent(title=title, AgentName="TestAgent")
        assert obj.title == title
    except ValueError as e:
        raise AssertionError(f"Valid title {title!r} was rejected: {e}")


# Test 8: Title validation - invalid non-alphanumeric
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.text(min_size=1).filter(lambda x: any(not c.isalnum() for c in x)))
def test_title_invalid(title):
    try:
        obj = bedrock.Agent(title=title, AgentName="TestAgent")
        raise AssertionError(f"Invalid title {title!r} was accepted")
    except ValueError as e:
        if "not alphanumeric" not in str(e):
            raise AssertionError(f"Unexpected error message: {e}")


# Test 9: Empty title validation
def test_title_empty():
    for title in ["", None]:
        try:
            obj = bedrock.Agent(title=title, AgentName="TestAgent")
            raise AssertionError(f"Empty/None title {title!r} was accepted")
        except ValueError:
            pass  # Expected


# Test 10: AWS Object property type validation
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.text())
def test_aws_object_string_property(value):
    obj = bedrock.S3Identifier()
    obj.S3BucketName = value
    assert obj.S3BucketName == value


# Test 11: AWS Object wrong type rejection
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.integers())
def test_aws_object_wrong_type(value):
    obj = bedrock.S3Identifier()
    try:
        obj.S3BucketName = value  # Expects string, giving integer
        raise AssertionError(f"Integer {value} was accepted for string property")
    except TypeError as e:
        assert "expected" in str(e).lower()


# Test 12: Boolean property with validator
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]))
def test_boolean_property(value):
    obj = bedrock.Agent(title="TestAgent", AgentName="TestAgent")
    obj.AutoPrepare = value
    expected = boolean(value)
    assert obj.AutoPrepare == expected


# Test 13: to_dict preserves values
@settings(max_examples=50, verbosity=Verbosity.quiet)
@given(st.text(min_size=1), st.text(min_size=1))
def test_to_dict_preserves(bucket, key):
    obj = bedrock.S3Identifier()
    obj.S3BucketName = bucket
    obj.S3ObjectKey = key
    
    result = obj.to_dict()
    assert result.get("S3BucketName") == bucket
    assert result.get("S3ObjectKey") == key


def main():
    """Run all tests and report results"""
    print("=" * 60)
    print("Property-Based Testing for troposphere.bedrock")
    print("=" * 60)
    
    tests = [
        (test_boolean_valid, "Boolean validator - valid inputs"),
        (test_boolean_invalid, "Boolean validator - invalid inputs"),
        (test_integer_valid, "Integer validator - valid integers"),
        (test_integer_string_valid, "Integer validator - string integers"),
        (test_double_float_valid, "Double validator - floats"),
        (test_double_integer_valid, "Double validator - integers"),
        (test_title_valid, "Title validation - valid alphanumeric"),
        (test_title_invalid, "Title validation - invalid non-alphanumeric"),
        (test_title_empty, "Title validation - empty/None"),
        (test_aws_object_string_property, "AWS Object - string property"),
        (test_aws_object_wrong_type, "AWS Object - type validation"),
        (test_boolean_property, "Boolean property with validator"),
        (test_to_dict_preserves, "to_dict preserves values"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)