#!/usr/bin/env python3
"""Property-based tests for troposphere.redshiftserverless module."""

import troposphere.redshiftserverless as rs
from hypothesis import assume, given, strategies as st, settings
import pytest
import math


# Test 1: Integer validator property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet='0123456789-+', min_size=1, max_size=20),
    st.booleans()
))
def test_integer_validator_consistency(value):
    """The integer() validator should either:
    1. Return a value that int() can process, or
    2. Raise a ValueError
    """
    try:
        result = rs.integer(value)
        # If it succeeds, the result should be convertible to int
        assert int(result) is not None
    except ValueError:
        # This is expected for invalid inputs
        pass
    except Exception as e:
        # Any other exception is a bug
        pytest.fail(f"Unexpected exception: {e}")


# Test 2: Boolean validator completeness
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=-10, max_value=10),
    st.text(max_size=10),
    st.none()
))
def test_boolean_validator_documented_values(value):
    """Boolean validator should accept only documented values:
    True: [True, 1, "1", "true", "True"]
    False: [False, 0, "0", "false", "False"]
    """
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    try:
        result = rs.boolean(value)
        # If it succeeds, value must be in one of the documented lists
        assert value in true_values or value in false_values
        # And result must be a boolean
        assert isinstance(result, bool)
        # And it should map correctly
        if value in true_values:
            assert result is True
        else:
            assert result is False
    except ValueError:
        # ValueError should only be raised for undocumented values
        assert value not in true_values and value not in false_values


# Test 3: ConfigParameter to_dict/from_dict round-trip
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: not x.startswith('_')),
    st.text(min_size=0, max_size=100)
)
def test_config_parameter_round_trip(key, value):
    """to_dict and from_dict should be inverse operations for ConfigParameter."""
    # Create original
    cp1 = rs.ConfigParameter(ParameterKey=key, ParameterValue=value)
    
    # Convert to dict
    dict1 = cp1.to_dict()
    
    # Create from dict
    cp2 = rs.ConfigParameter.from_dict('TestTitle', dict1)
    
    # Convert back to dict
    dict2 = cp2.to_dict()
    
    # They should be equal
    assert dict1 == dict2
    assert dict1['ParameterKey'] == key
    assert dict1['ParameterValue'] == value


# Test 4: Endpoint with integer Port validation
@given(
    st.text(min_size=1, max_size=100),
    st.one_of(
        st.integers(min_value=1, max_value=65535),
        st.text(alphabet='0123456789', min_size=1, max_size=5).map(int)
    )
)
def test_endpoint_port_integer_validation(address, port):
    """Endpoint should properly validate Port using integer validator."""
    endpoint = rs.Endpoint(Address=address, Port=port)
    result = endpoint.to_dict()
    
    # Port should be in the dict
    assert 'Port' in result
    # Port should be convertible to int and match original
    assert int(result['Port']) == int(port)


# Test 5: Nested property serialization
@given(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    st.integers(min_value=1, max_value=65535),
    st.lists(
        st.builds(
            rs.ConfigParameter,
            ParameterKey=st.text(min_size=1, max_size=50),
            ParameterValue=st.text(min_size=0, max_size=50)
        ),
        max_size=3
    )
)
def test_workgroup_nested_properties(title, base_capacity, config_params):
    """Workgroup with nested properties should serialize correctly."""
    wg = rs.Workgroup(
        title,
        WorkgroupName=f"wg-{title}",
        BaseCapacity=base_capacity,
        ConfigParameters=config_params
    )
    
    # Convert to dict
    wg_dict = wg.to_dict()
    
    # Check structure
    assert 'Type' in wg_dict
    assert wg_dict['Type'] == 'AWS::RedshiftServerless::Workgroup'
    assert 'Properties' in wg_dict
    
    props = wg_dict['Properties']
    assert props['WorkgroupName'] == f"wg-{title}"
    assert props['BaseCapacity'] == base_capacity
    
    # ConfigParameters should be serialized as list of dicts
    if config_params:
        assert 'ConfigParameters' in props
        assert len(props['ConfigParameters']) == len(config_params)
        for i, cp in enumerate(config_params):
            assert props['ConfigParameters'][i] == cp.to_dict()


# Test 6: Boolean validator edge cases
@given(st.one_of(
    st.just("TRUE"),
    st.just("FALSE"),
    st.just("yes"),
    st.just("no"),
    st.just("T"),
    st.just("F"),
    st.just("1.0"),
    st.just("0.0")
))
def test_boolean_validator_edge_cases(value):
    """Test edge cases that might seem boolean-like but aren't accepted."""
    try:
        result = rs.boolean(value)
        # If it doesn't raise, it's a bug - these values aren't documented as valid
        pytest.fail(f"boolean({value!r}) should have raised ValueError but returned {result}")
    except ValueError:
        # Expected behavior
        pass


# Test 7: Integer validator with float strings
@given(st.text(alphabet='0123456789.', min_size=3, max_size=10).filter(lambda x: '.' in x))
def test_integer_validator_float_strings(value):
    """Integer validator should handle float strings consistently."""
    try:
        result = rs.integer(value)
        # If it succeeds, int(value) should work
        int_value = int(float(value))
        # The result when passed to int should give same value
        assert int(result) == int_value
    except ValueError:
        # This is acceptable
        pass


# Test 8: Max/Min capacity validation in Workgroup
@given(
    st.integers(min_value=8, max_value=512),
    st.integers(min_value=8, max_value=512)
)
def test_workgroup_capacity_values(base_capacity, max_capacity):
    """Test that base and max capacity are handled correctly."""
    assume(base_capacity <= max_capacity)  # Logical constraint
    
    wg = rs.Workgroup(
        'TestWG',
        WorkgroupName='test-workgroup',
        BaseCapacity=base_capacity,
        MaxCapacity=max_capacity
    )
    
    wg_dict = wg.to_dict()
    props = wg_dict['Properties']
    
    # Values should be preserved
    assert props['BaseCapacity'] == base_capacity
    assert props['MaxCapacity'] == max_capacity


if __name__ == '__main__':
    # Run with pytest for better output
    pytest.main([__file__, '-v'])