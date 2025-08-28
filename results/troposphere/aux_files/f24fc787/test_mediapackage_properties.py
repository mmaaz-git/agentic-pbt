"""Property-based tests for troposphere.mediapackage module."""

import sys
import pytest
from hypothesis import given, strategies as st, assume, settings
import string
import json

# Add the venv site-packages to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
from troposphere import Tags
from troposphere.mediapackage import (
    Asset, Channel, OriginEndpoint, PackagingConfiguration, PackagingGroup,
    EgressEndpoint, IngestEndpoint, HlsIngest, LogConfiguration,
    Authorization, EncryptionContractConfiguration, OriginEndpointSpekeKeyProvider,
    OriginEndpointCmafEncryption, OriginEndpointHlsManifest, StreamSelection,
    OriginEndpointCmafPackage, SpekeKeyProvider, OriginEndpointDashEncryption,
    OriginEndpointDashPackage, OriginEndpointHlsEncryption, OriginEndpointHlsPackage,
    MssEncryption, OriginEndpointMssPackage, CmafEncryption, HlsManifest,
    CmafPackage, DashEncryption, DashManifest, DashPackage, HlsEncryption,
    HlsPackage, MssManifest, MssPackage
)


# Strategy for generating valid alphanumeric titles
valid_title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=100
)

# Strategy for invalid titles (containing non-alphanumeric characters)
invalid_title_strategy = st.one_of(
    st.text(min_size=1).filter(lambda s: not s.isalnum()),
    st.just(""),
    st.text(alphabet="!@#$%^&*()_+-=[]{}|;:,.<>?/`~", min_size=1),
    st.text(min_size=1).map(lambda s: s + " "),  # Add space
    st.text(min_size=1).map(lambda s: s + "-"),  # Add hyphen
)


@given(title=invalid_title_strategy)
@settings(max_examples=100)
def test_title_validation_rejects_invalid_titles(title):
    """Test that titles must be alphanumeric only as per validate_title() method."""
    assume(title != "")  # Empty titles might be handled differently
    
    # Try creating various AWS objects with invalid titles
    with pytest.raises(ValueError, match="not alphanumeric"):
        Asset(title, Id="test-id", PackagingGroupId="group-id", 
               SourceArn="arn:test", SourceRoleArn="arn:role")
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        Channel(title, Id="test-id")
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        OriginEndpoint(title, ChannelId="channel-id", Id="endpoint-id")


@given(title=valid_title_strategy)
@settings(max_examples=50)
def test_title_validation_accepts_valid_titles(title):
    """Test that alphanumeric titles are accepted."""
    # These should not raise exceptions
    asset = Asset(title, Id="test-id", PackagingGroupId="group-id",
                  SourceArn="arn:test", SourceRoleArn="arn:role")
    assert asset.title == title
    
    channel = Channel(title, Id="test-id")
    assert channel.title == title


@given(
    id_value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
@settings(max_examples=50)
def test_type_validation_for_string_properties(id_value):
    """Test that properties expecting strings reject non-string types."""
    assume(not isinstance(id_value, str))
    
    with pytest.raises(TypeError):
        Channel("TestChannel", Id=id_value)
    
    with pytest.raises(TypeError):
        Asset("TestAsset", Id=id_value, PackagingGroupId="group",
              SourceArn="arn", SourceRoleArn="role-arn")


@given(
    max_video_bits=st.one_of(
        st.text(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
@settings(max_examples=50)
def test_type_validation_for_integer_properties(max_video_bits):
    """Test that properties expecting integers reject non-integer types."""
    assume(not isinstance(max_video_bits, int))
    assume(not isinstance(max_video_bits, bool))  # bool is subclass of int
    
    stream_selection = StreamSelection()
    with pytest.raises(TypeError):
        stream_selection.MaxVideoBitsPerSecond = max_video_bits


@given(
    title=valid_title_strategy,
    channel_id=st.text(min_size=1),
    endpoint_id=st.text(min_size=1)
)
@settings(max_examples=50)
def test_required_properties_validation(title, channel_id, endpoint_id):
    """Test that required properties must be provided."""
    # OriginEndpoint requires ChannelId and Id
    origin_endpoint = OriginEndpoint(title, ChannelId=channel_id, Id=endpoint_id)
    
    # This should work
    origin_endpoint.to_dict()
    
    # Missing required property should fail validation
    incomplete_endpoint = OriginEndpoint(title)
    incomplete_endpoint.ChannelId = channel_id  # Set only one required property
    
    with pytest.raises(ValueError, match="required in type"):
        incomplete_endpoint.to_dict(validation=True)


@given(
    title=valid_title_strategy,
    description=st.text(),
    channel_id=st.text(min_size=1)
)
@settings(max_examples=30)
def test_round_trip_serialization_for_channel(title, description, channel_id):
    """Test round-trip serialization: from_dict(to_dict(obj)) preserves data."""
    original = Channel(title, Id=channel_id, Description=description)
    
    # Convert to dict
    dict_repr = original.to_dict(validation=False)
    
    # Create new object from dict
    properties = dict_repr.get("Properties", {})
    reconstructed = Channel.from_dict(title, properties)
    
    # Check that key properties are preserved
    assert reconstructed.Id == original.Id
    assert reconstructed.Description == original.Description
    assert reconstructed.title == original.title


@given(
    title=valid_title_strategy,
    id_value=st.text(min_size=1),
    packaging_group_id=st.text(min_size=1),
    source_arn=st.text(min_size=1),
    source_role_arn=st.text(min_size=1)
)
@settings(max_examples=30)
def test_round_trip_serialization_for_asset(title, id_value, packaging_group_id, source_arn, source_role_arn):
    """Test round-trip serialization for Asset objects."""
    original = Asset(
        title, 
        Id=id_value,
        PackagingGroupId=packaging_group_id,
        SourceArn=source_arn,
        SourceRoleArn=source_role_arn
    )
    
    # Convert to dict
    dict_repr = original.to_dict(validation=False)
    
    # Create new object from dict
    properties = dict_repr.get("Properties", {})
    reconstructed = Asset.from_dict(title, properties)
    
    # Check that all required properties are preserved
    assert reconstructed.Id == original.Id
    assert reconstructed.PackagingGroupId == original.PackagingGroupId
    assert reconstructed.SourceArn == original.SourceArn
    assert reconstructed.SourceRoleArn == original.SourceRoleArn


@given(
    cdnid_secret=st.text(min_size=1),
    role_arn=st.text(min_size=1)
)
@settings(max_examples=50)
def test_aws_property_subclass_validation(cdnid_secret, role_arn):
    """Test that AWSProperty subclasses validate their properties correctly."""
    auth = Authorization(CdnIdentifierSecret=cdnid_secret, SecretsRoleArn=role_arn)
    
    # Should be able to convert to dict
    dict_repr = auth.to_dict()
    assert "CdnIdentifierSecret" in dict_repr
    assert "SecretsRoleArn" in dict_repr
    
    # Test missing required property
    incomplete_auth = Authorization()
    incomplete_auth.CdnIdentifierSecret = cdnid_secret
    
    with pytest.raises(ValueError, match="required in type"):
        incomplete_auth.to_dict(validation=True)


@given(
    title=valid_title_strategy,
    wrong_type_value=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.dictionaries(st.text(), st.text())
    )
)
@settings(max_examples=50)
def test_list_property_type_validation(title, wrong_type_value):
    """Test that list properties validate element types."""
    assume(not isinstance(wrong_type_value, list))
    
    packaging_group = PackagingGroup(title, Id="test-id")
    
    # Tags expects a troposphere.Tags object or compatible type
    # Setting it to a non-list should fail
    with pytest.raises(TypeError):
        packaging_group.Tags = wrong_type_value


@given(
    preset_audio=st.text(min_size=1),
    preset_video=st.text(min_size=1)
)
@settings(max_examples=50)
def test_nested_property_validation(preset_audio, preset_video):
    """Test nested AWSProperty objects validate correctly."""
    # Create nested property structure
    enc_config = EncryptionContractConfiguration(
        PresetSpeke20Audio=preset_audio,
        PresetSpeke20Video=preset_video
    )
    
    speke_provider = OriginEndpointSpekeKeyProvider(
        ResourceId="resource-id",
        RoleArn="role-arn",
        SystemIds=["system1", "system2"],
        Url="https://example.com",
        EncryptionContractConfiguration=enc_config
    )
    
    # Should be able to convert the nested structure to dict
    dict_repr = speke_provider.to_dict()
    assert "EncryptionContractConfiguration" in dict_repr
    assert dict_repr["EncryptionContractConfiguration"]["PresetSpeke20Audio"] == preset_audio
    assert dict_repr["EncryptionContractConfiguration"]["PresetSpeke20Video"] == preset_video