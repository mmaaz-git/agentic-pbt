#!/usr/bin/env python3
"""Property-based tests for troposphere.applicationsignals module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import math
from hypothesis import given, strategies as st, assume, settings
from troposphere import applicationsignals
from troposphere.validators import boolean, double, integer


# Test validator functions
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator handles valid inputs correctly."""
    result = boolean(value)
    assert isinstance(result, bool)
    # Check that truthy values return True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Check that falsy values return False
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.floats(), st.none(), st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs."""
    try:
        result = boolean(value)
        # If it didn't raise, check if the value was actually valid
        assert value in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"]
    except ValueError:
        pass  # Expected behavior


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=57), min_size=1),  # digit strings
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid numeric inputs."""
    # Skip strings that would overflow float
    if isinstance(value, str) and len(value) > 300:
        assume(False)
    
    result = double(value)
    # The validator should return the value unchanged if it's valid
    assert result == value
    # Verify it can be converted to float
    float(result)


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: not x.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_double_validator_invalid_inputs(value):
    """Test that double validator raises ValueError for invalid inputs."""
    try:
        result = double(value)
        # If it didn't raise, verify the value can actually be converted to float
        float(value)
    except (ValueError, TypeError):
        pass  # Expected behavior


@given(st.one_of(
    st.integers(),
    st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=57), min_size=1),  # digit strings
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer inputs."""
    # Skip strings that would overflow int
    if isinstance(value, str) and len(value) > 4000:
        assume(False)
    
    result = integer(value)
    # The validator should return the value unchanged if it's valid
    assert result == value
    # Verify it can be converted to int
    int(result)


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer()),
    st.text(min_size=1).filter(lambda x: not x.lstrip('-+').isdigit()),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_invalid_inputs(value):
    """Test that integer validator raises ValueError for invalid inputs."""
    try:
        result = integer(value)
        # If it didn't raise, verify the value can actually be converted to int
        int(value)
    except (ValueError, TypeError):
        pass  # Expected behavior


# Test round-trip property for objects
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=20),
    lookback=st.integers(min_value=1, max_value=10000),
    duration=st.integers(min_value=1, max_value=365),
    duration_unit=st.sampled_from(["DAY", "MONTH"]),
    reason=st.text(max_size=100)
)
def test_round_trip_property(name, lookback, duration, duration_unit, reason):
    """Test that to_dict and from_dict are inverse operations."""
    # Create a BurnRateConfiguration object
    burn_rate = applicationsignals.BurnRateConfiguration(
        LookBackWindowMinutes=lookback
    )
    
    # Convert to dict
    dict_repr = burn_rate.to_dict()
    
    # Recreate from dict
    new_burn_rate = applicationsignals.BurnRateConfiguration.from_dict(None, dict_repr)
    
    # They should be equal
    assert burn_rate == new_burn_rate
    assert burn_rate.to_dict() == new_burn_rate.to_dict()
    
    # Test with Window object
    window = applicationsignals.Window(
        Duration=duration,
        DurationUnit=duration_unit
    )
    dict_repr = window.to_dict()
    new_window = applicationsignals.Window.from_dict(None, dict_repr)
    assert window == new_window
    
    # Test with ExclusionWindow (has optional properties)
    excl_window = applicationsignals.ExclusionWindow(
        Window=window,
        Reason=reason if reason else None
    )
    dict_repr = excl_window.to_dict()
    new_excl_window = applicationsignals.ExclusionWindow.from_dict(None, dict_repr)
    assert excl_window == new_excl_window


@given(
    title=st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=20),
    name=st.text(min_size=1, max_size=50),
    description=st.text(max_size=200)
)
def test_required_property_validation(title, name, description):
    """Test that objects validate required properties correctly."""
    # ServiceLevelObjective requires Name property
    # Should succeed with required property
    slo = applicationsignals.ServiceLevelObjective(
        title=title,
        Name=name
    )
    slo.to_dict()  # This triggers validation
    
    # Should fail without required property
    try:
        slo_invalid = applicationsignals.ServiceLevelObjective(title=title)
        slo_invalid.to_dict()  # This should raise ValueError
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # Optional properties should work fine
    slo_with_optional = applicationsignals.ServiceLevelObjective(
        title=title,
        Name=name,
        Description=description
    )
    slo_with_optional.to_dict()


@given(st.text(min_size=1))
def test_title_validation(title):
    """Test that title validation follows the alphanumeric pattern."""
    import re
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    
    try:
        # Try to create an object with the given title
        obj = applicationsignals.ServiceLevelObjective(
            title=title,
            Name="TestName"
        )
        # If it succeeded, the title should match the pattern
        assert valid_pattern.match(title) is not None
    except ValueError as e:
        # If it failed, the title should NOT match the pattern
        assert valid_pattern.match(title) is None
        assert "alphanumeric" in str(e)


# Test property type checking
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=20),
    lookback_value=st.one_of(
        st.integers(min_value=1, max_value=10000),
        st.text(min_size=1),
        st.floats(),
        st.none()
    )
)
def test_property_type_checking(title, lookback_value):
    """Test that property type checking works correctly."""
    try:
        burn_rate = applicationsignals.BurnRateConfiguration(
            LookBackWindowMinutes=lookback_value
        )
        # If successful, should be convertible to int
        int(lookback_value)
    except (ValueError, TypeError):
        # Expected for invalid types
        pass


# Test that Discovery has no required properties
@given(title=st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=20))
def test_discovery_no_properties(title):
    """Test that Discovery object works with no properties."""
    discovery = applicationsignals.Discovery(title)
    dict_repr = discovery.to_dict()
    # Should have Type but no Properties (or empty Properties)
    assert "Type" in dict_repr
    assert dict_repr["Type"] == "AWS::ApplicationSignals::Discovery"
    if "Properties" in dict_repr:
        assert dict_repr["Properties"] == {}


# Test Goal object with double values
@given(
    attainment=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    warning=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
)
def test_goal_double_properties(attainment, warning):
    """Test that Goal object handles double properties correctly."""
    goal = applicationsignals.Goal(
        AttainmentGoal=attainment,
        WarningThreshold=warning
    )
    dict_repr = goal.to_dict()
    
    # Values should be preserved
    if "AttainmentGoal" in dict_repr:
        assert dict_repr["AttainmentGoal"] == attainment
    if "WarningThreshold" in dict_repr:
        assert dict_repr["WarningThreshold"] == warning


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])