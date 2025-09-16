#!/usr/bin/env python3
"""Property-based tests for troposphere.opsworks module."""

import json
import sys
import os

# Add the virtual environment site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import pytest

# Import the modules to test
from troposphere import opsworks
from troposphere.validators import opsworks as opsworks_validators
from troposphere.validators import boolean, double, integer, json_checker, mutually_exclusive


# Test 1: validate_volume_type only accepts valid volume types
@given(st.text())
def test_validate_volume_type_accepts_only_valid_types(volume_type):
    """validate_volume_type should only accept 'standard', 'io1', or 'gp2'."""
    valid_types = ("standard", "io1", "gp2")
    
    if volume_type in valid_types:
        # Should return the same value
        assert opsworks_validators.validate_volume_type(volume_type) == volume_type
    else:
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            opsworks_validators.validate_volume_type(volume_type)
        assert "must be one of" in str(exc_info.value)


# Test 2: validate_volume_configuration mutual exclusion property
@given(
    volume_type=st.sampled_from(["standard", "io1", "gp2", None]),
    iops=st.one_of(st.none(), st.integers(min_value=1, max_value=20000)),
    mount_point=st.text(min_size=1, max_size=100),
)
def test_validate_volume_configuration_iops_constraint(volume_type, iops, mount_point):
    """Test that Iops is required iff VolumeType is 'io1'."""
    
    class MockVolumeConfig:
        def __init__(self):
            self.properties = {}
            if volume_type is not None:
                self.properties["VolumeType"] = volume_type
            if iops is not None:
                self.properties["Iops"] = iops
            self.properties["MountPoint"] = mount_point
    
    config = MockVolumeConfig()
    
    # Expected behavior from the code
    should_raise = False
    if volume_type == "io1" and iops is None:
        should_raise = True  # io1 requires Iops
    elif volume_type != "io1" and volume_type is not None and iops is not None:
        should_raise = True  # non-io1 cannot have Iops
    
    if should_raise:
        with pytest.raises(ValueError):
            opsworks_validators.validate_volume_configuration(config)
    else:
        # Should not raise
        opsworks_validators.validate_volume_configuration(config)


# Test 3: json_checker round-trip property
@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(-1000, 1000),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=100),
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=5),
                st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5),
            ),
            max_leaves=50,
        ),
        max_size=10,
    )
)
def test_json_checker_dict_to_string_round_trip(data):
    """json_checker should correctly handle dict -> JSON string conversion."""
    # Convert dict to JSON string
    json_string = json_checker(data)
    
    # Should be a valid JSON string
    assert isinstance(json_string, str)
    
    # Should be parseable back to the original dict
    parsed = json.loads(json_string)
    assert parsed == data


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(-1000, 1000),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=100),
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=5),
                st.dictionaries(st.text(min_size=1, max_size=10), children, max_size=5),
            ),
            max_leaves=50,
        ),
        max_size=10,
    )
)
def test_json_checker_string_validation(data):
    """json_checker should validate JSON strings properly."""
    # Create a valid JSON string
    valid_json = json.dumps(data)
    
    # Should accept and return the valid JSON string
    result = json_checker(valid_json)
    assert result == valid_json
    
    # Should be parseable
    assert json.loads(result) == data


@given(st.text())
def test_json_checker_invalid_json_string(text):
    """json_checker should reject invalid JSON strings."""
    # Skip if the text happens to be valid JSON
    try:
        json.loads(text)
        return  # Skip this test case as it's valid JSON
    except:
        pass
    
    # Should raise an error for invalid JSON
    with pytest.raises((json.JSONDecodeError, ValueError)):
        json_checker(text)


# Test 4: boolean validator invariants
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"]),
))
def test_boolean_accepts_valid_inputs(value):
    """boolean() should accept documented valid inputs."""
    expected = True if value in [True, 1, "1", "true", "True"] else False
    assert boolean(value) == expected


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
))
def test_boolean_rejects_invalid_inputs(value):
    """boolean() should reject invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)


# Test 5: validate_data_source_type
@given(st.text())
def test_validate_data_source_type_accepts_only_valid_types(data_type):
    """validate_data_source_type should only accept specific types."""
    valid_types = (
        "AutoSelectOpsworksMysqlInstance",
        "OpsworksMysqlInstance",
        "RdsDbInstance",
    )
    
    if data_type in valid_types:
        assert opsworks_validators.validate_data_source_type(data_type) == data_type
    else:
        with pytest.raises(ValueError) as exc_info:
            opsworks_validators.validate_data_source_type(data_type)
        assert "must be one of" in str(exc_info.value)


# Test 6: validate_stack VpcId/DefaultSubnetId dependency
@given(
    vpc_id=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    default_subnet_id=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
def test_validate_stack_vpc_dependency(vpc_id, default_subnet_id):
    """validate_stack should enforce VpcId requires DefaultSubnetId."""
    
    class MockStack:
        def __init__(self):
            self.properties = {}
            if vpc_id is not None:
                self.properties["VpcId"] = vpc_id
            if default_subnet_id is not None:
                self.properties["DefaultSubnetId"] = default_subnet_id
    
    stack = MockStack()
    
    # Should raise if VpcId is present but DefaultSubnetId is not
    if vpc_id is not None and default_subnet_id is None:
        with pytest.raises(ValueError) as exc_info:
            opsworks_validators.validate_stack(stack)
        assert "DefaultSubnetId" in str(exc_info.value)
    else:
        # Should not raise
        opsworks_validators.validate_stack(stack)


# Test 7: integer validator
@given(st.one_of(
    st.integers(),
    st.text(min_size=1).map(lambda x: str(x) if x.isdigit() or (x[0] == '-' and x[1:].isdigit()) else x),
))
def test_integer_validator(value):
    """integer() should validate integers correctly."""
    try:
        int(value)
        valid = True
    except (ValueError, TypeError):
        valid = False
    
    if valid:
        assert integer(value) == value
    else:
        with pytest.raises(ValueError):
            integer(value)


# Test 8: double validator
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(min_size=1),
))
def test_double_validator(value):
    """double() should validate doubles correctly."""
    try:
        float(value)
        valid = True
    except (ValueError, TypeError):
        valid = False
    
    if valid:
        assert double(value) == value
    else:
        with pytest.raises(ValueError):
            double(value)


# Test 9: mutually_exclusive function
@given(
    properties=st.dictionaries(
        keys=st.sampled_from(["A", "B", "C", "D"]),
        values=st.one_of(st.none(), st.text(min_size=1), st.integers()),
        min_size=0,
        max_size=4,
    ),
    conditionals=st.lists(
        st.sampled_from(["A", "B", "C", "D"]),
        min_size=2,
        max_size=4,
        unique=True,
    ),
)
def test_mutually_exclusive(properties, conditionals):
    """mutually_exclusive should enforce that at most one conditional is set."""
    from troposphere import NoValue
    
    # Replace None with NoValue to match the actual implementation
    clean_props = {}
    for k, v in properties.items():
        if v is not None:
            clean_props[k] = v
        else:
            clean_props[k] = NoValue
    
    # Count how many conditionals are present (and not NoValue)
    count = 0
    for c in conditionals:
        if c in clean_props and clean_props[c] != NoValue:
            count += 1
    
    if count > 1:
        with pytest.raises(ValueError) as exc_info:
            mutually_exclusive("TestClass", clean_props, conditionals)
        assert "only one of the following" in str(exc_info.value)
    else:
        result = mutually_exclusive("TestClass", clean_props, conditionals)
        assert result == count


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])