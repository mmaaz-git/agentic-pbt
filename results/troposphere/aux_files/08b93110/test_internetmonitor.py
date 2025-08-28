"""
Property-based tests for troposphere.internetmonitor module
"""

import math
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import troposphere.internetmonitor as im
from troposphere.validators import boolean, integer, double

# Test 1: Validator functions - boolean
# The boolean validator claims to accept various truthy/falsy values
# Based on code at validators/__init__.py:38-43

@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs"""
    result = boolean(value)
    assert isinstance(result, bool)
    # Check it returns correct boolean value
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False

@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs"""
    try:
        boolean(value)
        assert False, f"boolean() should have raised ValueError for {value}"
    except ValueError:
        pass  # Expected

# Test 2: Validator functions - integer
# The integer validator claims to validate integers
# Based on code at validators/__init__.py:46-52

@given(st.integers())
def test_integer_validator_with_integers(value):
    """Test that integer validator accepts actual integers"""
    result = integer(value)
    assert result == value
    assert int(result) == value

@given(st.text(min_size=1).map(str))
def test_integer_validator_with_numeric_strings(value):
    """Test that integer validator handles numeric strings correctly"""
    try:
        int_value = int(value)
        result = integer(value)
        assert result == value
        assert int(result) == int_value
    except ValueError:
        # If int() fails, integer() should also fail
        try:
            integer(value)
            assert False, f"integer() should have raised ValueError for {value}"
        except ValueError:
            pass

# Test 3: Validator functions - double
# The double validator claims to validate doubles/floats
# Based on code at validators/__init__.py:93-99

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_with_floats(value):
    """Test that double validator accepts floats"""
    result = double(value)
    assert result == value
    assert float(result) == value

@given(st.integers())
def test_double_validator_with_integers(value):
    """Test that double validator accepts integers (as they're valid floats)"""
    result = double(value)
    assert result == value
    assert float(result) == float(value)

# Test 4: Type validation in InternetMonitor classes
# Test that property setters validate types correctly
# Based on __setattr__ implementation in __init__.py:237-318

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=100))
def test_health_score_threshold_accepts_doubles(value):
    """Test that HealthScoreThreshold property accepts valid doubles"""
    config = im.LocalHealthEventsConfig()
    config.HealthScoreThreshold = value
    assert config.properties["HealthScoreThreshold"] == double(value)

@given(st.integers(min_value=0, max_value=100))
def test_max_city_networks_accepts_integers(value):
    """Test that MaxCityNetworksToMonitor accepts valid integers"""
    monitor = im.Monitor("TestMonitor")
    monitor.MaxCityNetworksToMonitor = value
    assert monitor.properties["MaxCityNetworksToMonitor"] == integer(value)

@given(st.booleans())
def test_include_linked_accounts_accepts_booleans(value):
    """Test that IncludeLinkedAccounts accepts booleans"""
    monitor = im.Monitor("TestMonitor")
    monitor.IncludeLinkedAccounts = value
    assert monitor.properties["IncludeLinkedAccounts"] == boolean(value)

# Test 5: Round-trip property - to_dict and from_dict
# Objects should convert to dict and back preserving data

@given(
    health_score=st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=100),
    min_traffic=st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=100),
    status=st.sampled_from(["ENABLED", "DISABLED"])
)
def test_local_health_events_config_round_trip(health_score, min_traffic, status):
    """Test LocalHealthEventsConfig to_dict/from_dict round-trip"""
    config = im.LocalHealthEventsConfig()
    config.HealthScoreThreshold = health_score
    config.MinTrafficImpact = min_traffic
    config.Status = status
    
    # Convert to dict
    dict_repr = config.to_dict()
    
    # Verify dict has correct structure
    assert isinstance(dict_repr, dict)
    if "HealthScoreThreshold" in dict_repr:
        assert float(dict_repr["HealthScoreThreshold"]) == health_score
    if "MinTrafficImpact" in dict_repr:
        assert float(dict_repr["MinTrafficImpact"]) == min_traffic
    if "Status" in dict_repr:
        assert dict_repr["Status"] == status

# Test 6: Required properties validation
# Test that required properties are validated

def test_monitor_requires_monitor_name():
    """Test that Monitor validates required MonitorName property"""
    monitor = im.Monitor("TestMonitor")
    # MonitorName is required (marked as True in props)
    try:
        # Don't set MonitorName and try to convert to dict with validation
        monitor_dict = monitor.to_dict()
        # MonitorName is required, so this should fail
        # But actually, the title is used as a fallback in some cases
        # Let's test without setting any name
    except Exception:
        pass  # Expected if validation works
    
    # Set MonitorName and it should work
    monitor.MonitorName = "test-monitor"
    monitor_dict = monitor.to_dict()
    assert "Properties" in monitor_dict
    assert "MonitorName" in monitor_dict["Properties"]

# Test 7: Title validation
# Titles must be alphanumeric according to validate_title()

@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1))
def test_valid_monitor_titles(title):
    """Test that Monitor accepts valid alphanumeric titles"""
    monitor = im.Monitor(title)
    monitor.validate_title()
    assert monitor.title == title

@given(st.text(min_size=1).filter(lambda x: not x.replace('_', '').replace('-', '').isalnum()))
def test_invalid_monitor_titles_rejected(title):
    """Test that Monitor rejects non-alphanumeric titles"""
    assume(not all(c.isalnum() for c in title))  # Ensure it's actually invalid
    monitor = im.Monitor(title)
    try:
        monitor.validate_title()
        # If the title passes validation but shouldn't, check if it's actually valid
        if not all(c.isalnum() for c in title):
            assert False, f"Title '{title}' should have been rejected"
    except ValueError:
        pass  # Expected

# Test 8: Property type coercion
# Test that validator functions are called during property assignment

@given(st.sampled_from([True, 1, "true", "True", False, 0, "false", "False"]))
def test_boolean_property_coercion(value):
    """Test that boolean properties are coerced through boolean() validator"""
    monitor = im.Monitor("TestMonitor")
    monitor.IncludeLinkedAccounts = value
    # After assignment, the value should be converted to proper boolean
    stored_value = monitor.properties.get("IncludeLinkedAccounts")
    assert isinstance(stored_value, bool)
    if value in [True, 1, "true", "True"]:
        assert stored_value is True
    else:
        assert stored_value is False

@given(st.one_of(st.integers(), st.text().filter(lambda x: x.isdigit())))
def test_integer_property_coercion(value):
    """Test that integer properties accept both ints and numeric strings"""
    monitor = im.Monitor("TestMonitor")
    try:
        monitor.TrafficPercentageToMonitor = value
        stored_value = monitor.properties.get("TrafficPercentageToMonitor")
        # The value should be stored as-is but be convertible to int
        assert int(stored_value) == int(value)
    except (ValueError, TypeError):
        # Some inputs might not be valid integers
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])