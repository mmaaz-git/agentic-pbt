import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codestarconnections as csc
from troposphere import Tags, AWSHelperFn
from hypothesis import given, strategies as st, assume, settings


# Test for None values
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_connection_with_none_values(title):
    """Test that Connection handles None values properly"""
    # Should we be able to pass None for optional properties?
    conn = csc.Connection(
        title=title,
        ConnectionName="test",
        HostArn=None,  # This is optional - can it be None?
        ProviderType=None  # This is also optional
    )
    
    # Try to serialize
    conn_dict = conn.to_dict()
    
    # Check if None values are handled correctly
    props = conn_dict.get("Properties", {})
    
    # None values should not appear in the dictionary
    assert props.get("HostArn") is None
    assert props.get("ProviderType") is None


# Test empty strings
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_connection_with_empty_string(title):
    """Test Connection with empty string for ConnectionName"""
    conn = csc.Connection(
        title=title,
        ConnectionName=""  # Empty string - is this valid?
    )
    
    # Should be able to create and serialize
    conn_dict = conn.to_dict()
    assert conn_dict["Properties"]["ConnectionName"] == ""


# Test very long strings
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
       long_name=st.text(min_size=10000, max_size=20000))
def test_connection_with_very_long_strings(title, long_name):
    """Test Connection with very long ConnectionName"""
    conn = csc.Connection(
        title=title,
        ConnectionName=long_name
    )
    
    # Should handle long strings
    conn_dict = conn.to_dict()
    assert conn_dict["Properties"]["ConnectionName"] == long_name


# Test special characters in strings
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
       special_name=st.text().filter(lambda x: len(x) > 0))
def test_connection_with_special_characters(title, special_name):
    """Test Connection with special characters in ConnectionName"""
    conn = csc.Connection(
        title=title,
        ConnectionName=special_name
    )
    
    # Should handle special characters
    conn_dict = conn.to_dict()
    assert conn_dict["Properties"]["ConnectionName"] == special_name


# Test wrong type for properties
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
       wrong_type=st.one_of(st.integers(), st.floats(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
def test_connection_with_wrong_type(title, wrong_type):
    """Test Connection with wrong type for ConnectionName"""
    # Skip if it's accidentally a string
    assume(not isinstance(wrong_type, str))
    
    try:
        conn = csc.Connection(
            title=title,
            ConnectionName=wrong_type  # Wrong type
        )
        # If it accepts wrong type, that might be a bug
        # unless it can convert it
        conn_dict = conn.to_dict()
        # Check if it was converted to string
        assert isinstance(conn_dict["Properties"]["ConnectionName"], (str, dict, list))
    except (TypeError, AttributeError):
        # Expected to fail with wrong type
        pass


# Test Tags with empty dict
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_connection_with_empty_tags(title):
    """Test Connection with empty Tags"""
    conn = csc.Connection(
        title=title,
        ConnectionName="test",
        Tags=Tags({})  # Empty tags
    )
    
    conn_dict = conn.to_dict()
    tags = conn_dict["Properties"]["Tags"]
    assert isinstance(tags, list)
    assert len(tags) == 0


# Test multiple tags
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
       tags_dict=st.dictionaries(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=50), min_size=1, max_size=10))
def test_connection_with_multiple_tags(title, tags_dict):
    """Test Connection with multiple tags"""
    conn = csc.Connection(
        title=title,
        ConnectionName="test",
        Tags=Tags(tags_dict)
    )
    
    conn_dict = conn.to_dict()
    tags = conn_dict["Properties"]["Tags"]
    assert isinstance(tags, list)
    assert len(tags) == len(tags_dict)
    
    # Check all tags are present
    tag_keys = {tag["Key"] for tag in tags}
    assert tag_keys == set(tags_dict.keys())


# Test JSON serialization with special characters
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
       json_special=st.text(alphabet='"\\\n\r\t', min_size=1, max_size=10))
def test_json_serialization_special_chars(title, json_special):
    """Test JSON serialization with characters that need escaping"""
    conn = csc.Connection(
        title=title,
        ConnectionName=json_special
    )
    
    # Should properly escape in JSON
    json_str = conn.to_json()
    parsed = json.loads(json_str)
    assert parsed["Properties"]["ConnectionName"] == json_special


# Test provider type case sensitivity
@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_provider_type_case_sensitivity(title):
    """Test if provider type validation is case sensitive"""
    from troposphere.validators.codestarconnections import validate_connection_providertype
    
    # Try lowercase versions
    for provider in ["bitbucket", "github", "githubenterpriseserver"]:
        try:
            validate_connection_providertype(provider)
            # If it accepts lowercase, that might be unexpected
            assert False, f"Lowercase '{provider}' was accepted"
        except ValueError:
            # Expected - should be case sensitive
            pass