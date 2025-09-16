#!/usr/bin/env python3
"""Property-based tests for troposphere.kinesis module"""

import pytest
from hypothesis import given, strategies as st, assume
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.kinesis import (
    ResourcePolicy,
    StreamEncryption,
    StreamModeDetails,
    Stream,
    StreamConsumer,
)
from troposphere.validators.kinesis import kinesis_stream_mode, validate_tags_or_list


# Test 1: kinesis_stream_mode validator error message bug
@given(st.text().filter(lambda x: x not in ["ON_DEMAND", "PROVISIONED"]))
def test_kinesis_stream_mode_error_message(invalid_mode):
    """Test that kinesis_stream_mode error message mentions 'ContentType' incorrectly"""
    try:
        kinesis_stream_mode(invalid_mode)
        assert False, f"Expected ValueError for invalid mode: {invalid_mode}"
    except ValueError as e:
        error_msg = str(e)
        # The bug: error message says "ContentType" but should reference StreamMode
        assert "ContentType" in error_msg, f"Error message doesn't contain 'ContentType': {error_msg}"


# Test 2: kinesis_stream_mode accepts valid values
@given(st.sampled_from(["ON_DEMAND", "PROVISIONED"]))
def test_kinesis_stream_mode_valid_values(valid_mode):
    """Test that kinesis_stream_mode accepts valid values"""
    result = kinesis_stream_mode(valid_mode)
    assert result == valid_mode


# Test 3: kinesis_stream_mode rejects invalid values
@given(st.text().filter(lambda x: x not in ["ON_DEMAND", "PROVISIONED"]))
def test_kinesis_stream_mode_invalid_values(invalid_mode):
    """Test that kinesis_stream_mode rejects invalid values"""
    with pytest.raises(ValueError):
        kinesis_stream_mode(invalid_mode)


# Test 4: StreamModeDetails property validation
@given(st.sampled_from(["ON_DEMAND", "PROVISIONED"]))
def test_stream_mode_details_valid(mode):
    """Test that StreamModeDetails accepts valid stream modes"""
    smd = StreamModeDetails(StreamMode=mode)
    assert smd.properties["StreamMode"] == mode


# Test 5: StreamModeDetails rejects invalid modes  
@given(st.text().filter(lambda x: x not in ["ON_DEMAND", "PROVISIONED", ""]))
def test_stream_mode_details_invalid(invalid_mode):
    """Test that StreamModeDetails rejects invalid stream modes"""
    assume(invalid_mode)  # Skip empty strings
    try:
        smd = StreamModeDetails(StreamMode=invalid_mode)
        # If creation succeeds, validation should fail on to_dict()
        smd.to_dict()
        assert False, f"Expected validation error for invalid mode: {invalid_mode}"
    except (ValueError, TypeError):
        pass  # Expected


# Test 6: Required properties validation for ResourcePolicy
def test_resource_policy_required_properties():
    """Test that ResourcePolicy enforces required properties"""
    # Missing required properties should fail validation
    rp = ResourcePolicy("TestPolicy")
    with pytest.raises(ValueError) as exc_info:
        rp.to_dict()
    assert "required" in str(exc_info.value).lower()


# Test 7: Required properties validation for StreamConsumer
def test_stream_consumer_required_properties():
    """Test that StreamConsumer enforces required properties"""
    sc = StreamConsumer("TestConsumer")
    with pytest.raises(ValueError) as exc_info:
        sc.to_dict()
    assert "required" in str(exc_info.value).lower()


# Test 8: StreamEncryption required properties
def test_stream_encryption_required_properties():
    """Test that StreamEncryption enforces required properties"""
    se = StreamEncryption()
    with pytest.raises(ValueError) as exc_info:
        se.to_dict()
    assert "required" in str(exc_info.value).lower()


# Test 9: Stream accepts optional properties
@given(
    shard_count=st.integers(min_value=1, max_value=100),
    retention_hours=st.integers(min_value=24, max_value=168)
)
def test_stream_optional_properties(shard_count, retention_hours):
    """Test that Stream correctly handles optional integer properties"""
    stream = Stream(
        "TestStream",
        ShardCount=shard_count,
        RetentionPeriodHours=retention_hours
    )
    props = stream.to_dict()["Properties"]
    assert props["ShardCount"] == shard_count
    assert props["RetentionPeriodHours"] == retention_hours


# Test 10: Tags validation with lists
@given(st.lists(st.dictionaries(st.text(min_size=1), st.text())))
def test_validate_tags_or_list_with_list(tags_list):
    """Test that validate_tags_or_list accepts lists"""
    result = validate_tags_or_list(tags_list)
    assert result == tags_list


# Test 11: Tags validation rejects invalid types
@given(st.one_of(st.integers(), st.floats(), st.text()))
def test_validate_tags_or_list_invalid_types(invalid_input):
    """Test that validate_tags_or_list rejects non-list/Tags types"""
    with pytest.raises(ValueError) as exc_info:
        validate_tags_or_list(invalid_input)
    assert "must be either Tags or list" in str(exc_info.value)