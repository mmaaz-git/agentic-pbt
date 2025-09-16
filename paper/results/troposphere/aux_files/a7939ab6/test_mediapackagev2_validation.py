#!/usr/bin/env python3
"""Deep validation tests for troposphere.mediapackagev2 module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example, HealthCheck
import troposphere.mediapackagev2 as mp2
from troposphere.validators import boolean, integer, double
from troposphere import Template, AWSHelperFn, Ref
import pytest


# Test 1: Test that boolean("1") returns True not 1
def test_boolean_string_one_returns_true_not_one():
    """The boolean validator for '1' should return True, not 1."""
    result = boolean("1")
    assert result is True
    assert result is not 1
    assert type(result) is bool


# Test 2: Test that boolean("0") returns False not 0
def test_boolean_string_zero_returns_false_not_zero():
    """The boolean validator for '0' should return False, not 0."""
    result = boolean("0")
    assert result is False
    assert result is not 0
    assert type(result) is bool


# Test 3: Test AWSHelperFn objects bypass validation
@given(st.text(min_size=1, max_size=50))
def test_aws_helper_fn_bypass_validation(ref_name):
    """Test that AWSHelperFn objects bypass type validation."""
    # Create a Ref (which is an AWSHelperFn)
    ref = Ref(ref_name)
    
    # This should work even though Ref is not a string
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=ref,  # Using Ref instead of string
        ChannelName="test"
    )
    
    result = channel.to_dict()
    # The Ref should be preserved in the output
    assert "Ref" in str(result["Properties"]["ChannelGroupName"])


# Test 4: Test that validation happens on to_dict() not on instantiation
@given(st.text(min_size=1, max_size=50))
def test_validation_timing(value):
    """Test when validation actually occurs."""
    # Create a Channel with no_validation
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=value,
        ChannelName="test"
    ).no_validation()
    
    # This should work because validation is disabled
    result = channel.to_dict(validation=False)
    assert result["Properties"]["ChannelGroupName"] == value
    
    # Now try with validation enabled
    result2 = channel.to_dict(validation=True)
    # Should still work because do_validation is False on the object
    assert result2["Properties"]["ChannelGroupName"] == value


# Test 5: Test property type coercion with integer validator
@given(
    value=st.one_of(
        st.integers(),
        st.text().filter(lambda x: x.strip() and (x.strip().lstrip('-').isdigit())),
        st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
    )
)
def test_integer_validator_type_preservation(value):
    """Test that integer validator preserves the input type."""
    result = integer(value)
    # The validator should return the original value, not convert it
    assert result == value
    assert type(result) == type(value)
    # But it should be convertible to int
    assert int(result) == int(value)


# Test 6: Test that lists of wrong types are caught
def test_list_validation_with_wrong_types():
    """Test that list properties validate element types."""
    # Try to create DashManifests with wrong types
    with pytest.raises((TypeError, AttributeError)):
        endpoint = mp2.OriginEndpoint(
            title="TestEndpoint",
            ChannelGroupName="test",
            ChannelName="test",
            OriginEndpointName="test",
            ContainerType="TS",
            DashManifests=["string", "instead", "of", "objects"]
        )


# Test 7: Test Tags property (which is a special AWSHelperFn)
@given(
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=5
    )
)
def test_tags_property(tags):
    """Test that Tags property works correctly."""
    from troposphere import Tags
    
    # Create Tags object
    tag_list = Tags(**tags)
    
    # Use it in a Channel
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName="test",
        ChannelName="test",
        Tags=tag_list
    )
    
    result = channel.to_dict()
    # Tags should be in the properties
    if tags:
        assert "Tags" in result["Properties"]


# Test 8: Test property deletion/removal
@given(
    description=st.text(min_size=1, max_size=100)
)
def test_optional_property_deletion(description):
    """Test behavior when optional properties are deleted."""
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName="test",
        ChannelName="test",
        Description=description
    )
    
    # Verify it's set
    assert channel.Description == description
    
    # Try to delete it
    try:
        del channel.Description
    except (AttributeError, KeyError):
        # Deletion might not be supported
        pass
    
    # The object should still be valid
    result = channel.to_dict()
    assert result["Type"] == "AWS::MediaPackageV2::Channel"


# Test 9: Test setting properties to empty lists
def test_empty_list_properties():
    """Test that empty lists are handled correctly."""
    endpoint = mp2.OriginEndpoint(
        title="TestEndpoint",
        ChannelGroupName="test",
        ChannelName="test",
        OriginEndpointName="test",
        ContainerType="TS",
        DashManifests=[],  # Empty list
        HlsManifests=[]    # Empty list
    )
    
    result = endpoint.to_dict()
    # Empty lists might be omitted or preserved
    props = result["Properties"]
    # Check if they're present
    if "DashManifests" in props:
        assert props["DashManifests"] == []
    if "HlsManifests" in props:
        assert props["HlsManifests"] == []


# Test 10: Test very long strings
@given(
    long_string=st.text(min_size=1000, max_size=10000)
)
def test_very_long_strings(long_string):
    """Test that very long strings are handled correctly."""
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=long_string,
        ChannelName="test"
    )
    
    result = channel.to_dict()
    assert result["Properties"]["ChannelGroupName"] == long_string


# Test 11: Test property names are case-sensitive
def test_property_case_sensitivity():
    """Test that property names are case-sensitive."""
    # Try with wrong case
    with pytest.raises(AttributeError):
        channel = mp2.Channel(
            title="TestChannel",
            channelgroupname="test",  # Wrong case
            ChannelName="test"
        )


# Test 12: Test that _from_dict validates types
@given(
    invalid_value=st.one_of(
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text())
    )
)
def test_from_dict_type_validation(invalid_value):
    """Test that _from_dict validates property types."""
    # Try to create from dict with wrong type
    try:
        channel = mp2.Channel._from_dict(
            title="TestChannel",
            ChannelGroupName=invalid_value,  # Should be string
            ChannelName="test"
        )
        # If it succeeds, check if coercion happened
        if not isinstance(invalid_value, str):
            # This is unexpected - it should have failed
            result = channel.to_dict()
            # Check what happened to the value
            actual_value = result["Properties"]["ChannelGroupName"]
            # It might have been coerced to string
            assert str(invalid_value) == actual_value or invalid_value == actual_value
    except (TypeError, AttributeError, ValueError):
        # Expected to fail with wrong types
        assert not isinstance(invalid_value, str)


# Test 13: Test circular reference detection
def test_circular_reference():
    """Test handling of circular references in nested structures."""
    # Create a FilterConfiguration
    config1 = mp2.FilterConfiguration(Start="test")
    
    # Try to create a circular reference (this should fail or be handled)
    # Note: This is more of a theoretical test as the current structure doesn't allow it
    # But it's good to verify the behavior
    try:
        # Can't actually create circular refs with current structure
        # But test that nested structures work
        endpoint = mp2.OriginEndpoint(
            title="TestEndpoint",
            ChannelGroupName="test",
            ChannelName="test",
            OriginEndpointName="test",
            ContainerType="TS",
            HlsManifests=[
                mp2.HlsManifestConfiguration(
                    ManifestName="manifest1",
                    FilterConfiguration=config1
                )
            ]
        )
        result = endpoint.to_dict()
        assert "HlsManifests" in result["Properties"]
    except RecursionError:
        # If circular refs cause recursion, that's a bug
        assert False, "Circular reference caused RecursionError"


# Test 14: Test that double validator preserves string type for numeric strings
@given(
    value=st.one_of(
        st.from_regex(r'^-?\d+\.?\d*$', fullmatch=True),
        st.sampled_from(["1", "1.0", "-1", "0.5", "123.456", "-999.99"])
    )
)
@settings(suppress_health_check=[])
def test_double_validator_string_preservation(value):
    """Test that double validator preserves string input."""
    try:
        result = double(value)
        # Should preserve the original type
        assert type(result) == type(value)
        assert result == value
        # But should be convertible to float
        float(result)
    except ValueError:
        # Some strings might not be valid floats
        pass


if __name__ == "__main__":
    print("Running validation tests for troposphere.mediapackagev2...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])