#!/usr/bin/env python3
"""Property-based tests for troposphere.cloudtrail module."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloudtrail as cloudtrail
from troposphere import validators


# Test 1: Boolean validator property
# Evidence: validators/__init__.py lines 38-43 show specific accepted values
@given(value=st.one_of(
    st.booleans(),
    st.integers(),
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_validator_consistency(value):
    """Test that boolean validator accepts only documented values."""
    accepted_true = [True, 1, "1", "true", "True"]
    accepted_false = [False, 0, "0", "false", "False"]
    
    try:
        result = validators.boolean(value)
        # If it succeeded, value must be in accepted lists
        if result is True:
            assert value in accepted_true, f"Value {value!r} returned True but not in accepted_true list"
        else:
            assert result is False
            assert value in accepted_false, f"Value {value!r} returned False but not in accepted_false list"
    except (ValueError, TypeError):
        # If it failed, value must NOT be in accepted lists
        assert value not in accepted_true + accepted_false, f"Value {value!r} should have been accepted"


# Test 2: Integer validator property
# Evidence: validators/__init__.py lines 46-52 show it validates via int() conversion
@given(value=st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_consistency(value):
    """Test that integer validator behavior matches int() conversion."""
    try:
        result = validators.integer(value)
        # If validator succeeded, int() should also succeed
        int_value = int(value)
        # And the result should still be convertible
        assert int(result) == int_value
    except (ValueError, TypeError):
        # If validator failed, int() should also fail
        try:
            int(value)
            # If int() succeeded, validator should have too
            assert False, f"validators.integer failed but int() succeeded for {value!r}"
        except (ValueError, TypeError):
            pass  # Both failed as expected


# Test 3: Positive integer validator property
# Evidence: validators/__init__.py lines 55-59 check for >= 0
@given(value=st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    st.text()
))
def test_positive_integer_validator(value):
    """Test that positive_integer validator only accepts non-negative integers."""
    try:
        result = validators.positive_integer(value)
        # If it succeeded, value must be convertible to int and >= 0
        int_value = int(value)
        assert int_value >= 0, f"positive_integer accepted negative value: {value}"
        assert result == value  # Should return original value
    except (ValueError, TypeError):
        # If it failed, either int() fails or value is negative
        try:
            int_value = int(value)
            assert int_value < 0, f"positive_integer rejected non-negative value: {value}"
        except (ValueError, TypeError):
            pass  # Not an integer at all


# Test 4: Required properties enforcement
# Evidence: cloudtrail.py shows many classes with required properties (marked True)
@given(
    location=st.text(min_size=1),
    dest_type=st.text(min_size=1),
    include_location=st.booleans(),
    include_type=st.booleans()
)
def test_destination_required_properties(location, dest_type, include_location, include_type):
    """Test that Destination enforces its required properties."""
    # Destination requires both Location and Type (lines 19-20)
    kwargs = {}
    if include_location:
        kwargs["Location"] = location
    if include_type:
        kwargs["Type"] = dest_type
    
    try:
        dest = cloudtrail.Destination(**kwargs)
        # If successful, both required properties must be present
        assert include_location and include_type, "Destination created without required properties"
        # And they should be retrievable
        assert dest.Location == location
        assert dest.Type == dest_type
    except ValueError as e:
        # Should fail if missing required properties
        assert not (include_location and include_type), f"Destination failed with all required properties: {e}"


# Test 5: Trail S3BucketName and IsLogging requirements
# Evidence: Trail requires IsLogging (line 217) and S3BucketName (line 221)
@given(
    bucket_name=st.text(min_size=1),
    is_logging=st.booleans(),
    include_bucket=st.booleans(),
    include_logging=st.booleans()
)
def test_trail_required_properties(bucket_name, is_logging, include_bucket, include_logging):
    """Test that Trail enforces its required properties."""
    kwargs = {}
    if include_bucket:
        kwargs["S3BucketName"] = bucket_name
    if include_logging:
        kwargs["IsLogging"] = is_logging
    
    try:
        trail = cloudtrail.Trail("TestTrail", **kwargs)
        # If successful, both required properties must be present
        assert include_bucket and include_logging, "Trail created without required properties"
        assert trail.S3BucketName == bucket_name
        assert trail.IsLogging == is_logging
    except ValueError as e:
        # Should fail if missing required properties
        assert not (include_bucket and include_logging), f"Trail failed with all required properties: {e}"


# Test 6: to_dict/from_dict round-trip property
# Evidence: BaseAWSObject has to_dict (line 337) and from_dict (line 406) methods
@given(
    bucket_name=st.text(min_size=1, max_size=63).filter(lambda x: x.replace('-', '').replace('.', '').isalnum()),
    is_logging=st.booleans(),
    trail_name=st.text(min_size=1, max_size=128).filter(lambda x: x.isalnum()),
    is_multi_region=st.booleans(),
    enable_validation=st.booleans()
)
@settings(max_examples=100)
def test_trail_round_trip_property(bucket_name, is_logging, trail_name, is_multi_region, enable_validation):
    """Test that Trail objects survive to_dict -> from_dict conversion."""
    # Create original trail
    original = cloudtrail.Trail(
        "TestTrail",
        S3BucketName=bucket_name,
        IsLogging=is_logging,
        TrailName=trail_name,
        IsMultiRegionTrail=is_multi_region,
        EnableLogFileValidation=enable_validation
    )
    
    # Convert to dict
    trail_dict = original.to_dict()
    
    # Convert back from dict
    properties = trail_dict.get("Properties", {})
    reconstructed = cloudtrail.Trail.from_dict("TestTrail", properties)
    
    # Properties should match
    assert reconstructed.S3BucketName == bucket_name
    assert reconstructed.IsLogging == is_logging
    assert reconstructed.TrailName == trail_name
    assert reconstructed.IsMultiRegionTrail == is_multi_region
    assert reconstructed.EnableLogFileValidation == enable_validation


# Test 7: EventDataStore RetentionPeriod integer validation
# Evidence: EventDataStore has RetentionPeriod with integer validator (line 159)
@given(retention=st.one_of(
    st.integers(min_value=-100, max_value=10000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans()
))
def test_eventdatastore_retention_validation(retention):
    """Test that EventDataStore validates RetentionPeriod as integer."""
    try:
        store = cloudtrail.EventDataStore("TestStore", RetentionPeriod=retention)
        # If successful, retention must be integer-convertible
        int_value = int(retention)
        assert store.RetentionPeriod == retention
    except (ValueError, TypeError):
        # If failed, int() should also fail
        try:
            int(retention)
            assert False, f"EventDataStore rejected valid integer: {retention}"
        except (ValueError, TypeError):
            pass  # Expected failure


# Test 8: Frequency Value integer validation
# Evidence: Frequency has Value with integer validator (line 46)
@given(
    unit=st.text(min_size=1),
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    )
)
def test_frequency_value_validation(unit, value):
    """Test that Frequency validates Value as integer."""
    try:
        freq = cloudtrail.Frequency(Unit=unit, Value=value)
        # If successful, value must be integer-convertible
        int_value = int(value)
        assert freq.Value == value
        assert freq.Unit == unit
    except (ValueError, TypeError):
        # Either missing required property or invalid integer
        try:
            int(value)
            # If int() works, then it must be missing Unit
            assert False, f"Frequency failed despite valid integer value: {value}"
        except (ValueError, TypeError):
            pass  # Value is not a valid integer