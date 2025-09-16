#!/usr/bin/env python3
"""Focused tests to find actual bugs in troposphere.neptune."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import json
import math
from troposphere import neptune
from troposphere import validators

# Test 1: Check if equality handles different property orders
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    props=st.dictionaries(
        st.sampled_from(["DBClusterIdentifier", "BackupRetentionPeriod", "DBPort", "KmsKeyId", "EngineVersion"]),
        st.text(min_size=1),
        min_size=2,
        max_size=5
    )
)
def test_equality_property_order(title, props):
    """Test if equality is independent of property order."""
    # Create two clusters with same properties in different order
    cluster1 = neptune.DBCluster(title)
    cluster2 = neptune.DBCluster(title)
    
    # Set properties in original order
    for key, value in props.items():
        if key == "BackupRetentionPeriod" or key == "DBPort":
            value = 10  # Use integer for these
        setattr(cluster1, key, value)
    
    # Set properties in reverse order
    for key in reversed(list(props.keys())):
        value = props[key]
        if key == "BackupRetentionPeriod" or key == "DBPort":
            value = 10  # Use integer for these
        setattr(cluster2, key, value)
    
    # They should be equal regardless of property order
    assert cluster1 == cluster2
    assert hash(cluster1) == hash(cluster2)


# Test 2: Test validator behavior with string representations of special floats
@given(
    value=st.sampled_from(["inf", "-inf", "nan", "infinity", "-infinity", "NaN", "Infinity", "-Infinity"])
)
def test_double_validator_string_special_values(value):
    """Test if double validator handles string representations of special float values."""
    result = validators.double(value)
    
    # Check if it was accepted and what it returns
    float_val = float(result)
    
    if value.lower() in ["nan"]:
        assert math.isnan(float_val)
    elif value.lower() in ["inf", "infinity"]:
        assert math.isinf(float_val) and float_val > 0
    elif value.lower() in ["-inf", "-infinity"]:
        assert math.isinf(float_val) and float_val < 0


# Test 3: Test integer validator with string representations of large numbers
@given(
    value=st.one_of(
        st.just(str(2**63)),  # Just beyond signed 64-bit
        st.just(str(2**64)),  # Unsigned 64-bit boundary
        st.just(str(2**128)), # Very large
        st.just(str(-2**63 - 1)), # Just beyond negative signed 64-bit
        st.integers(min_value=-10**20, max_value=10**20).map(str)
    )
)
def test_integer_validator_large_numbers(value):
    """Test integer validator with very large numbers as strings."""
    result = validators.integer(value)
    assert result == value
    # Should be convertible back to int
    int_val = int(result)
    assert str(int_val) == value


# Test 4: Test boolean validator case sensitivity
@given(
    value=st.sampled_from(["TRUE", "FALSE", "True", "False", "true", "false", "tRuE", "fAlSe"])
)
def test_boolean_validator_case_variations(value):
    """Test if boolean validator handles all case variations correctly."""
    if value.lower() == "true":
        expected = True
    elif value.lower() == "false":  
        expected = False
    else:
        # Mixed case not in the validator's list
        with pytest.raises(ValueError):
            validators.boolean(value)
        return
    
    result = validators.boolean(value)
    assert result == expected


# Test 5: Test from_dict with extra/unknown properties
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    extra_props=st.dictionaries(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=5, max_size=20),
        st.text(),
        min_size=1,
        max_size=3
    )
)
def test_from_dict_unknown_properties(title, extra_props):
    """Test if from_dict rejects unknown properties."""
    # Create a valid dict first
    valid_props = {
        "DBInstanceClass": "db.t3.medium"
    }
    
    # Add extra unknown properties
    all_props = {**valid_props, **extra_props}
    
    # Should raise an error for unknown properties
    with pytest.raises(AttributeError, match="does not have a .* property"):
        neptune.DBInstance.from_dict(title, all_props)


# Test 6: Test DBCluster with contradictory restore options
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    use_latest=st.booleans(),
    restore_time=st.text(min_size=1)
)
def test_contradictory_restore_options(title, use_latest, restore_time):
    """Test DBCluster with both UseLatestRestorableTime and RestoreToTime set."""
    cluster = neptune.DBCluster(
        title,
        UseLatestRestorableTime=use_latest,
        RestoreToTime=restore_time
    )
    
    # Both properties should be allowed simultaneously (AWS will validate)
    result = cluster.to_dict()
    assert result["Properties"]["UseLatestRestorableTime"] == use_latest
    assert result["Properties"]["RestoreToTime"] == restore_time


# Test 7: Test edge case with empty list properties
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1)
)
def test_empty_list_properties(title):
    """Test that empty lists are handled correctly."""
    cluster = neptune.DBCluster(
        title,
        AvailabilityZones=[],
        EnableCloudwatchLogsExports=[],
        VpcSecurityGroupIds=[]
    )
    
    result = cluster.to_dict()
    assert result["Properties"]["AvailabilityZones"] == []
    assert result["Properties"]["EnableCloudwatchLogsExports"] == []
    assert result["Properties"]["VpcSecurityGroupIds"] == []
    
    # Test round-trip
    cluster2 = neptune.DBCluster.from_dict(title, result["Properties"])
    assert cluster == cluster2


# Test 8: Test that changing a property after creation works
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    initial_port=st.integers(min_value=1, max_value=65535),
    new_port=st.integers(min_value=1, max_value=65535)
)
def test_property_mutation(title, initial_port, new_port):
    """Test that properties can be changed after object creation."""
    cluster = neptune.DBCluster(title, DBPort=initial_port)
    
    # Initial value
    result1 = cluster.to_dict()
    assert result1["Properties"]["DBPort"] == initial_port
    
    # Change the value
    cluster.DBPort = new_port
    
    # New value should be reflected
    result2 = cluster.to_dict()
    assert result2["Properties"]["DBPort"] == new_port


# Test 9: Test type coercion for string numbers
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    retention_str=st.integers(min_value=1, max_value=35).map(str),
    port_str=st.integers(min_value=1, max_value=65535).map(str)
)
def test_string_number_coercion(title, retention_str, port_str):
    """Test that string representations of numbers are accepted for integer fields."""
    cluster = neptune.DBCluster(
        title,
        BackupRetentionPeriod=retention_str,
        DBPort=port_str
    )
    
    result = cluster.to_dict()
    # Values should be preserved as strings (validator returns unchanged)
    assert result["Properties"]["BackupRetentionPeriod"] == retention_str
    assert result["Properties"]["DBPort"] == port_str
    
    # But should be convertible to int
    int(result["Properties"]["BackupRetentionPeriod"])
    int(result["Properties"]["DBPort"])


# Test 10: Test with Unicode in string values
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    description=st.text().filter(lambda x: any(ord(c) > 127 for c in x) if x else True),
    family=st.text(min_size=1)
)
def test_unicode_in_strings(title, description, family):
    """Test that Unicode characters are handled correctly in string properties."""
    param_group = neptune.DBParameterGroup(
        title,
        Description=description,
        Family=family,
        Parameters={}
    )
    
    result = param_group.to_dict()
    assert result["Properties"]["Description"] == description
    assert result["Properties"]["Family"] == family
    
    # Test JSON serialization with Unicode
    json_str = param_group.to_json()
    parsed = json.loads(json_str)
    assert parsed["Properties"]["Description"] == description