#!/usr/bin/env python3
"""Advanced property-based tests for troposphere.neptune to find real bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import json
import math
from troposphere import neptune
from troposphere import validators

# Test 1: from_dict should accept what to_dict produces (perfect round-trip)
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    min_capacity=st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
    max_capacity=st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False)
)
def test_serverless_scaling_from_dict_roundtrip(title, min_capacity, max_capacity):
    """Test that from_dict accepts what to_dict produces for ServerlessScalingConfiguration."""
    assume(min_capacity <= max_capacity)
    
    # Create a DBCluster with ServerlessScalingConfiguration
    config = neptune.ServerlessScalingConfiguration(
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )
    
    cluster1 = neptune.DBCluster(
        title,
        ServerlessScalingConfiguration=config
    )
    
    # Convert to dict
    dict_repr = cluster1.to_dict()
    
    # Should be able to recreate from dict
    props = dict_repr.get("Properties", {})
    cluster2 = neptune.DBCluster.from_dict(title, props)
    
    # Objects should be equal
    assert cluster1 == cluster2
    assert cluster1.to_dict() == cluster2.to_dict()


# Test 2: Testing extreme values for integer fields
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    backup_retention=st.one_of(
        st.just(0),
        st.just(-1),
        st.just(36),
        st.just(100),
        st.just(2**31 - 1),
        st.just(2**63 - 1),
        st.integers()
    ),
    db_port=st.one_of(
        st.just(0),
        st.just(-1),
        st.just(65536),
        st.just(2**16),
        st.just(2**31 - 1),
        st.integers()
    )
)
def test_integer_field_boundaries(title, backup_retention, db_port):
    """Test integer fields with extreme values."""
    cluster = neptune.DBCluster(
        title,
        BackupRetentionPeriod=backup_retention,
        DBPort=db_port
    )
    
    result = cluster.to_dict()
    # Values should be preserved exactly as given
    assert result["Properties"]["BackupRetentionPeriod"] == backup_retention
    assert result["Properties"]["DBPort"] == db_port


# Test 3: Testing special float values
@given(
    min_capacity=st.sampled_from([float('inf'), float('-inf'), float('nan'), 0.0, -0.0]),
    max_capacity=st.sampled_from([float('inf'), float('-inf'), float('nan'), 0.0, -0.0])
)
def test_serverless_scaling_special_floats(min_capacity, max_capacity):
    """Test ServerlessScalingConfiguration with special float values."""
    config = neptune.ServerlessScalingConfiguration(
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )
    
    result = config.to_dict()
    
    # Check if special values are preserved
    if math.isnan(min_capacity):
        assert math.isnan(result["MinCapacity"])
    else:
        assert result["MinCapacity"] == min_capacity
        
    if math.isnan(max_capacity):
        assert math.isnan(result["MaxCapacity"])
    else:
        assert result["MaxCapacity"] == max_capacity


# Test 4: Empty strings and None values
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    cluster_id=st.one_of(st.just(""), st.none()),
    param_group=st.one_of(st.just(""), st.none()),
    subnet_group=st.one_of(st.just(""), st.none())
)
def test_empty_and_none_strings(title, cluster_id, param_group, subnet_group):
    """Test handling of empty strings and None values."""
    kwargs = {}
    if cluster_id is not None:
        kwargs["DBClusterIdentifier"] = cluster_id
    if param_group is not None:
        kwargs["DBClusterParameterGroupName"] = param_group
    if subnet_group is not None:
        kwargs["DBSubnetGroupName"] = subnet_group
        
    cluster = neptune.DBCluster(title, **kwargs)
    result = cluster.to_dict()
    
    # Check properties are included correctly
    props = result["Properties"]
    if cluster_id is not None:
        assert "DBClusterIdentifier" in props
        assert props["DBClusterIdentifier"] == cluster_id
    if param_group is not None:
        assert "DBClusterParameterGroupName" in props
        assert props["DBClusterParameterGroupName"] == param_group
    if subnet_group is not None:
        assert "DBSubnetGroupName" in props
        assert props["DBSubnetGroupName"] == subnet_group


# Test 5: Lists with duplicates
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    zones=st.lists(st.sampled_from(["us-east-1a", "us-east-1b", "us-east-1c"]), min_size=1, max_size=10),
    exports=st.lists(st.sampled_from(["audit", "error", "general", "slowquery"]), min_size=1, max_size=10)
)
def test_list_with_duplicates(title, zones, exports):
    """Test that lists can contain duplicates."""
    cluster = neptune.DBCluster(
        title,
        AvailabilityZones=zones,
        EnableCloudwatchLogsExports=exports
    )
    
    result = cluster.to_dict()
    # Lists should preserve duplicates
    assert result["Properties"]["AvailabilityZones"] == zones
    assert result["Properties"]["EnableCloudwatchLogsExports"] == exports


# Test 6: Parameter validation with mixed types
@given(
    params=st.one_of(
        st.dictionaries(st.text(min_size=1), st.text()),
        st.dictionaries(st.text(min_size=1), st.integers()),
        st.dictionaries(st.text(min_size=1), st.floats(allow_nan=False, allow_infinity=False)),
        st.dictionaries(st.text(min_size=1), st.booleans()),
        st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()))
    )
)
def test_parameter_dict_mixed_types(params):
    """Test that Parameters dict can have mixed value types."""
    title = "TestParamGroup"
    param_group = neptune.DBParameterGroup(
        title,
        Description="Test group",
        Family="neptune1",
        Parameters=params
    )
    
    result = param_group.to_dict()
    assert result["Properties"]["Parameters"] == params


# Test 7: Boolean coercion edge cases
@given(
    enabled=st.one_of(
        st.just(""),
        st.just("yes"),
        st.just("no"),
        st.just("YES"),
        st.just("NO"),
        st.just(2),
        st.just(-1),
        st.just(0.0),
        st.just(1.0),
        st.just([]),
        st.just([1])
    )
)
def test_boolean_invalid_values(enabled):
    """Test that invalid boolean values are rejected."""
    title = "TestSubscription"
    subscription = neptune.EventSubscription(title)
    
    try:
        subscription.Enabled = enabled
        result = subscription.to_dict()
        # If it didn't raise, check if it was coerced to boolean
        if "Enabled" in result["Properties"]:
            assert result["Properties"]["Enabled"] in [True, False]
    except (ValueError, TypeError):
        # Expected for truly invalid values
        pass


# Test 8: Deeply nested structures
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    num_roles=st.integers(min_value=0, max_value=10)
)
def test_deeply_nested_roles(title, num_roles):
    """Test DBCluster with many nested roles."""
    roles = []
    for i in range(num_roles):
        role = neptune.DBClusterRole(
            RoleArn=f"arn:aws:iam::123456789012:role/role{i}",
            FeatureName=f"feature{i}" if i % 2 == 0 else None
        )
        roles.append(role)
    
    cluster = neptune.DBCluster(title)
    if roles:
        cluster.AssociatedRoles = roles
    
    result = cluster.to_dict()
    
    if roles:
        assert "AssociatedRoles" in result["Properties"]
        assert len(result["Properties"]["AssociatedRoles"]) == num_roles
        
        # Check round-trip
        cluster2 = neptune.DBCluster.from_dict(title, result["Properties"])
        assert cluster == cluster2


# Test 9: Hash consistency
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    instance_class=st.text(min_size=1)
)
@settings(max_examples=200)
def test_hash_consistency(title, instance_class):
    """Test that equal objects have equal hashes."""
    instance1 = neptune.DBInstance(title, DBInstanceClass=instance_class)
    instance2 = neptune.DBInstance(title, DBInstanceClass=instance_class)
    
    # Equal objects must have equal hashes
    assert instance1 == instance2
    assert hash(instance1) == hash(instance2)
    
    # Test that hash is consistent across multiple calls
    hash1_first = hash(instance1)
    hash1_second = hash(instance1)
    assert hash1_first == hash1_second


# Test 10: JSON serialization with special characters
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    description=st.text(),
    family=st.text(min_size=1)
)
def test_json_serialization_special_chars(title, description, family):
    """Test JSON serialization with special characters."""
    param_group = neptune.DBParameterGroup(
        title,
        Description=description,
        Family=family,
        Parameters={}
    )
    
    # Should be able to convert to JSON and back
    json_str = param_group.to_json()
    json_data = json.loads(json_str)
    
    # Verify the data is preserved
    assert json_data["Properties"]["Description"] == description
    assert json_data["Properties"]["Family"] == family