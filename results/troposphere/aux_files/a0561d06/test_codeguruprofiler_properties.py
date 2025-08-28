import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import troposphere.codeguruprofiler as cgp
from troposphere import Tags
import json
import re

# Strategy for valid CloudFormation resource titles (alphanumeric only)
valid_title_strategy = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100)

# Strategy for invalid titles with special characters
invalid_title_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)
)

# Strategy for channel URIs (simplified AWS ARN format)
channel_uri_strategy = st.text(min_size=10, max_size=200).map(
    lambda x: f"arn:aws:sns:us-east-1:123456789012:{x.replace(' ', '').replace('/', '')[:50]}"
)

# Strategy for principals (AWS account IDs or service principals)
principals_strategy = st.lists(
    st.one_of(
        st.from_regex(r"[0-9]{12}", fullmatch=True),  # AWS account ID
        st.just("codeguru-profiler.amazonaws.com")  # Service principal
    ),
    min_size=1,
    max_size=10
)

# Test 1: Round-trip property for ProfilingGroup
@given(
    title=valid_title_strategy,
    profiling_group_name=st.text(min_size=1, max_size=255),
    compute_platform=st.sampled_from(["Default", "AWSLambda"]),
    include_permissions=st.booleans(),
    principals=principals_strategy
)
def test_profiling_group_round_trip(title, profiling_group_name, compute_platform, include_permissions, principals):
    # Create a ProfilingGroup
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=profiling_group_name,
        ComputePlatform=compute_platform
    )
    
    if include_permissions:
        pg.AgentPermissions = cgp.AgentPermissions(Principals=principals)
    
    # Convert to dict and back
    pg_dict = pg.to_dict()
    
    # Extract properties for from_dict (need to remove Type and other metadata)
    properties = pg_dict.get("Properties", {})
    
    # Create new object from dict
    pg_new = cgp.ProfilingGroup.from_dict(title, properties)
    
    # Compare the dictionaries (not the objects directly)
    assert pg.to_dict() == pg_new.to_dict()

# Test 2: Title validation - valid titles should work
@given(title=valid_title_strategy)
def test_valid_title_accepts(title):
    # This should not raise an exception
    pg = cgp.ProfilingGroup(title, ProfilingGroupName="TestGroup")
    assert pg.title == title

# Test 3: Title validation - invalid titles should fail
@given(title=invalid_title_strategy)
def test_invalid_title_rejects(title):
    try:
        pg = cgp.ProfilingGroup(title, ProfilingGroupName="TestGroup")
        # If we get here, the validation failed to reject invalid title
        assert False, f"Title validation should have rejected: {title}"
    except ValueError as e:
        # Expected behavior
        assert "not alphanumeric" in str(e)

# Test 4: Required field validation for AgentPermissions
@given(principals=principals_strategy)
def test_agent_permissions_required_field(principals):
    # Principals is required in AgentPermissions
    ap = cgp.AgentPermissions(Principals=principals)
    ap_dict = ap.to_dict()
    assert "Principals" in ap_dict
    assert ap_dict["Principals"] == principals

# Test 5: Required field validation for Channel
@given(channel_uri=channel_uri_strategy, channel_id=st.text(min_size=0, max_size=100))
def test_channel_required_field(channel_uri, channel_id):
    # channelUri is required, channelId is optional
    if channel_id:
        channel = cgp.Channel(channelUri=channel_uri, channelId=channel_id)
        channel_dict = channel.to_dict()
        assert channel_dict["channelUri"] == channel_uri
        assert channel_dict["channelId"] == channel_id
    else:
        channel = cgp.Channel(channelUri=channel_uri)
        channel_dict = channel.to_dict()
        assert channel_dict["channelUri"] == channel_uri
        assert "channelId" not in channel_dict or channel_dict["channelId"] == ""

# Test 6: Missing required field should fail
@given(title=valid_title_strategy)
def test_missing_required_field_fails(title):
    try:
        pg = cgp.ProfilingGroup(title)  # Missing required ProfilingGroupName
        pg.to_dict()  # This should trigger validation
        assert False, "Should have raised ValueError for missing required field"
    except ValueError as e:
        assert "required" in str(e).lower()

# Test 7: Round-trip with complex nested structures
@given(
    title=valid_title_strategy,
    profiling_group_name=st.text(min_size=1, max_size=255),
    num_channels=st.integers(min_value=0, max_value=5),
    channel_uris=st.lists(channel_uri_strategy, min_size=5, max_size=5)
)
def test_complex_round_trip(title, profiling_group_name, num_channels, channel_uris):
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=profiling_group_name
    )
    
    # Add notification channels
    if num_channels > 0:
        channels = []
        for i in range(num_channels):
            channels.append(cgp.Channel(
                channelUri=channel_uris[i],
                channelId=f"channel-{i}"
            ))
        pg.AnomalyDetectionNotificationConfiguration = channels
    
    # Convert to dict and back
    pg_dict = pg.to_dict()
    properties = pg_dict.get("Properties", {})
    
    pg_new = cgp.ProfilingGroup.from_dict(title, properties)
    
    # The dictionaries should be equal
    assert pg.to_dict() == pg_new.to_dict()

# Test 8: Tags property if supported
@given(
    title=valid_title_strategy,
    profiling_group_name=st.text(min_size=1, max_size=255),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_tags_handling(title, profiling_group_name, tags):
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=profiling_group_name
    )
    
    if tags:
        pg.Tags = Tags(**tags)
        pg_dict = pg.to_dict()
        
        # Verify tags are properly formatted
        assert "Properties" in pg_dict
        if "Tags" in pg_dict["Properties"]:
            tags_list = pg_dict["Properties"]["Tags"]
            assert isinstance(tags_list, list)
            
            # Check each tag has Key and Value
            for tag in tags_list:
                assert "Key" in tag
                assert "Value" in tag

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])