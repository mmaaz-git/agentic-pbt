import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import troposphere.codeguruprofiler as cgp
from troposphere import Tags
import json

# Test edge cases with empty strings and None values

# Test 1: Empty string for required field
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_empty_string_required_field(title):
    """Test that empty strings for required fields fail validation"""
    try:
        pg = cgp.ProfilingGroup(title, ProfilingGroupName="")
        pg.to_dict()  # This should trigger validation
        # Empty string might be accepted, let's check
        d = pg.to_dict()
        assert d["Properties"]["ProfilingGroupName"] == ""
    except (ValueError, TypeError) as e:
        # If it fails, that's also acceptable behavior
        pass

# Test 2: None value for optional field
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    profiling_group_name=st.text(min_size=1, max_size=255)
)
def test_none_optional_field(title, profiling_group_name):
    """Test setting None to optional fields"""
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=profiling_group_name,
        ComputePlatform=None  # Optional field set to None
    )
    
    d = pg.to_dict()
    # None values should not appear in the dictionary
    assert "ComputePlatform" not in d["Properties"]

# Test 3: None value for required field in nested property
def test_none_required_in_agent_permissions():
    """Test that None for required field in AgentPermissions fails"""
    try:
        ap = cgp.AgentPermissions(Principals=None)
        ap.to_dict()
        assert False, "Should have failed with None for required field"
    except (ValueError, TypeError, AttributeError):
        # Expected to fail
        pass

# Test 4: Empty list for required list field
def test_empty_list_for_principals():
    """Test empty list for Principals which requires at least one"""
    ap = cgp.AgentPermissions(Principals=[])
    d = ap.to_dict()
    # Check if empty list is accepted
    assert d["Principals"] == []

# Test 5: Very long strings
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    long_string=st.text(min_size=10000, max_size=100000)
)
def test_very_long_strings(title, long_string):
    """Test handling of very long strings"""
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=long_string
    )
    d = pg.to_dict()
    assert d["Properties"]["ProfilingGroupName"] == long_string

# Test 6: Unicode in string properties (not title)
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    unicode_string=st.text(min_size=1, max_size=100).filter(lambda x: any(ord(c) > 127 for c in x))
)
def test_unicode_in_properties(title, unicode_string):
    """Test Unicode characters in regular string properties"""
    assume(unicode_string)  # Skip if we couldn't generate unicode
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=unicode_string
    )
    d = pg.to_dict()
    assert d["Properties"]["ProfilingGroupName"] == unicode_string

# Test 7: Special characters in Channel URIs
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    special_chars=st.text(alphabet='!@#$%^&*()[]{}|\\:;"\'<>,.?/~`', min_size=1, max_size=50)
)
def test_special_chars_in_channel_uri(title, special_chars):
    """Test special characters in channel URIs"""
    channel = cgp.Channel(channelUri=special_chars)
    d = channel.to_dict()
    assert d["channelUri"] == special_chars

# Test 8: Round-trip with all None optional fields
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_round_trip_with_none_optionals(title):
    """Test round-trip when all optional fields are None"""
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName="TestGroup",
        AgentPermissions=None,
        AnomalyDetectionNotificationConfiguration=None,
        ComputePlatform=None,
        Tags=None
    )
    
    d = pg.to_dict()
    properties = d.get("Properties", {})
    
    pg_new = cgp.ProfilingGroup.from_dict(title, properties)
    
    # Should successfully round-trip
    assert pg.to_dict() == pg_new.to_dict()

# Test 9: Multiple channels with duplicate URIs
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    duplicate_uri=st.text(min_size=10, max_size=100)
)
def test_duplicate_channel_uris(title, duplicate_uri):
    """Test multiple channels with the same URI"""
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName="TestGroup"
    )
    
    # Create multiple channels with the same URI
    channels = [
        cgp.Channel(channelUri=duplicate_uri, channelId="channel-1"),
        cgp.Channel(channelUri=duplicate_uri, channelId="channel-2"),
        cgp.Channel(channelUri=duplicate_uri, channelId="channel-3")
    ]
    
    pg.AnomalyDetectionNotificationConfiguration = channels
    
    d = pg.to_dict()
    assert len(d["Properties"]["AnomalyDetectionNotificationConfiguration"]) == 3
    
    # All should have the same URI
    for channel in d["Properties"]["AnomalyDetectionNotificationConfiguration"]:
        assert channel["channelUri"] == duplicate_uri

# Test 10: Tags with empty keys or values
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_tags_with_empty_strings(title):
    """Test Tags with empty keys or values"""
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName="TestGroup"
    )
    
    # Try tags with empty strings
    pg.Tags = Tags(**{"": "empty-key", "empty-value": ""})
    
    d = pg.to_dict()
    tags_list = d["Properties"]["Tags"]
    
    # Check if empty strings are preserved
    assert any(tag["Key"] == "" for tag in tags_list)
    assert any(tag["Value"] == "" for tag in tags_list)

# Test 11: from_dict with extra fields
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    extra_field_name=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=10, max_size=20),
    extra_field_value=st.text(min_size=1, max_size=100)
)
def test_from_dict_with_extra_fields(title, extra_field_name, extra_field_value):
    """Test from_dict with unknown fields"""
    assume(extra_field_name not in ["ProfilingGroupName", "ComputePlatform", "AgentPermissions", 
                                     "AnomalyDetectionNotificationConfiguration", "Tags"])
    
    properties = {
        "ProfilingGroupName": "TestGroup",
        extra_field_name: extra_field_value  # Unknown field
    }
    
    try:
        pg = cgp.ProfilingGroup.from_dict(title, properties)
        # If it accepts extra fields, that might be a bug
        assert False, f"Should not accept unknown field: {extra_field_name}"
    except (AttributeError, KeyError) as e:
        # Expected to reject unknown fields
        assert extra_field_name in str(e) or "does not have" in str(e)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])