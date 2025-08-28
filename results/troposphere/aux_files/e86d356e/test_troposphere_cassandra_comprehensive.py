#!/usr/bin/env python3
"""Comprehensive property-based tests looking for deeper bugs in troposphere.cassandra."""

import sys
import json
import re
from hypothesis import given, strategies as st, assume, settings, example, note
from hypothesis.strategies import composite
from decimal import Decimal

# Add the virtual environment's site-packages to path  
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra
from troposphere.validators.cassandra import (
    validate_clusteringkeycolumn_orderby,
    validate_billingmode_mode,
)


# Test 1: Type confusion - passing wrong types to validators
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.booleans(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.binary(),
))
def test_validators_with_non_string_types(value):
    """Validators should handle non-string types appropriately."""
    # Test clusteringkeycolumn_orderby
    if not isinstance(value, str):
        try:
            result = validate_clusteringkeycolumn_orderby(value)
            # If it accepts non-strings, check the behavior
            note(f"Accepted non-string {type(value).__name__}: {value!r} -> {result!r}")
            # For some types this might work due to string coercion
        except (ValueError, TypeError, AttributeError):
            pass  # Expected for non-strings
    
    # Test billingmode_mode
    if not isinstance(value, str):
        try:
            result = validate_billingmode_mode(value)
            note(f"Accepted non-string {type(value).__name__}: {value!r} -> {result!r}")
        except (ValueError, TypeError, AttributeError):
            pass  # Expected


# Test 2: Integer validators with boundary values
@given(st.one_of(
    st.just(0),
    st.just(-1),
    st.just(2**31 - 1),
    st.just(2**31),
    st.just(2**32 - 1),
    st.just(2**32),
    st.just(2**63 - 1),
    st.just(2**63),
    st.just(-2**31),
    st.just(-2**63),
    st.floats(allow_nan=True, allow_infinity=True),
    st.decimals(allow_nan=True, allow_infinity=True),
))
def test_integer_properties_with_edge_values(value):
    """Test integer properties with boundary and special values."""
    # Test with ProvisionedThroughput
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=value,
            WriteCapacityUnits=1
        )
        result = throughput.to_dict()
        # Check if the value is preserved correctly
        assert result["ReadCapacityUnits"] == value or isinstance(value, (float, Decimal))
        note(f"Accepted value {value!r} of type {type(value).__name__}")
    except (TypeError, ValueError, OverflowError, AttributeError):
        pass  # Some values should be rejected
    
    # Test with AutoScalingSetting
    try:
        autoscaling = cassandra.AutoScalingSetting(
            MinimumUnits=value,
            MaximumUnits=100
        )
        result = autoscaling.to_dict()
        note(f"AutoScaling accepted {value!r}")
    except (TypeError, ValueError, OverflowError, AttributeError):
        pass


# Test 3: Boolean properties with non-boolean values
@given(st.one_of(
    st.just(0),
    st.just(1),
    st.just("true"),
    st.just("false"),
    st.just("True"),
    st.just("False"),
    st.just("yes"),
    st.just("no"),
    st.just(""),
    st.none(),
    st.lists(st.booleans()),
))
def test_boolean_properties_with_truthy_values(value):
    """Test boolean properties with various truthy/falsy values."""
    try:
        keyspace = cassandra.Keyspace(
            title="TestKeyspace",
            ClientSideTimestampsEnabled=value
        )
        result = keyspace.to_dict()
        # Check how the value was interpreted
        actual = result["Properties"].get("ClientSideTimestampsEnabled")
        note(f"Input {value!r} ({type(value).__name__}) -> {actual!r} ({type(actual).__name__})")
    except (TypeError, ValueError):
        pass  # Some values should be rejected


# Test 4: Complex Table with all optional properties
@composite
def complex_table_strategy(draw):
    """Generate complex Table configurations."""
    keyspace_name = draw(st.text(min_size=1, max_size=20).filter(
        lambda x: re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', x)
    ))
    
    # Generate multiple columns
    num_partition_keys = draw(st.integers(min_value=1, max_value=5))
    partition_columns = [
        cassandra.Column(
            ColumnName=f"pk_{i}",
            ColumnType=draw(st.sampled_from(["text", "int", "uuid", "timeuuid"]))
        )
        for i in range(num_partition_keys)
    ]
    
    # Generate clustering columns
    num_clustering = draw(st.integers(min_value=0, max_value=5))
    clustering_columns = [
        cassandra.ClusteringKeyColumn(
            Column=cassandra.Column(
                ColumnName=f"ck_{i}",
                ColumnType=draw(st.sampled_from(["text", "int", "timestamp"]))
            ),
            OrderBy=draw(st.sampled_from(["ASC", "DESC"]))
        )
        for i in range(num_clustering)
    ]
    
    # Generate regular columns
    num_regular = draw(st.integers(min_value=0, max_value=10))
    regular_columns = [
        cassandra.Column(
            ColumnName=f"col_{i}",
            ColumnType=draw(st.sampled_from(["text", "int", "boolean", "double", "map<text,text>"]))
        )
        for i in range(num_regular)
    ]
    
    return {
        "keyspace_name": keyspace_name,
        "partition_columns": partition_columns,
        "clustering_columns": clustering_columns if clustering_columns else None,
        "regular_columns": regular_columns if regular_columns else None,
    }


@given(complex_table_strategy())
def test_complex_table_configurations(table_config):
    """Test complex Table configurations with multiple columns."""
    table = cassandra.Table(
        title="ComplexTable",
        KeyspaceName=table_config["keyspace_name"],
        PartitionKeyColumns=table_config["partition_columns"],
        ClusteringKeyColumns=table_config["clustering_columns"],
        RegularColumns=table_config["regular_columns"],
    )
    
    result = table.to_dict()
    
    # Verify all columns are preserved
    props = result["Properties"]
    assert len(props["PartitionKeyColumns"]) == len(table_config["partition_columns"])
    
    if table_config["clustering_columns"]:
        assert len(props["ClusteringKeyColumns"]) == len(table_config["clustering_columns"])
        # Check OrderBy is preserved
        for i, col in enumerate(props["ClusteringKeyColumns"]):
            assert col["OrderBy"] in ["ASC", "DESC"]
    
    if table_config["regular_columns"]:
        assert len(props["RegularColumns"]) == len(table_config["regular_columns"])


# Test 5: Mixing valid and invalid properties
@given(
    valid_mode=st.sampled_from(["ON_DEMAND", "PROVISIONED"]),
    invalid_value=st.text().filter(lambda x: x not in ["ON_DEMAND", "PROVISIONED"]),
)
def test_property_override_behavior(valid_mode, invalid_value):
    """Test what happens when properties are set multiple times."""
    # Create with valid mode
    billing = cassandra.BillingMode(Mode=valid_mode)
    
    # Try to override with invalid value
    try:
        billing.Mode = invalid_value
        # If this succeeds, check what happens on serialization
        result = billing.to_dict()
        # Did it keep the invalid value or validate on serialization?
        note(f"Overwrote {valid_mode!r} with {invalid_value!r}, got {result['Mode']!r}")
    except (ValueError, TypeError, AttributeError):
        pass  # Expected if validation happens on assignment


# Test 6: Property access patterns
@given(
    keyspace_name=st.text(min_size=1, max_size=20).filter(
        lambda x: re.match(r'^[a-zA-Z0-9]+$', x)
    ),
)
def test_property_access_methods(keyspace_name):
    """Test different ways of accessing properties."""
    keyspace = cassandra.Keyspace(
        title="TestKeyspace",
        KeyspaceName=keyspace_name
    )
    
    # Test different access methods
    # Direct attribute access
    try:
        name_via_attr = keyspace.KeyspaceName
        assert name_via_attr == keyspace_name
    except AttributeError:
        pass
    
    # Via properties dict
    try:
        name_via_props = keyspace.properties.get("KeyspaceName")
        assert name_via_props == keyspace_name
    except (AttributeError, KeyError):
        pass
    
    # Via to_dict
    result = keyspace.to_dict()
    name_via_dict = result["Properties"]["KeyspaceName"]
    assert name_via_dict == keyspace_name


# Test 7: Testing ReplicaSpecification with region validation
@given(
    region=st.text(),
    read_units=st.integers(min_value=1, max_value=1000),
)
def test_replica_specification_region_validation(region, read_units):
    """Test ReplicaSpecification with various region values."""
    try:
        replica = cassandra.ReplicaSpecification(
            Region=region,  # Required field
            ReadCapacityUnits=read_units
        )
        result = replica.to_dict()
        # Any string is accepted as region - AWS will validate
        assert result["Region"] == region
        assert result.get("ReadCapacityUnits") == read_units
    except (ValueError, TypeError):
        pass  # Might validate regions


# Test 8: EncryptionSpecification with various encryption types
@given(
    encryption_type=st.text(),
    kms_key=st.text(),
)
def test_encryption_specification_types(encryption_type, kms_key):
    """Test EncryptionSpecification with various encryption types."""
    try:
        # EncryptionType is required
        encryption = cassandra.EncryptionSpecification(
            EncryptionType=encryption_type,
            KmsKeyIdentifier=kms_key if kms_key else None
        )
        result = encryption.to_dict()
        assert result["EncryptionType"] == encryption_type
        if kms_key:
            assert result.get("KmsKeyIdentifier") == kms_key
    except (ValueError, TypeError):
        pass


# Test 9: Type field with Fields property
@given(
    type_name=st.text(min_size=1, max_size=20).filter(
        lambda x: re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', x)
    ),
    num_fields=st.integers(min_value=1, max_value=10),
)
def test_type_with_fields(type_name, num_fields):
    """Test Type resource with Field definitions."""
    fields = [
        cassandra.Field(
            FieldName=f"field_{i}",
            FieldType="text"
        )
        for i in range(num_fields)
    ]
    
    type_resource = cassandra.Type(
        title="TestType",
        KeyspaceName="test_keyspace",
        TypeName=type_name,
        Fields=fields
    )
    
    result = type_resource.to_dict()
    assert result["Type"] == "AWS::Cassandra::Type"
    assert result["Properties"]["TypeName"] == type_name
    assert len(result["Properties"]["Fields"]) == num_fields


# Test 10: Validator return value identity
@given(st.sampled_from(["ASC", "DESC", "ON_DEMAND", "PROVISIONED"]))
def test_validator_return_identity(value):
    """Validators should return the exact same object/value they receive."""
    # Test both validators
    if value in ["ASC", "DESC"]:
        result = validate_clusteringkeycolumn_orderby(value)
        assert result is value  # Should be same object
    
    if value in ["ON_DEMAND", "PROVISIONED"]:
        result = validate_billingmode_mode(value)
        assert result is value  # Should be same object


# Test 11: Testing with JSON-incompatible values
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.decimals().filter(lambda x: not x.is_finite()),
))
def test_json_incompatible_values(value):
    """Test handling of values that can't be serialized to JSON."""
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=value if not isinstance(value, float) or value == value else 1,
            WriteCapacityUnits=1
        )
        result = throughput.to_dict()
        # Try to serialize to JSON
        json_str = json.dumps(result)
        # If this succeeds, the value was handled somehow
        note(f"Successfully serialized {value!r} to JSON")
    except (TypeError, ValueError, OverflowError):
        pass  # Expected for JSON-incompatible values


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])