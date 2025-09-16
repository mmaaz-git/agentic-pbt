#!/usr/bin/env python3
"""Run property-based tests for troposphere.applicationinsights."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import traceback
from hypothesis import given, strategies as st, settings, assume, example
import string

# Import modules to test
import troposphere.applicationinsights as appinsights
from troposphere import validators


def run_test(test_func, test_name):
    """Run a single property-based test and report results."""
    print(f"\nTesting: {test_name}")
    print("-" * 60)
    
    try:
        # Run the test with Hypothesis
        test_func()
        print(f"✅ PASSED: {test_name}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Boolean validator
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1, max_size=10),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none()
))
@settings(max_examples=100)
def test_boolean_validator(value):
    """Test boolean validator accepts documented values."""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        result = validators.boolean(value)
        assert result is True, f"Expected True for {value}, got {result}"
    elif value in valid_false:
        result = validators.boolean(value)
        assert result is False, f"Expected False for {value}, got {result}"
    else:
        try:
            result = validators.boolean(value)
            assert False, f"Should have raised ValueError for {value}, got {result}"
        except ValueError:
            pass  # Expected


# Test 2: Integer validator with edge cases
@given(st.one_of(
    st.integers(),
    st.text(alphabet=string.digits, min_size=1, max_size=10),
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none()
))
@settings(max_examples=100)
def test_integer_validator(value):
    """Test integer validator."""
    try:
        int(value)
        # If int() succeeds, validator should succeed
        result = validators.integer(value)
        assert result == value
    except (ValueError, TypeError):
        # If int() fails, validator should fail
        try:
            validators.integer(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected


# Test 3: Application required properties
@given(
    resource_group=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20)
)
@settings(max_examples=50)
def test_application_required_property(resource_group):
    """Test Application requires ResourceGroupName."""
    # Should succeed with required property
    app = appinsights.Application(
        "TestApp",
        ResourceGroupName=resource_group
    )
    app._validate_props()
    assert app.ResourceGroupName == resource_group
    
    # Test missing required property
    app2 = appinsights.Application("TestApp2")
    try:
        app2._validate_props()
        assert False, "Should have raised ValueError for missing ResourceGroupName"
    except ValueError as e:
        assert "ResourceGroupName" in str(e)


# Test 4: LogPattern integer rank validation
@given(
    pattern=st.text(min_size=1, max_size=20),
    name=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    rank_value=st.one_of(
        st.integers(),
        st.text(alphabet=string.digits, min_size=1, max_size=5),
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5)
    )
)
@settings(max_examples=50)
def test_logpattern_rank_validation(pattern, name, rank_value):
    """Test LogPattern rank accepts integers."""
    try:
        int(rank_value)
        # Should succeed with valid integer
        log_pattern = appinsights.LogPattern(
            Pattern=pattern,
            PatternName=name,
            Rank=rank_value
        )
        assert log_pattern.Rank == rank_value
    except (ValueError, TypeError):
        # Should fail with invalid integer
        try:
            log_pattern = appinsights.LogPattern(
                Pattern=pattern,
                PatternName=name,
                Rank=rank_value
            )
            # The property assignment happens in __init__, check if it raised
            assert False, f"Should have raised error for non-integer rank: {rank_value}"
        except (ValueError, TypeError):
            pass  # Expected


# Test 5: Round-trip serialization
@given(
    alarm_name=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
    severity=st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
@settings(max_examples=50)
def test_alarm_serialization_roundtrip(alarm_name, severity):
    """Test Alarm to_dict/from_dict round-trip."""
    kwargs = {"AlarmName": alarm_name}
    if severity is not None:
        kwargs["Severity"] = severity
    
    # Create alarm
    alarm1 = appinsights.Alarm(**kwargs)
    
    # Convert to dict and back
    alarm_dict = alarm1.to_dict()
    alarm2 = appinsights.Alarm._from_dict(**alarm_dict)
    
    # Properties should match
    assert alarm2.AlarmName == alarm_name
    if severity is not None:
        assert alarm2.Severity == severity
    
    # Dicts should be equal
    assert alarm1.to_dict() == alarm2.to_dict()


# Test 6: Title validation rules
@given(st.text(min_size=0, max_size=20))
@settings(max_examples=100)
def test_title_validation(title):
    """Test Application title must be alphanumeric."""
    # Check if title is valid (alphanumeric only)
    is_valid = bool(title and title.isalnum())
    
    try:
        app = appinsights.Application(
            title,
            ResourceGroupName="TestGroup"
        )
        # validate_title is called in __init__ if title is present
        if title and not is_valid:
            assert False, f"Invalid title {title!r} was accepted"
    except ValueError as e:
        if is_valid:
            assert False, f"Valid title {title!r} was rejected: {e}"
        assert "not alphanumeric" in str(e)


# Main execution
def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Property-Based Testing for troposphere.applicationinsights")
    print("=" * 60)
    
    tests = [
        (test_boolean_validator, "Boolean validator"),
        (test_integer_validator, "Integer validator"),
        (test_application_required_property, "Application required properties"),
        (test_logpattern_rank_validation, "LogPattern rank validation"),
        (test_alarm_serialization_roundtrip, "Alarm serialization round-trip"),
        (test_title_validation, "Title validation rules"),
    ]
    
    results = []
    for test_func, test_name in tests:
        passed = run_test(test_func, test_name)
        results.append((test_name, passed))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    failed_count = len(results) - passed_count
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed_count} passed, {failed_count} failed out of {len(results)} tests")
    
    return failed_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)