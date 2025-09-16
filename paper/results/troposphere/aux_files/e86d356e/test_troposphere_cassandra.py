#!/usr/bin/env python3
"""Property-based tests for troposphere.cassandra module."""

import sys
import json
import re
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra
from troposphere.validators.cassandra import (
    validate_clusteringkeycolumn_orderby,
    validate_billingmode_mode,
)
from troposphere import AWSObject, AWSProperty


# Test 1: Validator function properties
@given(st.text())
def test_validate_clusteringkeycolumn_orderby_rejects_invalid(value):
    """Validator should only accept ASC or DESC, reject everything else."""
    if value not in ("ASC", "DESC"):
        try:
            validate_clusteringkeycolumn_orderby(value)
            assert False, f"Should have rejected {value!r}"
        except ValueError as e:
            assert "ClusteringKeyColumn OrderBy must be one of" in str(e)
    else:
        # Valid values should return the same value
        result = validate_clusteringkeycolumn_orderby(value)
        assert result == value


@given(st.text())
def test_validate_billingmode_mode_rejects_invalid(value):
    """Validator should only accept ON_DEMAND or PROVISIONED."""
    if value not in ("ON_DEMAND", "PROVISIONED"):
        try:
            validate_billingmode_mode(value)
            assert False, f"Should have rejected {value!r}"
        except ValueError as e:
            assert "BillingMode Mode must be one of" in str(e)
    else:
        # Valid values should return the same value
        result = validate_billingmode_mode(value)
        assert result == value


# Test 2: Object construction with valid properties
@given(
    keyspace_name=st.text(min_size=1, max_size=255).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
    client_side_timestamps=st.booleans(),
)
def test_keyspace_construction_and_serialization(keyspace_name, client_side_timestamps):
    """Keyspace objects should construct and serialize correctly."""
    # Create a Keyspace with valid properties
    keyspace = cassandra.Keyspace(
        title="TestKeyspace",
        KeyspaceName=keyspace_name,
        ClientSideTimestampsEnabled=client_side_timestamps,
    )
    
    # Should be able to serialize to dict
    result = keyspace.to_dict()
    assert isinstance(result, dict)
    assert result["Type"] == "AWS::Cassandra::Keyspace"
    
    # Properties should be preserved
    props = result.get("Properties", {})
    assert props.get("KeyspaceName") == keyspace_name
    assert props.get("ClientSideTimestampsEnabled") == client_side_timestamps


# Test 3: BillingMode construction with validators
@given(mode=st.sampled_from(["ON_DEMAND", "PROVISIONED"]))
def test_billingmode_valid_modes(mode):
    """BillingMode should accept valid modes and serialize correctly."""
    billing = cassandra.BillingMode(Mode=mode)
    
    # Should serialize correctly
    result = billing.to_dict()
    assert result["Mode"] == mode


# Test 4: Table construction with required properties
@given(
    keyspace_name=st.text(min_size=1, max_size=48).filter(lambda x: re.match(r'^[a-zA-Z0-9_]+$', x)),
    column_name=st.text(min_size=1, max_size=48).filter(lambda x: re.match(r'^[a-zA-Z0-9_]+$', x)),
    column_type=st.sampled_from(["text", "int", "bigint", "uuid", "boolean", "float", "double"]),
)
def test_table_construction_with_required_fields(keyspace_name, column_name, column_type):
    """Table should construct with required fields and serialize correctly."""
    # Create a partition key column
    partition_column = cassandra.Column(
        ColumnName=column_name,
        ColumnType=column_type
    )
    
    # Create a table with minimum required properties
    table = cassandra.Table(
        title="TestTable",
        KeyspaceName=keyspace_name,
        PartitionKeyColumns=[partition_column]
    )
    
    # Should serialize correctly
    result = table.to_dict()
    assert result["Type"] == "AWS::Cassandra::Table"
    props = result.get("Properties", {})
    assert props["KeyspaceName"] == keyspace_name
    assert len(props["PartitionKeyColumns"]) == 1
    assert props["PartitionKeyColumns"][0]["ColumnName"] == column_name
    assert props["PartitionKeyColumns"][0]["ColumnType"] == column_type


# Test 5: ClusteringKeyColumn with OrderBy validation
@given(
    column_name=st.text(min_size=1, max_size=48).filter(lambda x: re.match(r'^[a-zA-Z0-9_]+$', x)),
    column_type=st.sampled_from(["text", "int", "bigint", "uuid"]),
    order_by=st.sampled_from(["ASC", "DESC"]),
)
def test_clustering_key_column_with_orderby(column_name, column_type, order_by):
    """ClusteringKeyColumn should validate OrderBy correctly."""
    column = cassandra.Column(
        ColumnName=column_name,
        ColumnType=column_type
    )
    
    clustering = cassandra.ClusteringKeyColumn(
        Column=column,
        OrderBy=order_by
    )
    
    # Should serialize correctly
    result = clustering.to_dict()
    assert result["OrderBy"] == order_by
    assert result["Column"]["ColumnName"] == column_name
    assert result["Column"]["ColumnType"] == column_type


# Test 6: Invalid OrderBy should raise error
@given(
    column_name=st.text(min_size=1, max_size=48).filter(lambda x: re.match(r'^[a-zA-Z0-9_]+$', x)),
    column_type=st.sampled_from(["text", "int"]),
    invalid_order=st.text().filter(lambda x: x not in ["ASC", "DESC"]),
)
def test_clustering_key_column_rejects_invalid_orderby(column_name, column_type, invalid_order):
    """ClusteringKeyColumn should reject invalid OrderBy values."""
    column = cassandra.Column(
        ColumnName=column_name,
        ColumnType=column_type
    )
    
    try:
        clustering = cassandra.ClusteringKeyColumn(
            Column=column,
            OrderBy=invalid_order
        )
        # If we got here, it didn't validate - this might be a bug
        # But let's check if it validates on serialization
        clustering.to_dict()
        assert False, f"Should have rejected OrderBy={invalid_order!r}"
    except (ValueError, TypeError) as e:
        # Expected - invalid OrderBy should be rejected
        pass


# Test 7: Title validation for alphanumeric constraint
@given(title=st.text())
def test_title_validation_alphanumeric(title):
    """Object titles must be alphanumeric only."""
    is_valid_title = bool(re.match(r'^[a-zA-Z0-9]+$', title))
    
    try:
        keyspace = cassandra.Keyspace(title=title)
        # If construction succeeded, title should be valid
        assert is_valid_title or not title, f"Invalid title {title!r} was accepted"
    except ValueError as e:
        # Should only reject non-alphanumeric titles
        assert not is_valid_title
        assert 'not alphanumeric' in str(e)


# Test 8: ReplicationSpecification properties
@given(
    regions=st.lists(st.sampled_from(["us-east-1", "us-west-2", "eu-west-1"]), min_size=1, max_size=3, unique=True),
    strategy=st.sampled_from(["SINGLE_REGION", "MULTI_REGION"])
)
def test_replication_specification(regions, strategy):
    """ReplicationSpecification should handle regions and strategy correctly."""
    replication = cassandra.ReplicationSpecification(
        RegionList=regions,
        ReplicationStrategy=strategy
    )
    
    result = replication.to_dict()
    assert result["RegionList"] == regions
    assert result["ReplicationStrategy"] == strategy


# Test 9: AutoScaling settings with integer validation
@given(
    min_units=st.integers(min_value=1, max_value=1000),
    max_units=st.integers(min_value=1, max_value=40000),
    target_value=st.integers(min_value=20, max_value=90),
)
def test_autoscaling_settings(min_units, max_units, target_value):
    """AutoScaling settings should handle integer properties correctly."""
    assume(min_units <= max_units)  # Logical constraint
    
    target_tracking = cassandra.TargetTrackingScalingPolicyConfiguration(
        TargetValue=target_value
    )
    
    scaling_policy = cassandra.ScalingPolicy(
        TargetTrackingScalingPolicyConfiguration=target_tracking
    )
    
    autoscaling = cassandra.AutoScalingSetting(
        MinimumUnits=min_units,
        MaximumUnits=max_units,
        ScalingPolicy=scaling_policy
    )
    
    result = autoscaling.to_dict()
    assert result["MinimumUnits"] == min_units
    assert result["MaximumUnits"] == max_units
    assert result["ScalingPolicy"]["TargetTrackingScalingPolicyConfiguration"]["TargetValue"] == target_value


# Test 10: ProvisionedThroughput required fields
@given(
    read_units=st.integers(min_value=1, max_value=40000),
    write_units=st.integers(min_value=1, max_value=40000),
)
def test_provisioned_throughput_required_fields(read_units, write_units):
    """ProvisionedThroughput should enforce required fields."""
    throughput = cassandra.ProvisionedThroughput(
        ReadCapacityUnits=read_units,
        WriteCapacityUnits=write_units
    )
    
    result = throughput.to_dict()
    assert result["ReadCapacityUnits"] == read_units
    assert result["WriteCapacityUnits"] == write_units


if __name__ == "__main__":
    # Run with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])