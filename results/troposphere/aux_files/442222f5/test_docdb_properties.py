import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest
from troposphere import validators
from troposphere.docdb import (
    DBCluster, DBInstance, DBClusterParameterGroup, DBSubnetGroup,
    ServerlessV2ScalingConfiguration, EventSubscription
)


# Test validator functions
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator handles all documented valid inputs"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    # Verify the mapping is correct
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(st.integers(), st.text(alphabet="0123456789")))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer representations"""
    result = validators.integer(value)
    # Should not raise and should be convertible to int
    int(result)


@given(st.one_of(st.floats(allow_nan=False, allow_infinity=False), 
                  st.integers(),
                  st.text(alphabet="0123456789.-")))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid float representations"""
    try:
        float(value)  # Pre-check if it's actually convertible
        result = validators.double(value)
        # Should not raise and should be convertible to float
        float(result)
    except (ValueError, TypeError):
        # If Python can't convert it, the validator should also fail
        with pytest.raises(ValueError):
            validators.double(value)


# Test title validation
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1))
def test_valid_alphanumeric_titles(title):
    """Test that alphanumeric titles are accepted"""
    cluster = DBCluster(title)
    cluster.validate_title()  # Should not raise


@given(st.text(min_size=1))
def test_title_validation_rejects_non_alphanumeric(title):
    """Test that non-alphanumeric titles are rejected when they contain special chars"""
    # Check if title has non-alphanumeric characters
    import re
    if not re.match(r'^[a-zA-Z0-9]+$', title):
        cluster = DBCluster(title)
        with pytest.raises(ValueError, match="not alphanumeric"):
            cluster.validate_title()
    else:
        # If it's alphanumeric, it should pass
        cluster = DBCluster(title)
        cluster.validate_title()


# Test round-trip serialization for DBCluster
@given(
    st.builds(
        dict,
        AvailabilityZones=st.one_of(st.none(), st.lists(st.text(min_size=1), max_size=3)),
        BackupRetentionPeriod=st.one_of(st.none(), st.integers(min_value=1, max_value=35)),
        DBClusterIdentifier=st.one_of(st.none(), st.text(min_size=1, max_size=63)),
        Port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
        StorageEncrypted=st.one_of(st.none(), st.booleans()),
        MasterUsername=st.one_of(st.none(), st.text(min_size=1, max_size=16))
    )
)
def test_dbcluster_to_dict_from_dict_roundtrip(properties):
    """Test that DBCluster can be serialized and deserialized without loss"""
    # Filter out None values
    properties = {k: v for k, v in properties.items() if v is not None}
    
    # Create a DBCluster with the properties
    original = DBCluster("TestCluster", **properties)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract just the Properties section for from_dict
    if "Properties" in dict_repr:
        props_dict = dict_repr["Properties"]
        # Create new instance from dict
        restored = DBCluster._from_dict("TestCluster", **props_dict)
        
        # Compare the properties
        restored_dict = restored.to_dict()
        
        # They should be equal
        assert dict_repr == restored_dict


# Test ServerlessV2ScalingConfiguration validation
@given(
    min_capacity=st.floats(min_value=0.5, max_value=128),
    max_capacity=st.floats(min_value=0.5, max_value=128)
)
def test_serverless_scaling_configuration(min_capacity, max_capacity):
    """Test ServerlessV2ScalingConfiguration with valid capacity values"""
    config = ServerlessV2ScalingConfiguration(
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )
    # Should not raise during creation
    dict_repr = config.to_dict()
    assert "MinCapacity" in dict_repr
    assert "MaxCapacity" in dict_repr


# Test required properties enforcement
def test_dbcluster_parameter_group_required_properties():
    """Test that DBClusterParameterGroup enforces required properties"""
    # Should fail without required properties
    with pytest.raises(ValueError):
        group = DBClusterParameterGroup("TestGroup")
        group.to_dict()  # Validation happens here
    
    # Should succeed with required properties
    group = DBClusterParameterGroup(
        "TestGroup",
        Description="Test description",
        Family="docdb4.0",
        Parameters={"param1": "value1"}
    )
    group.to_dict()  # Should not raise


# Test DBInstance required properties
def test_dbinstance_required_properties():
    """Test that DBInstance enforces required properties"""
    # Should fail without required properties
    with pytest.raises(ValueError):
        instance = DBInstance("TestInstance")
        instance.to_dict()  # Validation happens here
    
    # Should succeed with required properties  
    instance = DBInstance(
        "TestInstance",
        DBClusterIdentifier="test-cluster",
        DBInstanceClass="db.r5.large"
    )
    instance.to_dict()  # Should not raise


# Test edge cases in boolean validator
@given(st.one_of(
    st.text(),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs"""
    if value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
        with pytest.raises(ValueError):
            validators.boolean(value)