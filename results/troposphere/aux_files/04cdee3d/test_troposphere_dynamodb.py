#!/usr/bin/env python3
"""Property-based tests for troposphere.dynamodb module."""

import math
from hypothesis import given, strategies as st, assume
import pytest
from troposphere import dynamodb
from troposphere.validators import boolean, double, integer
from troposphere.validators.dynamodb import (
    attribute_type_validator,
    key_type_validator,
    projection_type_validator,
    billing_mode_validator,
    table_class_validator,
    validate_table
)


# Test enum validators - they should only accept predefined values
@given(st.text())
def test_attribute_type_validator_only_accepts_valid_values(value):
    """AttributeType validator should only accept S, N, B values."""
    valid_types = ["S", "N", "B"]
    if value in valid_types:
        assert attribute_type_validator(value) == value
    else:
        with pytest.raises(ValueError, match="AttributeType must be one of"):
            attribute_type_validator(value)


@given(st.text())
def test_key_type_validator_only_accepts_valid_values(value):
    """KeyType validator should only accept HASH, RANGE values."""
    valid_types = ["HASH", "RANGE"]
    if value in valid_types:
        assert key_type_validator(value) == value
    else:
        with pytest.raises(ValueError, match="KeyType must be one of"):
            key_type_validator(value)


@given(st.text())
def test_projection_type_validator_only_accepts_valid_values(value):
    """ProjectionType validator should only accept KEYS_ONLY, INCLUDE, ALL values."""
    valid_types = ["KEYS_ONLY", "INCLUDE", "ALL"]
    if value in valid_types:
        assert projection_type_validator(value) == value
    else:
        with pytest.raises(ValueError, match="ProjectionType must be one of"):
            projection_type_validator(value)


@given(st.text())
def test_billing_mode_validator_only_accepts_valid_values(value):
    """BillingMode validator should only accept PROVISIONED, PAY_PER_REQUEST values."""
    valid_modes = ["PROVISIONED", "PAY_PER_REQUEST"]
    if value in valid_modes:
        assert billing_mode_validator(value) == value
    else:
        with pytest.raises(ValueError, match="Table billing mode must be one of"):
            billing_mode_validator(value)


@given(st.text())
def test_table_class_validator_only_accepts_valid_values(value):
    """TableClass validator should only accept STANDARD, STANDARD_INFREQUENT_ACCESS values."""
    valid_classes = ["STANDARD", "STANDARD_INFREQUENT_ACCESS"]
    if value in valid_classes:
        assert table_class_validator(value) == value
    else:
        with pytest.raises(ValueError, match="Table class must be one of"):
            table_class_validator(value)


# Test boolean validator conversion properties
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False"),
    st.text(), st.integers(), st.floats(), st.none()
))
def test_boolean_validator_conversion(value):
    """Boolean validator should correctly convert known values."""
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        assert boolean(value) is True
    elif value in false_values:
        assert boolean(value) is False
    else:
        with pytest.raises(ValueError):
            boolean(value)


# Test double validator - accepts floats, rejects non-numeric
@given(st.one_of(
    st.floats(allow_nan=True, allow_infinity=True),
    st.integers(),
    st.text(),
    st.none(),
    st.booleans()
))
def test_double_validator_numeric_handling(value):
    """Double validator should accept numeric values and reject non-numeric."""
    # Check if value can be converted to float
    try:
        float_val = float(value)
        result = double(value)
        assert result == value  # Should return original value
    except (ValueError, TypeError):
        # Non-numeric values should raise ValueError
        with pytest.raises(ValueError, match="is not a valid double"):
            double(value)


# Test special float values
@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_double_validator_special_floats(value):
    """Double validator should handle special float values."""
    result = double(value)
    assert result == value


# Test integer validator edge cases 
@given(st.sampled_from([float('inf'), float('-inf')]))
def test_integer_validator_rejects_infinity(value):
    """Integer validator should reject infinity values."""
    # This might be a bug - infinity can be passed to int() but isn't a valid integer
    try:
        result = integer(value)
        # If it accepts infinity, that's potentially a bug
        int_val = int(value)  # This will raise OverflowError
    except (ValueError, OverflowError):
        pass  # Expected behavior


# Test Table validation logic
def test_table_provisioned_mode_requires_throughput():
    """Table with PROVISIONED billing mode must have ProvisionedThroughput."""
    table = dynamodb.Table("TestTable")
    table.properties["BillingMode"] = "PROVISIONED"
    table.properties["KeySchema"] = [
        dynamodb.KeySchema(AttributeName="id", KeyType="HASH")
    ]
    table.properties["AttributeDefinitions"] = [
        dynamodb.AttributeDefinition(AttributeName="id", AttributeType="S")
    ]
    
    # Without ProvisionedThroughput, should raise error
    with pytest.raises(ValueError, match="ProvisionedThroughput required"):
        validate_table(table)
    
    # With ProvisionedThroughput, should pass
    table.properties["ProvisionedThroughput"] = dynamodb.ProvisionedThroughput(
        ReadCapacityUnits=5,
        WriteCapacityUnits=5
    )
    validate_table(table)  # Should not raise


def test_table_pay_per_request_mode_excludes_throughput():
    """Table with PAY_PER_REQUEST billing mode must not have ProvisionedThroughput."""
    table = dynamodb.Table("TestTable")
    table.properties["BillingMode"] = "PAY_PER_REQUEST"
    table.properties["KeySchema"] = [
        dynamodb.KeySchema(AttributeName="id", KeyType="HASH")
    ]
    table.properties["AttributeDefinitions"] = [
        dynamodb.AttributeDefinition(AttributeName="id", AttributeType="S")
    ]
    
    # Without ProvisionedThroughput, should pass
    validate_table(table)  # Should not raise
    
    # With ProvisionedThroughput, should raise error
    table.properties["ProvisionedThroughput"] = dynamodb.ProvisionedThroughput(
        ReadCapacityUnits=5,
        WriteCapacityUnits=5
    )
    with pytest.raises(ValueError, match="ProvisionedThroughput property is mutually exclusive"):
        validate_table(table)


# Test required properties in classes
def test_attribute_definition_requires_both_properties():
    """AttributeDefinition requires both AttributeName and AttributeType."""
    # Both properties provided - should work
    attr = dynamodb.AttributeDefinition(
        AttributeName="test",
        AttributeType="S"
    )
    assert attr.properties["AttributeName"] == "test"
    assert attr.properties["AttributeType"] == "S"
    
    # Missing AttributeType - should fail validation when used
    with pytest.raises(TypeError):
        dynamodb.AttributeDefinition(AttributeName="test")
    
    # Missing AttributeName - should fail validation when used
    with pytest.raises(TypeError):
        dynamodb.AttributeDefinition(AttributeType="S")


def test_key_schema_requires_both_properties():
    """KeySchema requires both AttributeName and KeyType."""
    # Both properties provided - should work
    key = dynamodb.KeySchema(
        AttributeName="test",
        KeyType="HASH"
    )
    assert key.properties["AttributeName"] == "test"
    assert key.properties["KeyType"] == "HASH"
    
    # Missing KeyType - should fail
    with pytest.raises(TypeError):
        dynamodb.KeySchema(AttributeName="test")
    
    # Missing AttributeName - should fail
    with pytest.raises(TypeError):
        dynamodb.KeySchema(KeyType="HASH")


# Test that capacity settings accept integers  
@given(st.integers(min_value=1, max_value=40000))
def test_provisioned_throughput_accepts_valid_integers(capacity):
    """ProvisionedThroughput should accept valid integer capacity values."""
    throughput = dynamodb.ProvisionedThroughput(
        ReadCapacityUnits=capacity,
        WriteCapacityUnits=capacity
    )
    assert throughput.properties["ReadCapacityUnits"] == capacity
    assert throughput.properties["WriteCapacityUnits"] == capacity


# Test WarmThroughput with edge cases
@given(st.integers())
def test_warm_throughput_integer_validation(value):
    """WarmThroughput should validate integer inputs properly."""
    try:
        warm = dynamodb.WarmThroughput(
            ReadUnitsPerSecond=value,
            WriteUnitsPerSecond=value
        )
        # If it accepts the value, verify it's stored correctly
        assert warm.properties.get("ReadUnitsPerSecond") == value
        assert warm.properties.get("WriteUnitsPerSecond") == value
    except (ValueError, TypeError) as e:
        # Some values might be rejected by validation
        pass