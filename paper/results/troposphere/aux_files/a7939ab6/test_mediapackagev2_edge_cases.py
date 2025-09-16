#!/usr/bin/env python3
"""Edge case tests for troposphere.mediapackagev2 module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.mediapackagev2 as mp2
from troposphere.validators import boolean, integer, double
from troposphere import Template
import pytest


# Test 1: Boolean validator edge cases with string variations
@given(st.text())
@example("1")  # Should pass
@example("0")  # Should pass
@example(" true ")  # Should fail - has spaces
@example("TRUE")  # Should fail - all caps
@example("yes")  # Should fail - not a valid value
@example("")  # Should fail - empty string
def test_boolean_validator_edge_cases(value):
    """Test boolean validator with various string inputs."""
    try:
        result = boolean(value)
        # Should only succeed for specific values
        assert value in ["1", "0", "true", "false", "True", "False"] or value in [True, False, 1, 0]
    except ValueError:
        # Should fail for anything else
        assert value not in ["1", "0", "true", "false", "True", "False", True, False, 1, 0]


# Test 2: Integer validator with string representations
@given(st.one_of(
    st.text(),
    st.floats(),
    st.integers(),
    st.sampled_from([None, [], {}, float('inf'), float('-inf'), float('nan')])
))
def test_integer_validator_comprehensive(value):
    """Test integer validator with various input types."""
    try:
        result = integer(value)
        # If it succeeds, the value should be convertible to int
        int_val = int(result)
        # Check that the conversion is valid
        if isinstance(value, str):
            assert int(value) == int_val
        elif isinstance(value, (int, float)):
            assert int(value) == int_val
    except (ValueError, TypeError, OverflowError):
        # Should fail for non-integer-convertible values
        pass


# Test 3: Testing class instantiation with None values
@given(
    channel_group=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    channel_name=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_channel_with_none_required_fields(channel_group, channel_name):
    """Test that Channel properly handles None in required fields."""
    if channel_group is None or channel_name is None:
        # Should fail when required fields are None
        with pytest.raises((TypeError, AttributeError, ValueError)):
            channel = mp2.Channel(
                title="TestChannel",
                ChannelGroupName=channel_group,
                ChannelName=channel_name
            )
    else:
        # Should succeed with valid values
        channel = mp2.Channel(
            title="TestChannel",
            ChannelGroupName=channel_group,
            ChannelName=channel_name
        )
        assert channel.ChannelGroupName == channel_group


# Test 4: Testing property assignment after instantiation
@given(
    initial_value=st.text(min_size=1, max_size=50),
    new_value=st.one_of(
        st.text(min_size=1, max_size=50),
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_property_reassignment(initial_value, new_value):
    """Test reassigning properties after object creation."""
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=initial_value,
        ChannelName="test"
    )
    
    # Try to reassign the property
    try:
        channel.ChannelGroupName = new_value
        # Should only succeed if new_value is a string
        assert isinstance(new_value, str)
        assert channel.ChannelGroupName == new_value
    except (TypeError, AttributeError):
        # Should fail for non-string values
        assert not isinstance(new_value, str)


# Test 5: Testing lists with wrong element types
@given(
    manifests=st.lists(
        st.one_of(
            st.text(),
            st.integers(),
            st.dictionaries(st.text(), st.text()),
            st.none()
        ),
        min_size=1,
        max_size=5
    )
)
def test_origin_endpoint_invalid_manifest_lists(manifests):
    """Test OriginEndpoint with invalid manifest list types."""
    try:
        endpoint = mp2.OriginEndpoint(
            title="TestEndpoint",
            ChannelGroupName="test",
            ChannelName="test",
            OriginEndpointName="test",
            ContainerType="TS",
            DashManifests=manifests  # Should be list of DashManifestConfiguration
        )
        # If this succeeds, all elements should be valid
        # This is unlikely since we're passing wrong types
        endpoint.to_dict()
        assert False, "Should not accept invalid manifest types"
    except (TypeError, AttributeError, ValueError):
        # Expected to fail with wrong types
        pass


# Test 6: Testing integer boundaries in FilterConfiguration
@given(
    time_delay=st.one_of(
        st.just(-1),  # Negative
        st.just(0),   # Zero
        st.just(2**31 - 1),  # Max 32-bit int
        st.just(2**31),      # Overflow 32-bit
        st.just(2**63 - 1),  # Max 64-bit int
        st.just(2**63),      # Overflow 64-bit
        st.floats()          # Float values
    )
)
def test_filter_configuration_integer_boundaries(time_delay):
    """Test integer property with boundary values."""
    try:
        config = mp2.FilterConfiguration(
            TimeDelaySeconds=time_delay
        )
        result = config.to_dict()
        # If it succeeds, check the value is preserved
        assert result["TimeDelaySeconds"] == time_delay
    except (ValueError, TypeError, OverflowError):
        # May fail for invalid integer values
        pass


# Test 7: Testing double/float edge cases in StartTag
@given(
    time_offset=st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
        st.just(0.0),
        st.just(-0.0),
        st.floats(min_value=-1e308, max_value=1e308),
        st.text()  # String representation of numbers
    )
)
def test_start_tag_float_edge_cases(time_offset):
    """Test StartTag TimeOffset with edge case float values."""
    try:
        tag = mp2.StartTag(
            TimeOffset=time_offset
        )
        result = tag.to_dict()
        # Check if the value is preserved correctly
        if isinstance(time_offset, float):
            if time_offset != time_offset:  # NaN check
                assert result["TimeOffset"] != result["TimeOffset"]
            else:
                assert result["TimeOffset"] == time_offset
    except (ValueError, TypeError, OverflowError):
        # Should fail for invalid float values
        pass


# Test 8: Testing empty strings in required fields
@given(
    channel_group=st.sampled_from(["", " ", "\t", "\n", "valid"]),
    channel_name=st.sampled_from(["", " ", "\t", "\n", "valid"])
)
def test_channel_empty_strings(channel_group, channel_name):
    """Test Channel with empty or whitespace-only strings."""
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=channel_group,
        ChannelName=channel_name
    )
    result = channel.to_dict()
    # Empty strings should be preserved
    assert result["Properties"]["ChannelGroupName"] == channel_group
    assert result["Properties"]["ChannelName"] == channel_name


# Test 9: Testing _from_dict round-trip with complex nested structures
@given(
    drm_systems=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3),
    resource_id=st.text(min_size=1, max_size=50),
    role_arn=st.text(min_size=1, max_size=100),
    url=st.text(min_size=1, max_size=100),
    audio_preset=st.text(min_size=1, max_size=50),
    video_preset=st.text(min_size=1, max_size=50)
)
def test_speke_from_dict_round_trip(drm_systems, resource_id, role_arn, url, audio_preset, video_preset):
    """Test _from_dict round-trip for SpekeKeyProvider."""
    # Create the object
    encryption_contract = mp2.EncryptionContractConfiguration(
        PresetSpeke20Audio=audio_preset,
        PresetSpeke20Video=video_preset
    )
    
    speke = mp2.SpekeKeyProvider(
        DrmSystems=drm_systems,
        EncryptionContractConfiguration=encryption_contract,
        ResourceId=resource_id,
        RoleArn=role_arn,
        Url=url
    )
    
    # Convert to dict
    speke_dict = speke.to_dict()
    
    # Try to recreate from dict
    speke2 = mp2.SpekeKeyProvider._from_dict(**speke_dict)
    
    # Convert back to dict and compare
    speke2_dict = speke2.to_dict()
    
    # The dicts should be identical
    assert speke_dict == speke2_dict


# Test 10: Testing with Unicode and special characters
@given(
    channel_name=st.text(
        alphabet=st.characters(min_codepoint=0, max_codepoint=0x10ffff),
        min_size=1,
        max_size=50
    ).filter(lambda x: '\x00' not in x)  # Filter out null bytes
)
def test_unicode_in_string_properties(channel_name):
    """Test that Unicode characters are handled correctly in string properties."""
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName="TestGroup",
        ChannelName=channel_name
    )
    result = channel.to_dict()
    assert result["Properties"]["ChannelName"] == channel_name


# Test 11: Test boolean edge case - the string "1" 
def test_boolean_string_one():
    """Test that boolean validator accepts the string '1'."""
    result = boolean("1")
    assert result is True


# Test 12: Test boolean edge case - the string "0"
def test_boolean_string_zero():
    """Test that boolean validator accepts the string '0'."""
    result = boolean("0")
    assert result is False


if __name__ == "__main__":
    print("Running edge case tests for troposphere.mediapackagev2...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])