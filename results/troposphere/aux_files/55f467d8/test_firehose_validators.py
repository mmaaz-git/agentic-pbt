#!/usr/bin/env python3
"""Property-based tests for troposphere.firehose validators using Hypothesis."""

import re
from hypothesis import given, strategies as st, assume
from troposphere.validators.firehose import (
    processor_type_validator,
    delivery_stream_type_validator,
    index_rotation_period_validator,
    s3_backup_mode_elastic_search_validator,
    s3_backup_mode_extended_s3_validator,
)


# Test 1: Validators should accept all valid values
@given(st.sampled_from(["Lambda", "MetadataExtraction", "RecordDeAggregation", "AppendDelimiterToRecord"]))
def test_processor_type_accepts_valid(value):
    """Processor type validator should accept all documented valid types."""
    result = processor_type_validator(value)
    assert result == value  # Should return the same value


@given(st.sampled_from(["DirectPut", "KinesisStreamAsSource"]))
def test_delivery_stream_type_accepts_valid(value):
    """Delivery stream type validator should accept all documented valid types."""
    result = delivery_stream_type_validator(value)
    assert result == value


@given(st.sampled_from(["NoRotation", "OneHour", "OneDay", "OneWeek", "OneMonth"]))
def test_index_rotation_accepts_valid(value):
    """Index rotation period validator should accept all documented valid types."""
    result = index_rotation_period_validator(value)
    assert result == value


@given(st.sampled_from(["FailedDocumentsOnly", "AllDocuments"]))
def test_s3_backup_mode_elastic_accepts_valid(value):
    """S3 backup mode elastic search validator should accept all documented valid types."""
    result = s3_backup_mode_elastic_search_validator(value)
    assert result == value


@given(st.sampled_from(["Disabled", "Enabled"]))
def test_s3_backup_mode_extended_accepts_valid(value):
    """S3 backup mode extended S3 validator should accept all documented valid types."""
    result = s3_backup_mode_extended_s3_validator(value)
    assert result == value


# Test 2: Validators should reject invalid values
@given(st.text(min_size=1))
def test_processor_type_rejects_invalid(value):
    """Processor type validator should reject values not in valid set."""
    valid_types = ["Lambda", "MetadataExtraction", "RecordDeAggregation", "AppendDelimiterToRecord"]
    assume(value not in valid_types)
    
    try:
        processor_type_validator(value)
        assert False, f"Should have raised ValueError for '{value}'"
    except ValueError as e:
        # Check error message contains all valid types
        error_msg = str(e)
        for valid_type in valid_types:
            assert valid_type in error_msg, f"Error message should mention '{valid_type}'"


@given(st.text(min_size=1))
def test_delivery_stream_type_rejects_invalid(value):
    """Delivery stream type validator should reject values not in valid set."""
    valid_types = ["DirectPut", "KinesisStreamAsSource"]
    assume(value not in valid_types)
    
    try:
        delivery_stream_type_validator(value)
        assert False, f"Should have raised ValueError for '{value}'"
    except ValueError as e:
        error_msg = str(e)
        for valid_type in valid_types:
            assert valid_type in error_msg


# Test 3: Validators should be idempotent
@given(st.sampled_from(["Lambda", "MetadataExtraction", "RecordDeAggregation", "AppendDelimiterToRecord"]))
def test_processor_type_idempotent(value):
    """Calling processor type validator twice should return same result."""
    result1 = processor_type_validator(value)
    result2 = processor_type_validator(result1)
    assert result1 == result2 == value


# Test 4: Validator error messages should follow consistent format
@given(st.text(min_size=1, max_size=100).filter(lambda x: x not in ["DirectPut", "KinesisStreamAsSource"]))
def test_delivery_stream_error_format(value):
    """Error messages should follow consistent format with 'must be one of'."""
    try:
        delivery_stream_type_validator(value)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        assert "must be one of:" in error_msg.lower() or "must be one of :" in error_msg.lower()


# Test 5: Case sensitivity - validators should be case-sensitive
@given(st.sampled_from(["lambda", "LAMBDA", "Lambda"]))
def test_processor_type_case_sensitive(value):
    """Validators should be case-sensitive - only exact matches allowed."""
    if value == "Lambda":
        # This should succeed
        result = processor_type_validator(value)
        assert result == value
    else:
        # These should fail
        try:
            processor_type_validator(value)
            assert False, f"Should have rejected '{value}' (case-sensitive)"
        except ValueError:
            pass  # Expected


# Test 6: Validators should handle None and edge cases appropriately
@given(st.none())
def test_validators_handle_none(value):
    """Validators should handle None values appropriately."""
    # All validators should reject None
    validators = [
        processor_type_validator,
        delivery_stream_type_validator,
        index_rotation_period_validator,
        s3_backup_mode_elastic_search_validator,
        s3_backup_mode_extended_s3_validator,
    ]
    
    for validator in validators:
        try:
            validator(value)
            assert False, f"{validator.__name__} should reject None"
        except (ValueError, TypeError):
            pass  # Expected to raise an error


# Test 7: Validators should handle empty string
@given(st.just(""))
def test_validators_handle_empty_string(value):
    """Validators should reject empty strings."""
    validators = [
        processor_type_validator,
        delivery_stream_type_validator,
        index_rotation_period_validator,
        s3_backup_mode_elastic_search_validator,
        s3_backup_mode_extended_s3_validator,
    ]
    
    for validator in validators:
        try:
            validator(value)
            assert False, f"{validator.__name__} should reject empty string"
        except ValueError:
            pass  # Expected


# Test 8: Test metamorphic property - validator composition
@given(st.sampled_from(["Disabled", "Enabled"]))
def test_s3_backup_validators_distinct(value):
    """Different S3 backup validators should have different valid sets."""
    # extended S3 validator accepts "Disabled" and "Enabled"
    extended_result = s3_backup_mode_extended_s3_validator(value)
    assert extended_result == value
    
    # elastic search validator should reject these values (it uses different values)
    try:
        s3_backup_mode_elastic_search_validator(value)
        assert False, "Elastic search validator should reject extended S3 values"
    except ValueError:
        pass  # Expected - different validators have different valid sets