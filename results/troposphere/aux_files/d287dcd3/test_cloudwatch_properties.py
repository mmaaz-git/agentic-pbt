#!/usr/bin/env python3
"""Property-based tests for troposphere.cloudwatch module using Hypothesis."""

import string
from hypothesis import given, strategies as st, assume, settings
import pytest
import cloudwatch


# Define the valid values as constants
VALID_UNITS = [
    "Seconds", "Microseconds", "Milliseconds", "Bytes", "Kilobytes",
    "Megabytes", "Gigabytes", "Terabytes", "Bits", "Kilobits",
    "Megabits", "Gigabits", "Terabits", "Percent", "Count",
    "Bytes/Second", "Kilobytes/Second", "Megabytes/Second",
    "Gigabytes/Second", "Terabytes/Second", "Bits/Second",
    "Kilobits/Second", "Megabits/Second", "Gigabits/Second",
    "Terabits/Second", "Count/Second", "None"
]

VALID_TREAT_MISSING_DATA = ["breaching", "notBreaching", "ignore", "missing"]


# Property 1: Round-trip property for validators
@given(st.sampled_from(VALID_UNITS))
def test_validate_unit_round_trip(unit):
    """Valid units should be returned unchanged by validate_unit."""
    result = cloudwatch.validate_unit(unit)
    assert result == unit, f"validate_unit modified the input: {unit} -> {result}"


@given(st.sampled_from(VALID_TREAT_MISSING_DATA))
def test_validate_treat_missing_data_round_trip(value):
    """Valid TreatMissingData values should be returned unchanged."""
    result = cloudwatch.validate_treat_missing_data(value)
    assert result == value, f"validate_treat_missing_data modified: {value} -> {result}"


# Property 2: Invalid values should raise ValueError
@given(st.text(min_size=1))
def test_validate_unit_rejects_invalid(text):
    """Invalid units should raise ValueError."""
    assume(text not in VALID_UNITS)
    with pytest.raises(ValueError, match="Unit must be one of"):
        cloudwatch.validate_unit(text)


@given(st.text(min_size=1))
def test_validate_treat_missing_data_rejects_invalid(text):
    """Invalid TreatMissingData values should raise ValueError."""
    assume(text not in VALID_TREAT_MISSING_DATA)
    with pytest.raises(ValueError, match="TreatMissingData must be one of"):
        cloudwatch.validate_treat_missing_data(text)


# Property 3: Case sensitivity
@given(st.sampled_from(VALID_UNITS))
def test_validate_unit_case_sensitive(unit):
    """validate_unit should be case-sensitive."""
    # Test lowercase version
    lower_unit = unit.lower()
    if lower_unit != unit and lower_unit not in VALID_UNITS:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(lower_unit)
    
    # Test uppercase version
    upper_unit = unit.upper()
    if upper_unit != unit and upper_unit not in VALID_UNITS:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(upper_unit)


# Property 4: Whitespace sensitivity
@given(st.sampled_from(VALID_UNITS), st.text(alphabet=" \t\n", min_size=1, max_size=5))
def test_validate_unit_whitespace_sensitive(unit, whitespace):
    """validate_unit should not trim whitespace."""
    # Add whitespace before
    with_prefix = whitespace + unit
    if with_prefix != unit:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(with_prefix)
    
    # Add whitespace after
    with_suffix = unit + whitespace
    if with_suffix != unit:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(with_suffix)


# Property 5: Type validators
@given(st.booleans())
def test_boolean_validator_accepts_bools(value):
    """boolean validator should accept all boolean values."""
    assert cloudwatch.boolean(value) == True


@given(st.one_of(st.integers(), st.floats(), st.text(), st.none()))
def test_boolean_validator_rejects_non_bools(value):
    """boolean validator should reject non-boolean values."""
    if not isinstance(value, bool):
        assert cloudwatch.boolean(value) == False


@given(st.integers())
def test_integer_validator_accepts_ints(value):
    """integer validator should accept all integers."""
    assert cloudwatch.integer(value) == True


@given(st.one_of(st.floats(), st.text(), st.booleans(), st.none()))
def test_integer_validator_rejects_non_ints(value):
    """integer validator should reject non-integer values."""
    # Note: booleans are subclass of int in Python, so they might pass
    if not isinstance(value, int) or isinstance(value, bool):
        assert cloudwatch.integer(value) == False


@given(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False)))
def test_double_validator_accepts_numbers(value):
    """double validator should accept integers and floats."""
    assert cloudwatch.double(value) == True


@given(st.one_of(st.text(), st.booleans(), st.none()))
def test_double_validator_rejects_non_numbers(value):
    """double validator should reject non-numeric values."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        assert cloudwatch.double(value) == False


# Property 6: Special values handling
def test_validate_unit_none_string_vs_none():
    """'None' string should be valid but Python None should not."""
    # String 'None' should work
    assert cloudwatch.validate_unit('None') == 'None'
    
    # Python None should fail
    with pytest.raises(ValueError):
        cloudwatch.validate_unit(None)


# Property 7: Empty string handling
def test_validators_reject_empty_string():
    """Validators should reject empty strings."""
    with pytest.raises(ValueError):
        cloudwatch.validate_unit('')
    
    with pytest.raises(ValueError):
        cloudwatch.validate_treat_missing_data('')


# Property 8: Metamorphic property - case variations
@given(st.sampled_from(VALID_UNITS))
def test_unit_case_variations_consistency(unit):
    """Different case variations should behave consistently."""
    original_valid = True
    lower_valid = unit.lower() in VALID_UNITS
    upper_valid = unit.upper() in VALID_UNITS
    
    # If original is valid, check the behavior of variations
    if not lower_valid:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(unit.lower())
    else:
        assert cloudwatch.validate_unit(unit.lower()) == unit.lower()
    
    if not upper_valid:
        with pytest.raises(ValueError):
            cloudwatch.validate_unit(unit.upper())
    else:
        assert cloudwatch.validate_unit(unit.upper()) == unit.upper()


# Property 9: Class instantiation with required properties
@given(st.text(min_size=1), st.text(min_size=1))
def test_metric_dimension_instantiation(name, value):
    """MetricDimension should accept Name and Value parameters."""
    md = cloudwatch.MetricDimension(Name=name, Value=value)
    assert md.Name == name
    assert md.Value == value


@given(st.text(min_size=1), st.text(min_size=1))
def test_metric_instantiation(metric_name, namespace):
    """Metric should accept MetricName and Namespace parameters."""
    m = cloudwatch.Metric(MetricName=metric_name, Namespace=namespace)
    assert m.MetricName == metric_name
    assert m.Namespace == namespace


# Property 10: Alarm instantiation with required properties
@given(st.text(min_size=1), st.text(min_size=1), st.integers(min_value=1, max_value=100))
def test_alarm_instantiation(name, comparison_operator, evaluation_periods):
    """Alarm should accept required parameters."""
    a = cloudwatch.Alarm(
        name,
        ComparisonOperator=comparison_operator,
        EvaluationPeriods=evaluation_periods
    )
    assert a.name == name
    assert a.ComparisonOperator == comparison_operator
    assert a.EvaluationPeriods == evaluation_periods


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))