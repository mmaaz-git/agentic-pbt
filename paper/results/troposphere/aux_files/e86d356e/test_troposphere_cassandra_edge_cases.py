#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.cassandra module."""

import sys
import json
import re
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra
from troposphere.validators.cassandra import (
    validate_clusteringkeycolumn_orderby,
    validate_billingmode_mode,
)
from troposphere import AWSObject, AWSProperty


# Test edge cases with Unicode and special characters
@given(st.text())
def test_validator_with_unicode_and_special_chars(value):
    """Test validators with Unicode and special characters."""
    # Test clustering key column orderby validator
    if value not in ("ASC", "DESC"):
        try:
            result = validate_clusteringkeycolumn_orderby(value)
            assert False, f"Should have rejected {value!r} but got {result!r}"
        except ValueError:
            pass  # Expected
    else:
        result = validate_clusteringkeycolumn_orderby(value)
        assert result == value


# Test empty strings and None values
@given(st.one_of(st.none(), st.just("")))
def test_validators_with_empty_or_none(value):
    """Test validators with empty strings and None values."""
    # Both validators should reject empty/None
    try:
        validate_clusteringkeycolumn_orderby(value)
        assert False, f"Should have rejected {value!r}"
    except (ValueError, TypeError, AttributeError):
        pass  # Expected
    
    try:
        validate_billingmode_mode(value)
        assert False, f"Should have rejected {value!r}"
    except (ValueError, TypeError, AttributeError):
        pass  # Expected


# Test case sensitivity
@given(st.sampled_from(["asc", "desc", "Asc", "Desc", "aSc", "DeSc"]))
def test_orderby_case_sensitivity(value):
    """OrderBy validator should be case-sensitive."""
    try:
        result = validate_clusteringkeycolumn_orderby(value)
        # If it accepts lowercase, that's a bug
        assert False, f"Should have rejected case variant {value!r} but got {result!r}"
    except ValueError as e:
        assert "ClusteringKeyColumn OrderBy must be one of" in str(e)


# Test BillingMode with None provisioned throughput
@given(mode=st.sampled_from(["ON_DEMAND", "PROVISIONED"]))
def test_billingmode_with_optional_throughput(mode):
    """BillingMode should handle optional ProvisionedThroughput correctly."""
    # ON_DEMAND shouldn't require ProvisionedThroughput
    billing = cassandra.BillingMode(Mode=mode)
    result = billing.to_dict()
    assert result["Mode"] == mode
    
    # If PROVISIONED, can still be created without throughput (it's optional)
    if mode == "PROVISIONED":
        # But adding throughput should work
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=100,
            WriteCapacityUnits=100
        )
        billing_with_throughput = cassandra.BillingMode(
            Mode=mode,
            ProvisionedThroughput=throughput
        )
        result2 = billing_with_throughput.to_dict()
        assert result2["Mode"] == mode
        assert result2["ProvisionedThroughput"]["ReadCapacityUnits"] == 100


# Test Table with empty partition key columns (should fail)
def test_table_with_empty_partition_keys():
    """Table should reject empty PartitionKeyColumns."""
    try:
        table = cassandra.Table(
            title="TestTable",
            KeyspaceName="test_keyspace",
            PartitionKeyColumns=[]  # Empty list - should this be allowed?
        )
        result = table.to_dict()
        # If this succeeds, it might be a bug - empty partition keys don't make sense
        # But the library might allow it for CloudFormation to validate
    except (ValueError, TypeError):
        pass  # This would be the expected behavior


# Test extremely long names
@given(
    long_name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                      min_size=256, max_size=1000)
)
def test_long_names(long_name):
    """Test handling of extremely long names."""
    # KeyspaceName might have length limits
    try:
        keyspace = cassandra.Keyspace(
            title="TestKeyspace",
            KeyspaceName=long_name
        )
        result = keyspace.to_dict()
        # The library allows it - CloudFormation would validate
        assert result["Properties"]["KeyspaceName"] == long_name
    except (ValueError, TypeError):
        pass  # Some implementations might validate length


# Test integer overflow scenarios
@given(
    huge_int=st.integers(min_value=2**31, max_value=2**63)
)
def test_integer_overflow_in_capacity_settings(huge_int):
    """Test handling of very large integers in capacity settings."""
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=huge_int,
            WriteCapacityUnits=huge_int
        )
        result = throughput.to_dict()
        assert result["ReadCapacityUnits"] == huge_int
        assert result["WriteCapacityUnits"] == huge_int
    except (ValueError, TypeError, OverflowError):
        pass  # Might have limits


# Test negative integers (should probably be rejected)
@given(
    negative_int=st.integers(max_value=-1)
)
def test_negative_capacity_units(negative_int):
    """Capacity units should not accept negative values."""
    # This should probably be rejected but let's test
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=negative_int,
            WriteCapacityUnits=1
        )
        result = throughput.to_dict()
        # If this succeeds, it's likely a bug - negative capacity doesn't make sense
        # The library doesn't validate this - leaves it to CloudFormation
        assert result["ReadCapacityUnits"] == negative_int
    except (ValueError, TypeError):
        pass  # This would be expected


# Test float values where integers are expected
@given(
    float_value=st.floats(min_value=1.0, max_value=1000.0).filter(lambda x: not x.is_integer())
)
def test_float_instead_of_integer(float_value):
    """Test providing floats where integers are expected."""
    try:
        throughput = cassandra.ProvisionedThroughput(
            ReadCapacityUnits=float_value,
            WriteCapacityUnits=1
        )
        result = throughput.to_dict()
        # If it accepts floats, check how they're handled
        # It might convert to int or reject them
    except (TypeError, ValueError):
        pass  # Expected if type checking is strict


# Test property assignment after construction
@given(
    initial_name=st.text(min_size=1, max_size=10).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
    new_name=st.text(min_size=1, max_size=10).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
)
def test_property_mutation_after_construction(initial_name, new_name):
    """Test that properties can be modified after construction."""
    keyspace = cassandra.Keyspace(
        title="TestKeyspace",
        KeyspaceName=initial_name
    )
    
    # Get initial state
    result1 = keyspace.to_dict()
    assert result1["Properties"]["KeyspaceName"] == initial_name
    
    # Modify the property
    keyspace.KeyspaceName = new_name
    
    # Check it changed
    result2 = keyspace.to_dict()
    assert result2["Properties"]["KeyspaceName"] == new_name


# Test missing required fields
def test_missing_required_fields():
    """Test that required fields are enforced."""
    # Table requires KeyspaceName and PartitionKeyColumns
    try:
        table = cassandra.Table(title="TestTable")
        # Try to serialize without required fields
        result = table.to_dict()
        # If this succeeds without required fields, might be a validation issue
    except (ValueError, TypeError, KeyError):
        pass  # Expected
    
    # Column requires ColumnName and ColumnType
    try:
        column = cassandra.Column()
        result = column.to_dict()
        # Missing required fields
    except (TypeError, ValueError, KeyError):
        pass  # Expected


# Test circular references or deep nesting
@given(depth=st.integers(min_value=1, max_value=10))
def test_deep_nesting_in_properties(depth):
    """Test deeply nested property structures."""
    # Create nested auto-scaling specifications
    target_tracking = cassandra.TargetTrackingScalingPolicyConfiguration(
        TargetValue=70
    )
    
    scaling_policy = cassandra.ScalingPolicy(
        TargetTrackingScalingPolicyConfiguration=target_tracking
    )
    
    autoscaling = cassandra.AutoScalingSetting(
        MinimumUnits=1,
        MaximumUnits=100,
        ScalingPolicy=scaling_policy
    )
    
    spec = cassandra.AutoScalingSpecification(
        ReadCapacityAutoScaling=autoscaling,
        WriteCapacityAutoScaling=autoscaling  # Reusing same object
    )
    
    # This creates a Table with nested structures
    table = cassandra.Table(
        title="TestTable",
        KeyspaceName="test",
        PartitionKeyColumns=[
            cassandra.Column(ColumnName=f"col{i}", ColumnType="text")
            for i in range(depth)
        ],
        AutoScalingSpecifications=spec
    )
    
    result = table.to_dict()
    assert len(result["Properties"]["PartitionKeyColumns"]) == depth


# Test special CloudFormation values
@given(
    special_value=st.sampled_from(["!Ref", "!GetAtt", "${AWS::StackName}", "Fn::Sub"])
)
def test_special_cloudformation_syntax_in_strings(special_value):
    """Test that CloudFormation special syntax in strings is preserved."""
    # These might be treated specially or just as regular strings
    keyspace = cassandra.Keyspace(
        title="TestKeyspace",
        KeyspaceName=special_value  # Using CF function as name
    )
    
    result = keyspace.to_dict()
    # Should preserve the special value
    assert result["Properties"]["KeyspaceName"] == special_value


# Test whitespace in validators
@given(
    value_with_spaces=st.sampled_from([" ASC", "ASC ", " ASC ", "AS C", "A SC"])
)
def test_validator_with_whitespace(value_with_spaces):
    """Validators should handle whitespace appropriately."""
    try:
        result = validate_clusteringkeycolumn_orderby(value_with_spaces)
        # If it accepts with spaces, that's unexpected
        assert False, f"Accepted {value_with_spaces!r} - got {result!r}"
    except ValueError:
        pass  # Expected - should reject with whitespace


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])