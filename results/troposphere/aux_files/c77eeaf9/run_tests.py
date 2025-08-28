#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
from troposphere import appflow, validators
from troposphere import AWSProperty, AWSObject
import traceback


def run_test(test_func, test_name):
    """Run a single test and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        # Run the test with many examples
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except Exception as e:
        print(f"✗ {test_name} FAILED")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Boolean validator
@settings(max_examples=100, verbosity=Verbosity.normal)
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1, max_size=5),
    st.integers(min_value=-100, max_value=100),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none()
))
def test_boolean_validator(value):
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        result = validators.boolean(value)
        assert result is True, f"boolean({value!r}) should return True, got {result}"
    elif value in false_values:
        result = validators.boolean(value)
        assert result is False, f"boolean({value!r}) should return False, got {result}"
    else:
        try:
            result = validators.boolean(value)
            # If we get here, it should have raised ValueError
            assert False, f"boolean({value!r}) should raise ValueError but returned {result}"
        except ValueError:
            pass  # Expected


# Test 2: Integer validator
@settings(max_examples=100, verbosity=Verbosity.normal)
@given(st.one_of(
    st.integers(),
    st.text(min_size=1, max_size=5),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none()
))
def test_integer_validator(value):
    try:
        # Try to convert to int first
        int_value = int(value)
        # If that succeeds, validator should also succeed
        result = validators.integer(value)
        assert int(result) == int_value
    except (ValueError, TypeError):
        # If int() fails, validator should also fail
        try:
            result = validators.integer(value)
            assert False, f"integer({value!r}) should raise ValueError but returned {result}"
        except ValueError:
            pass  # Expected


# Test 3: Required field validation
@settings(max_examples=50, verbosity=Verbosity.normal)
@given(
    st.text(min_size=1, max_size=10).filter(lambda x: x.isalnum()),
    st.text(min_size=1, max_size=20)
)
def test_required_field_validation(field_name, field_value):
    # Create a custom class with a required field
    class TestProp(AWSProperty):
        props = {
            field_name: (str, True)  # Required string field
        }
    
    # Test 1: Without setting the field, validation should fail
    obj1 = TestProp()
    try:
        obj1.to_dict(validation=True)
        assert False, f"Should have raised ValueError for missing required field {field_name}"
    except ValueError as e:
        assert field_name in str(e), f"Error message should mention {field_name}"
    
    # Test 2: With the field set, validation should succeed
    obj2 = TestProp()
    setattr(obj2, field_name, field_value)
    result = obj2.to_dict(validation=True)
    assert field_name in result, f"Result should contain {field_name}"
    assert result[field_name] == field_value


# Test 4: Type validation
@settings(max_examples=50, verbosity=Verbosity.normal)
@given(
    st.one_of(st.text(), st.integers(), st.booleans(), st.none())
)
def test_type_validation(value):
    # Test with AmplitudeConnectorProfileCredentials which requires string fields
    obj = appflow.AmplitudeConnectorProfileCredentials()
    
    # ApiKey is a required string field
    if isinstance(value, str):
        obj.ApiKey = value
        assert obj.ApiKey == value
    else:
        try:
            obj.ApiKey = value
            # Check if it was converted or accepted
            if not isinstance(obj.ApiKey, str):
                assert False, f"ApiKey should be string, but accepted {type(value)}"
        except TypeError:
            pass  # Expected for non-string types


# Test 5: Invalid property rejection
@settings(max_examples=50, verbosity=Verbosity.normal)
@given(
    st.text(min_size=5, max_size=20).filter(lambda x: x.isalnum() and x not in ['title', 'template']),
    st.one_of(st.text(), st.integers())
)
def test_invalid_property(prop_name, value):
    # Make sure we're testing a property that doesn't exist
    if prop_name not in appflow.Connector.props:
        obj = appflow.Connector(title="TestConnector")
        try:
            setattr(obj, prop_name, value)
            # Check if it was silently ignored or accepted
            if not hasattr(obj, prop_name):
                assert False, f"Property {prop_name} was silently ignored"
        except AttributeError as e:
            assert prop_name in str(e)  # Expected


# Main execution
if __name__ == "__main__":
    print("Starting property-based testing of troposphere.appflow")
    print("="*60)
    
    results = []
    
    tests = [
        (test_boolean_validator, "Boolean Validator Property"),
        (test_integer_validator, "Integer Validator Property"),
        (test_required_field_validation, "Required Field Validation"),
        (test_type_validation, "Type Validation Property"),
        (test_invalid_property, "Invalid Property Rejection"),
    ]
    
    for test_func, test_name in tests:
        result = run_test(test_func, test_name)
        results.append((test_name, result))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed > 0:
        sys.exit(1)