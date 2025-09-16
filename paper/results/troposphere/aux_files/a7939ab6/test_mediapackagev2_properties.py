#!/usr/bin/env python3
"""Property-based tests for troposphere.mediapackagev2 module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.mediapackagev2 as mp2
from troposphere.validators import boolean, integer, double


# Test 1: Boolean validator round-trip property
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]))
def test_boolean_validator_conversion(value):
    """Test that boolean validator properly converts accepted values."""
    result = boolean(value)
    # The function should return True for truthy values, False for falsy values
    if value in [True, 1, "true", "True"]:
        assert result is True
    elif value in [False, 0, "false", "False"]:
        assert result is False


# Test 2: Integer validator accepts valid integers
@given(st.integers(min_value=-10**10, max_value=10**10))
def test_integer_validator_accepts_integers(value):
    """Test that integer validator accepts integer values."""
    result = integer(value)
    assert result == value
    # Should be convertible to int
    assert int(result) == value


# Test 3: Double validator accepts valid floats
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_double_validator_accepts_floats(value):
    """Test that double validator accepts float values."""
    result = double(value)
    assert result == value
    # Should be convertible to float
    assert float(result) == value


# Test 4: Channel class with required properties
@given(
    channel_group=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    channel_name=st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
)
def test_channel_required_properties(channel_group, channel_name):
    """Test that Channel can be created with required properties."""
    # Channel requires ChannelGroupName and ChannelName
    channel = mp2.Channel(
        title="TestChannel",
        ChannelGroupName=channel_group,
        ChannelName=channel_name
    )
    # Should be able to convert to dict
    channel_dict = channel.to_dict()
    assert channel_dict["Type"] == "AWS::MediaPackageV2::Channel"
    assert channel_dict["Properties"]["ChannelGroupName"] == channel_group
    assert channel_dict["Properties"]["ChannelName"] == channel_name


# Test 5: Round-trip property for FilterConfiguration
@given(
    clip_start=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    end=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    manifest_filter=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    start=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    time_delay=st.one_of(st.none(), st.integers(min_value=0, max_value=86400))
)
def test_filter_configuration_round_trip(clip_start, end, manifest_filter, start, time_delay):
    """Test round-trip property for FilterConfiguration."""
    # Create FilterConfiguration with optional properties
    kwargs = {}
    if clip_start is not None:
        kwargs["ClipStartTime"] = clip_start
    if end is not None:
        kwargs["End"] = end
    if manifest_filter is not None:
        kwargs["ManifestFilter"] = manifest_filter
    if start is not None:
        kwargs["Start"] = start
    if time_delay is not None:
        kwargs["TimeDelaySeconds"] = time_delay
    
    if not kwargs:
        # At least one property should be set for meaningful test
        return
    
    config = mp2.FilterConfiguration(**kwargs)
    config_dict = config.to_dict()
    
    # Verify all set properties are in the dict
    for key, value in kwargs.items():
        assert config_dict.get(key) == value


# Test 6: StartTag with required TimeOffset
@given(
    precise=st.booleans(),
    time_offset=st.floats(min_value=0.0, max_value=86400.0, allow_nan=False, allow_infinity=False)
)
def test_start_tag_properties(precise, time_offset):
    """Test StartTag with required TimeOffset property."""
    start_tag = mp2.StartTag(
        Precise=precise,
        TimeOffset=time_offset
    )
    tag_dict = start_tag.to_dict()
    assert tag_dict["TimeOffset"] == time_offset
    assert tag_dict["Precise"] == precise


# Test 7: OriginEndpoint with multiple manifest configurations
@given(
    channel_group=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    channel_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    endpoint_name=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    container_type=st.sampled_from(["TS", "CMAF"]),
    num_dash_manifests=st.integers(min_value=0, max_value=3),
    num_hls_manifests=st.integers(min_value=0, max_value=3)
)
def test_origin_endpoint_with_manifests(channel_group, channel_name, endpoint_name, container_type, num_dash_manifests, num_hls_manifests):
    """Test OriginEndpoint can handle multiple manifest configurations."""
    # Create manifest configurations
    dash_manifests = []
    for i in range(num_dash_manifests):
        dash_manifests.append(mp2.DashManifestConfiguration(
            ManifestName=f"dash_manifest_{i}"
        ))
    
    hls_manifests = []
    for i in range(num_hls_manifests):
        hls_manifests.append(mp2.HlsManifestConfiguration(
            ManifestName=f"hls_manifest_{i}"
        ))
    
    kwargs = {
        "title": "TestEndpoint",
        "ChannelGroupName": channel_group,
        "ChannelName": channel_name,
        "OriginEndpointName": endpoint_name,
        "ContainerType": container_type
    }
    
    if dash_manifests:
        kwargs["DashManifests"] = dash_manifests
    if hls_manifests:
        kwargs["HlsManifests"] = hls_manifests
    
    endpoint = mp2.OriginEndpoint(**kwargs)
    endpoint_dict = endpoint.to_dict()
    
    assert endpoint_dict["Type"] == "AWS::MediaPackageV2::OriginEndpoint"
    assert endpoint_dict["Properties"]["ChannelGroupName"] == channel_group
    assert endpoint_dict["Properties"]["ChannelName"] == channel_name
    assert endpoint_dict["Properties"]["OriginEndpointName"] == endpoint_name
    assert endpoint_dict["Properties"]["ContainerType"] == container_type
    
    if dash_manifests:
        assert len(endpoint_dict["Properties"]["DashManifests"]) == num_dash_manifests
    if hls_manifests:
        assert len(endpoint_dict["Properties"]["HlsManifests"]) == num_hls_manifests


# Test 8: EncryptionContractConfiguration required properties
@given(
    audio_preset=st.text(min_size=1, max_size=50),
    video_preset=st.text(min_size=1, max_size=50)
)
def test_encryption_contract_required_properties(audio_preset, video_preset):
    """Test EncryptionContractConfiguration enforces required properties."""
    config = mp2.EncryptionContractConfiguration(
        PresetSpeke20Audio=audio_preset,
        PresetSpeke20Video=video_preset
    )
    config_dict = config.to_dict()
    assert config_dict["PresetSpeke20Audio"] == audio_preset
    assert config_dict["PresetSpeke20Video"] == video_preset


# Test 9: Complex nested structure with SpekeKeyProvider
@given(
    drm_systems=st.lists(st.sampled_from(["WIDEVINE", "PLAYREADY", "FAIRPLAY"]), min_size=1, max_size=3, unique=True),
    resource_id=st.text(min_size=1, max_size=100),
    role_arn=st.text(min_size=1, max_size=200),
    url=st.text(min_size=10, max_size=200)
)
def test_speke_key_provider_nested_structure(drm_systems, resource_id, role_arn, url):
    """Test SpekeKeyProvider with nested EncryptionContractConfiguration."""
    # Create nested structure
    encryption_contract = mp2.EncryptionContractConfiguration(
        PresetSpeke20Audio="PRESET_AUDIO_1",
        PresetSpeke20Video="PRESET_VIDEO_1"
    )
    
    speke = mp2.SpekeKeyProvider(
        DrmSystems=drm_systems,
        EncryptionContractConfiguration=encryption_contract,
        ResourceId=resource_id,
        RoleArn=role_arn,
        Url=url
    )
    
    speke_dict = speke.to_dict()
    
    # Verify the structure is preserved
    assert speke_dict["DrmSystems"] == drm_systems
    assert speke_dict["ResourceId"] == resource_id
    assert speke_dict["RoleArn"] == role_arn
    assert speke_dict["Url"] == url
    assert "EncryptionContractConfiguration" in speke_dict
    assert speke_dict["EncryptionContractConfiguration"]["PresetSpeke20Audio"] == "PRESET_AUDIO_1"
    assert speke_dict["EncryptionContractConfiguration"]["PresetSpeke20Video"] == "PRESET_VIDEO_1"


if __name__ == "__main__":
    print("Running property-based tests for troposphere.mediapackagev2...")
    import pytest
    pytest.main([__file__, "-v"])