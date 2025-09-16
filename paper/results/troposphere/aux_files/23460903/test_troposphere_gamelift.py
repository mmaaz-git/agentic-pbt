#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Property-based tests for troposphere.gamelift module"""

from hypothesis import given, assume, strategies as st, settings
import pytest
import sys
import os

# Add the virtual environment's site-packages to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.gamelift as gamelift
from troposphere.validators import integer, double, boolean


# Test 1: Port range invariants - FromPort should be <= ToPort
@given(
    from_port=st.integers(min_value=1, max_value=65535),
    to_port=st.integers(min_value=1, max_value=65535)
)
def test_connection_port_range_invariant(from_port, to_port):
    """Test that ConnectionPortRange accepts any from/to port combination"""
    # The class should either validate FromPort <= ToPort or accept any values
    port_range = gamelift.ConnectionPortRange(
        FromPort=from_port,
        ToPort=to_port
    )
    
    # Verify the properties are set correctly
    result = port_range.to_dict()
    assert result['FromPort'] == from_port
    assert result['ToPort'] == to_port


@given(
    from_port=st.integers(min_value=1, max_value=65535),
    to_port=st.integers(min_value=1, max_value=65535),
    protocol=st.sampled_from(['TCP', 'UDP'])
)
def test_container_port_range_invariant(from_port, to_port, protocol):
    """Test that ContainerPortRange accepts any from/to port combination"""
    port_range = gamelift.ContainerPortRange(
        FromPort=from_port,
        ToPort=to_port,
        Protocol=protocol
    )
    
    result = port_range.to_dict()
    assert result['FromPort'] == from_port
    assert result['ToPort'] == to_port
    assert result['Protocol'] == protocol


# Test 2: Validator functions - integer validator
@given(st.integers())
def test_integer_validator_valid_integers(x):
    """Test that integer validator accepts all valid integers"""
    result = integer(x)
    assert result == x
    # Should be convertible back to int
    assert int(result) == x


@given(st.text(min_size=1).filter(lambda x: not x.strip().lstrip('-').isdigit()))
def test_integer_validator_invalid_strings(x):
    """Test that integer validator rejects non-integer strings"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(x)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_invalid_types(x):
    """Test that integer validator rejects invalid types"""
    with pytest.raises(ValueError, match="is not a valid integer"):
        integer(x)


# Test 3: Validator functions - double validator
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_valid_floats(x):
    """Test that double validator accepts all valid floats"""
    result = double(x)
    assert result == x
    assert float(result) == x


@given(st.integers())
def test_double_validator_valid_integers(x):
    """Test that double validator accepts integers (as they're valid doubles)"""
    result = double(x)
    assert result == x
    assert float(result) == float(x)


@given(st.text(min_size=1).filter(
    lambda x: not any(x.strip().startswith(p) and x.strip()[len(p):].replace('.', '').lstrip('-').isdigit() 
                      for p in ['', '-', '+'])
))
def test_double_validator_invalid_strings(x):
    """Test that double validator rejects non-numeric strings"""
    with pytest.raises(ValueError, match="is not a valid double"):
        double(x)


# Test 4: Validator functions - boolean validator
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_validator_true_values(x):
    """Test that boolean validator correctly identifies true values"""
    result = boolean(x)
    assert result is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_validator_false_values(x):
    """Test that boolean validator correctly identifies false values"""
    result = boolean(x)
    assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["true", "True", "false", "False", "1", "0"]),
    st.none(),
    st.floats()
))
def test_boolean_validator_invalid_values(x):
    """Test that boolean validator rejects invalid values"""
    with pytest.raises(ValueError):
        boolean(x)


# Test 5: IpPermission port range properties
@given(
    from_port=st.integers(min_value=1, max_value=65535),
    to_port=st.integers(min_value=1, max_value=65535),
    ip_range=st.sampled_from(["0.0.0.0/0", "10.0.0.0/8", "192.168.0.0/16"]),
    protocol=st.sampled_from(["tcp", "udp", "icmp", "-1"])
)
def test_ip_permission_creation(from_port, to_port, ip_range, protocol):
    """Test IpPermission accepts all valid port combinations"""
    permission = gamelift.IpPermission(
        FromPort=from_port,
        ToPort=to_port,
        IpRange=ip_range,
        Protocol=protocol
    )
    
    result = permission.to_dict()
    assert result['FromPort'] == from_port
    assert result['ToPort'] == to_port
    assert result['IpRange'] == ip_range
    assert result['Protocol'] == protocol


# Test 6: LocationCapacity invariants
@given(
    desired=st.integers(min_value=0, max_value=1000),
    min_size=st.integers(min_value=0, max_value=1000),
    max_size=st.integers(min_value=0, max_value=1000)
)
def test_location_capacity_creation(desired, min_size, max_size):
    """Test LocationCapacity accepts any size combination"""
    capacity = gamelift.LocationCapacity(
        DesiredEC2Instances=desired,
        MinSize=min_size,
        MaxSize=max_size
    )
    
    result = capacity.to_dict()
    assert result['DesiredEC2Instances'] == desired
    assert result['MinSize'] == min_size
    assert result['MaxSize'] == max_size


# Test 7: Property type validation - should reject wrong types
@given(st.text())
def test_connection_port_range_type_validation(text_value):
    """Test that ConnectionPortRange validates integer types for ports"""
    # FromPort and ToPort must be integers
    if not text_value.lstrip('-').isdigit():
        with pytest.raises((TypeError, ValueError)):
            gamelift.ConnectionPortRange(
                FromPort=text_value,
                ToPort=1024
            )


# Test 8: GameProperty key-value pairs
@given(
    key=st.text(min_size=1, max_size=100),
    value=st.text(min_size=0, max_size=1000)
)
def test_game_property_creation(key, value):
    """Test GameProperty accepts any key-value strings"""
    prop = gamelift.GameProperty(
        Key=key,
        Value=value
    )
    
    result = prop.to_dict()
    assert result['Key'] == key
    assert result['Value'] == value


# Test 9: Test that to_dict() is idempotent
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
    value=st.text(min_size=1, max_size=100)
)
def test_game_property_to_dict_idempotent(name, value):
    """Test that calling to_dict() multiple times returns the same result"""
    prop = gamelift.GameProperty(Key=name, Value=value)
    
    dict1 = prop.to_dict()
    dict2 = prop.to_dict()
    dict3 = prop.to_dict()
    
    assert dict1 == dict2 == dict3
    assert dict1 is not dict2  # Should create new dict each time


# Test 10: ContainerEnvironment properties
@given(
    name=st.text(min_size=1, max_size=100),
    value=st.text(min_size=0, max_size=1000)
)
def test_container_environment_creation(name, value):
    """Test ContainerEnvironment accepts any name-value strings"""
    env = gamelift.ContainerEnvironment(
        Name=name,
        Value=value
    )
    
    result = env.to_dict()
    assert result['Name'] == name
    assert result['Value'] == value


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])