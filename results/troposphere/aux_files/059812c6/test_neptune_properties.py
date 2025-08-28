#!/usr/bin/env python3
"""Property-based tests for troposphere.neptune module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import json
from troposphere import neptune
from troposphere import validators

# Test 1: Boolean validator idempotence
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_idempotence(value):
    """Test that boolean validator is idempotent for valid inputs."""
    result1 = validators.boolean(value)
    result2 = validators.boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)


# Test 2: Integer validator accepts various formats
def is_valid_int_string(x):
    """Check if string can be converted to int."""
    try:
        int(x)
        return True
    except (ValueError, TypeError):
        return False

@given(st.one_of(
    st.integers(),
    st.text(min_size=1).filter(is_valid_int_string)
))
def test_integer_validator_valid(value):
    """Test that integer validator accepts valid integers and returns unchanged value."""
    result = validators.integer(value)
    # The validator should return the value unchanged
    assert result == value
    # Should be convertible to int
    int(result)


# Test 3: Double validator accepts various numeric formats
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '').replace('-', '').replace('e', '').replace('E', '').replace('+', '').isdigit() and x != '' and x.count('.') <= 1)
))
def test_double_validator_valid(value):
    """Test that double validator accepts valid numbers and returns unchanged value."""
    try:
        float(str(value))  # Pre-check if convertible
        result = validators.double(value)
        # The validator should return the value unchanged
        assert result == value
        # Should be convertible to float
        float(result)
    except (ValueError, OverflowError):
        # If float() fails, the validator should also fail
        with pytest.raises(ValueError):
            validators.double(value)


# Test 4: Title validation for Neptune resources
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1))
def test_valid_title_alphanumeric(title):
    """Test that alphanumeric titles are accepted for Neptune resources."""
    cluster = neptune.DBCluster(title)
    assert cluster.title == title


@given(st.text(min_size=1).filter(lambda x: not x.isalnum()))
def test_invalid_title_non_alphanumeric(title):
    """Test that non-alphanumeric titles are rejected."""
    with pytest.raises(ValueError, match="not alphanumeric"):
        neptune.DBCluster(title)


# Test 5: DBCluster to_dict/from_dict round-trip
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    db_cluster_id=st.text(min_size=1),
    backup_retention=st.integers(min_value=1, max_value=35),
    enable_iam=st.sampled_from([True, False, 1, 0, "true", "false"]),
    db_port=st.integers(min_value=1, max_value=65535),
    deletion_protection=st.booleans()
)
def test_db_cluster_to_dict_from_dict_roundtrip(
    title, db_cluster_id, backup_retention, enable_iam, db_port, deletion_protection
):
    """Test DBCluster round-trip through to_dict and from_dict."""
    cluster1 = neptune.DBCluster(
        title,
        DBClusterIdentifier=db_cluster_id,
        BackupRetentionPeriod=backup_retention,
        IamAuthEnabled=enable_iam,
        DBPort=db_port,
        DeletionProtection=deletion_protection
    )
    
    # Convert to dict
    dict_repr = cluster1.to_dict()
    
    # Extract properties (removing Type field)
    props = dict_repr.get("Properties", {})
    
    # Create new object from dict
    cluster2 = neptune.DBCluster.from_dict(title, props)
    
    # Compare the two objects
    assert cluster1 == cluster2
    assert cluster1.to_dict() == cluster2.to_dict()


# Test 6: ServerlessScalingConfiguration with doubles
@given(
    min_capacity=st.floats(min_value=0.5, max_value=128, allow_nan=False),
    max_capacity=st.floats(min_value=0.5, max_value=128, allow_nan=False)
)
def test_serverless_scaling_configuration(min_capacity, max_capacity):
    """Test ServerlessScalingConfiguration with double validator."""
    assume(min_capacity <= max_capacity)  # Logical constraint
    
    config = neptune.ServerlessScalingConfiguration(
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity
    )
    result = config.to_dict()
    
    # Values should be preserved
    assert result["MinCapacity"] == min_capacity
    assert result["MaxCapacity"] == max_capacity
    # Should be convertible to float
    float(result["MinCapacity"])
    float(result["MaxCapacity"])


# Test 7: DBClusterRole required property validation
def test_db_cluster_role_missing_required():
    """Test that DBClusterRole raises error when RoleArn is missing."""
    role = neptune.DBClusterRole()
    with pytest.raises(ValueError, match="RoleArn required"):
        role.to_dict()


@given(
    role_arn=st.text(min_size=1),
    feature_name=st.text(min_size=0)
)
def test_db_cluster_role_with_required(role_arn, feature_name):
    """Test DBClusterRole with required RoleArn."""
    if feature_name:
        role = neptune.DBClusterRole(
            RoleArn=role_arn,
            FeatureName=feature_name
        )
    else:
        role = neptune.DBClusterRole(RoleArn=role_arn)
    
    result = role.to_dict()
    assert result["RoleArn"] == role_arn
    if feature_name:
        assert result["FeatureName"] == feature_name


# Test 8: DBInstance required properties
def test_db_instance_missing_required():
    """Test that DBInstance raises error when required DBInstanceClass is missing."""
    instance = neptune.DBInstance("TestInstance")
    with pytest.raises(ValueError, match="DBInstanceClass required"):
        instance.to_dict()


@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    instance_class=st.text(min_size=1),
    instance_id=st.text(min_size=1),
    allow_major_upgrade=st.sampled_from([True, False, 1, 0, "true", "false"]),
    auto_minor_upgrade=st.booleans()
)
def test_db_instance_with_required(
    title, instance_class, instance_id, allow_major_upgrade, auto_minor_upgrade
):
    """Test DBInstance with required properties."""
    instance = neptune.DBInstance(
        title,
        DBInstanceClass=instance_class,
        DBInstanceIdentifier=instance_id,
        AllowMajorVersionUpgrade=allow_major_upgrade,
        AutoMinorVersionUpgrade=auto_minor_upgrade
    )
    
    result = instance.to_dict()
    assert result["Properties"]["DBInstanceClass"] == instance_class
    assert result["Properties"]["DBInstanceIdentifier"] == instance_id
    # Boolean fields should be normalized
    assert result["Properties"]["AllowMajorVersionUpgrade"] in [True, False]
    assert result["Properties"]["AutoMinorVersionUpgrade"] in [True, False]


# Test 9: DBParameterGroup and DBClusterParameterGroup required fields
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    description=st.text(min_size=1),
    family=st.text(min_size=1),
    params=st.dictionaries(st.text(min_size=1), st.text(min_size=1), min_size=0, max_size=5)
)
def test_parameter_groups_required_fields(title, description, family, params):
    """Test DBParameterGroup and DBClusterParameterGroup with required fields."""
    # Test DBParameterGroup
    param_group = neptune.DBParameterGroup(
        title,
        Description=description,
        Family=family,
        Parameters=params
    )
    result1 = param_group.to_dict()
    assert result1["Properties"]["Description"] == description
    assert result1["Properties"]["Family"] == family
    assert result1["Properties"]["Parameters"] == params
    
    # Test DBClusterParameterGroup (same required fields)
    cluster_param_group = neptune.DBClusterParameterGroup(
        title,
        Description=description,
        Family=family,
        Parameters=params
    )
    result2 = cluster_param_group.to_dict()
    assert result2["Properties"]["Description"] == description
    assert result2["Properties"]["Family"] == family
    assert result2["Properties"]["Parameters"] == params


# Test 10: DBSubnetGroup required properties
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    description=st.text(min_size=1),
    subnet_ids=st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
def test_db_subnet_group_required(title, description, subnet_ids):
    """Test DBSubnetGroup with required properties."""
    subnet_group = neptune.DBSubnetGroup(
        title,
        DBSubnetGroupDescription=description,
        SubnetIds=subnet_ids
    )
    result = subnet_group.to_dict()
    assert result["Properties"]["DBSubnetGroupDescription"] == description
    assert result["Properties"]["SubnetIds"] == subnet_ids


# Test 11: EventSubscription with boolean Enabled field
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    enabled=st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]),
    categories=st.lists(st.text(min_size=1), min_size=0, max_size=3),
    sns_topic=st.text(min_size=1)
)
def test_event_subscription_boolean_field(title, enabled, categories, sns_topic):
    """Test EventSubscription with boolean Enabled field."""
    subscription = neptune.EventSubscription(
        title,
        Enabled=enabled,
        EventCategories=categories,
        SnsTopicArn=sns_topic
    )
    result = subscription.to_dict()
    # Boolean should be normalized
    assert result["Properties"]["Enabled"] in [True, False]
    assert result["Properties"]["EventCategories"] == categories
    assert result["Properties"]["SnsTopicArn"] == sns_topic


# Test 12: Equality and hashing properties
@given(
    title1=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    title2=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    instance_class=st.text(min_size=1)
)
def test_equality_and_hashing(title1, title2, instance_class):
    """Test equality and hashing properties of Neptune objects."""
    # Same title and properties should be equal
    instance1 = neptune.DBInstance(title1, DBInstanceClass=instance_class)
    instance2 = neptune.DBInstance(title1, DBInstanceClass=instance_class)
    
    assert instance1 == instance2
    assert hash(instance1) == hash(instance2)
    
    # Different titles should not be equal
    if title1 != title2:
        instance3 = neptune.DBInstance(title2, DBInstanceClass=instance_class)
        assert instance1 != instance3
        # Note: different objects might have same hash (collision), so we don't test hash inequality


# Test 13: List properties handling
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    availability_zones=st.lists(st.text(min_size=1), min_size=1, max_size=3),
    log_exports=st.lists(st.text(min_size=1), min_size=0, max_size=3),
    security_groups=st.lists(st.text(min_size=1), min_size=0, max_size=3)
)
def test_list_properties(title, availability_zones, log_exports, security_groups):
    """Test that list properties are handled correctly."""
    cluster = neptune.DBCluster(
        title,
        AvailabilityZones=availability_zones,
        EnableCloudwatchLogsExports=log_exports,
        VpcSecurityGroupIds=security_groups
    )
    result = cluster.to_dict()
    assert result["Properties"]["AvailabilityZones"] == availability_zones
    assert result["Properties"]["EnableCloudwatchLogsExports"] == log_exports
    assert result["Properties"]["VpcSecurityGroupIds"] == security_groups


# Test 14: Complex nested structure with roles
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    role_arns=st.lists(st.text(min_size=1), min_size=1, max_size=3),
    feature_names=st.lists(st.text(min_size=0), min_size=1, max_size=3)
)
def test_nested_roles(title, role_arns, feature_names):
    """Test DBCluster with nested DBClusterRole objects."""
    # Ensure we have same number of role_arns and feature_names
    min_len = min(len(role_arns), len(feature_names))
    role_arns = role_arns[:min_len]
    feature_names = feature_names[:min_len]
    
    roles = []
    for arn, feature in zip(role_arns, feature_names):
        if feature:
            roles.append(neptune.DBClusterRole(RoleArn=arn, FeatureName=feature))
        else:
            roles.append(neptune.DBClusterRole(RoleArn=arn))
    
    cluster = neptune.DBCluster(title, AssociatedRoles=roles)
    result = cluster.to_dict()
    
    assert "AssociatedRoles" in result["Properties"]
    assert len(result["Properties"]["AssociatedRoles"]) == len(roles)
    for i, role_dict in enumerate(result["Properties"]["AssociatedRoles"]):
        assert role_dict["RoleArn"] == role_arns[i]
        if feature_names[i]:
            assert role_dict["FeatureName"] == feature_names[i]


# Test 15: Edge cases for integer validator
@given(st.integers())
def test_integer_validator_edge_cases(value):
    """Test integer validator with various integer values."""
    result = validators.integer(value)
    assert result == value
    int(result)  # Should be convertible


@given(st.text(min_size=1).filter(lambda x: not (x.lstrip('-').isdigit() and x != '' and x != '-')))
def test_integer_validator_invalid(value):
    """Test that integer validator rejects non-integer strings."""
    with pytest.raises(ValueError, match="is not a valid integer"):
        validators.integer(value)


# Test 16: Edge cases for double validator
@given(st.floats())
def test_double_validator_edge_cases(value):
    """Test double validator with various float values including special values."""
    import math
    result = validators.double(value)
    # Can't use == for NaN comparison
    if math.isnan(value):
        assert math.isnan(result)
    else:
        assert result == value


# Test 17: ServerlessScalingConfiguration missing required fields
def test_serverless_scaling_missing_required():
    """Test that ServerlessScalingConfiguration requires both MinCapacity and MaxCapacity."""
    config1 = neptune.ServerlessScalingConfiguration(MinCapacity=1.0)
    with pytest.raises(ValueError, match="MaxCapacity required"):
        config1.to_dict()
    
    config2 = neptune.ServerlessScalingConfiguration(MaxCapacity=2.0)
    with pytest.raises(ValueError, match="MinCapacity required"):
        config2.to_dict()