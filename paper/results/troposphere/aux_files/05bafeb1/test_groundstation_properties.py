#!/usr/bin/env python3
"""Property-based tests for troposphere.groundstation module"""

import json
from hypothesis import given, strategies as st, assume
import pytest
import math
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import the modules we're testing
from troposphere.groundstation import IntegerRange, Bandwidth, Frequency
from troposphere.validators import json_checker, double, integer, boolean
from troposphere import AWSHelperFn


# Test 1: IntegerRange invariant - Maximum should be >= Minimum when both are set
@given(
    min_val=st.integers(),
    max_val=st.integers()
)
def test_integer_range_invariant(min_val, max_val):
    """Test that IntegerRange allows setting any integer values for min/max"""
    # Create an IntegerRange with specific min/max values
    int_range = IntegerRange()
    
    # Set properties directly
    int_range.properties = {
        "Minimum": min_val,
        "Maximum": max_val
    }
    
    # The class should accept any values without validation
    # This tests that the class doesn't enforce Maximum >= Minimum
    assert int_range.properties.get("Minimum") == min_val
    assert int_range.properties.get("Maximum") == max_val
    
    # Check if to_dict works regardless of the values
    result = int_range.to_dict()
    if min_val is not None:
        assert result.get("Minimum") == min_val
    if max_val is not None:
        assert result.get("Maximum") == max_val


# Test 2: json_checker round-trip property for dict -> JSON string -> dict
@given(
    # Generate valid JSON-serializable dicts
    test_dict=st.dictionaries(
        keys=st.text(min_size=1, alphabet=st.characters(blacklist_categories=['Cs'])),
        values=st.recursive(
            st.one_of(
                st.none(),
                st.booleans(), 
                st.integers(min_value=-1e10, max_value=1e10),
                st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
                st.text(max_size=100, alphabet=st.characters(blacklist_categories=['Cs']))
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=10),
                st.dictionaries(
                    st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=['Cs'])),
                    children,
                    max_size=10
                )
            ),
            max_leaves=50
        ),
        max_size=20
    )
)
def test_json_checker_dict_round_trip(test_dict):
    """Test that json_checker correctly converts dicts to JSON strings and back"""
    # json_checker should convert dict to JSON string
    json_string = json_checker(test_dict)
    
    # Result should be a string
    assert isinstance(json_string, str)
    
    # We should be able to parse it back to get the original dict
    parsed_dict = json.loads(json_string)
    assert parsed_dict == test_dict


# Test 3: json_checker accepts valid JSON strings
@given(
    test_dict=st.dictionaries(
        keys=st.text(min_size=1, alphabet=st.characters(blacklist_categories=['Cs'])),
        values=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(max_size=100, alphabet=st.characters(blacklist_categories=['Cs']))
        ),
        max_size=10
    )
)
def test_json_checker_string_validation(test_dict):
    """Test that json_checker validates JSON strings correctly"""
    # Create a valid JSON string
    json_string = json.dumps(test_dict)
    
    # json_checker should accept and return the valid JSON string
    result = json_checker(json_string)
    assert result == json_string
    
    # Verify the string is still valid JSON
    parsed = json.loads(result)
    assert parsed == test_dict


# Test 4: double validator accepts valid float values
@given(
    value=st.one_of(
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.integers(min_value=-1000000, max_value=1000000)
    )
)
def test_double_validator_accepts_valid_floats(value):
    """Test that double validator accepts valid numeric values"""
    result = double(value)
    assert result == value
    # Verify the value can be converted to float
    assert isinstance(float(result), float)


# Test 5: integer validator accepts valid integer values
@given(value=st.integers(min_value=-10**10, max_value=10**10))
def test_integer_validator_accepts_valid_integers(value):
    """Test that integer validator accepts valid integer values"""
    result = integer(value)
    assert result == value
    # Verify the value can be converted to int
    assert isinstance(int(result), int)


# Test 6: boolean validator mappings
@given(
    true_value=st.sampled_from([True, 1, "1", "true", "True"]),
    false_value=st.sampled_from([False, 0, "0", "false", "False"])
)
def test_boolean_validator_mappings(true_value, false_value):
    """Test that boolean validator maps values correctly according to spec"""
    # Test true values
    assert boolean(true_value) is True
    
    # Test false values  
    assert boolean(false_value) is False


# Test 7: Test Bandwidth and Frequency classes with double values
@given(
    value=st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=1e9),
    units=st.sampled_from(["Hz", "kHz", "MHz", "GHz"])
)
def test_bandwidth_frequency_double_values(value, units):
    """Test that Bandwidth and Frequency accept double values as specified"""
    # Test Bandwidth
    bandwidth = Bandwidth()
    bandwidth.properties = {
        "Value": value,
        "Units": units
    }
    result = bandwidth.to_dict()
    assert result["Value"] == value
    assert result["Units"] == units
    
    # Test Frequency  
    frequency = Frequency()
    frequency.properties = {
        "Value": value,
        "Units": units
    }
    result = frequency.to_dict()
    assert result["Value"] == value
    assert result["Units"] == units


# Test 8: IntegerRange with edge cases
@given(value=st.integers())
def test_integer_range_single_value(value):
    """Test IntegerRange when Maximum equals Minimum"""
    int_range = IntegerRange()
    int_range.properties = {
        "Minimum": value,
        "Maximum": value
    }
    result = int_range.to_dict()
    assert result["Minimum"] == value
    assert result["Maximum"] == value