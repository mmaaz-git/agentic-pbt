"""Edge case property-based tests for troposphere.iotfleethub.Application"""

import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.iotfleethub as iotfleethub
from troposphere import Tags, Ref


# Valid titles
valid_titles = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=255)


@given(title=valid_titles)
def test_empty_string_application_name(title):
    """Test that empty ApplicationName is invalid"""
    try:
        app = iotfleethub.Application(
            title,
            ApplicationName="",  # Empty string
            RoleArn="arn:aws:iam::123456789012:role/TestRole"
        )
        # Empty string might be accepted during creation but should fail validation
        d = app.to_dict()
        # If we get here, check if empty string was preserved
        assert d["Properties"]["ApplicationName"] == ""
    except (ValueError, TypeError) as e:
        # This is acceptable - empty strings might be rejected
        pass


@given(title=valid_titles)
def test_empty_string_role_arn(title):
    """Test that empty RoleArn is handled"""
    try:
        app = iotfleethub.Application(
            title,
            ApplicationName="TestApp",
            RoleArn=""  # Empty string
        )
        # Empty string might be accepted during creation
        d = app.to_dict()
        # If we get here, check if empty string was preserved
        assert d["Properties"]["RoleArn"] == ""
    except (ValueError, TypeError) as e:
        # This is acceptable - empty strings might be rejected
        pass


@given(
    title=valid_titles,
    unicode_str=st.text(alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x10000), min_size=1)
)
def test_unicode_in_application_name(title, unicode_str):
    """Test that Unicode characters in ApplicationName are handled correctly"""
    app = iotfleethub.Application(
        title,
        ApplicationName=unicode_str,
        RoleArn="arn:aws:iam::123456789012:role/TestRole"
    )
    
    d = app.to_dict()
    # Unicode should be preserved
    assert d["Properties"]["ApplicationName"] == unicode_str
    
    # Should serialize to JSON correctly
    json_str = app.to_json()
    parsed = json.loads(json_str)
    assert parsed["Properties"]["ApplicationName"] == unicode_str


@given(
    title=valid_titles,
    control_char=st.text(alphabet="\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f", min_size=1, max_size=10)
)
def test_control_characters_in_description(title, control_char):
    """Test that control characters in ApplicationDescription are handled"""
    description = f"Test{control_char}Description"
    
    app = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        ApplicationDescription=description
    )
    
    d = app.to_dict()
    assert d["Properties"]["ApplicationDescription"] == description
    
    # JSON serialization might fail or escape control chars
    try:
        json_str = app.to_json()
        parsed = json.loads(json_str)
        # If it works, the control chars should be preserved or escaped
        assert parsed["Properties"]["ApplicationDescription"]
    except (ValueError, UnicodeDecodeError):
        # Control characters might cause JSON serialization issues
        pass


@given(
    title=valid_titles,
    very_long_str=st.text(min_size=10000, max_size=50000)
)
def test_very_long_strings(title, very_long_str):
    """Test that very long strings are handled correctly"""
    app = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        ApplicationDescription=very_long_str
    )
    
    d = app.to_dict()
    assert d["Properties"]["ApplicationDescription"] == very_long_str
    
    # Should still serialize correctly
    json_str = app.to_json()
    parsed = json.loads(json_str)
    assert parsed["Properties"]["ApplicationDescription"] == very_long_str


@given(title=valid_titles)
def test_none_vs_missing_property(title):
    """Test difference between None and missing optional property"""
    # Create with no ApplicationDescription
    app1 = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole"
    )
    
    # Create with explicit None
    app2 = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        ApplicationDescription=None
    )
    
    d1 = app1.to_dict()
    d2 = app2.to_dict()
    
    # Both should probably omit the property or treat None as missing
    # This tests the actual behavior
    if "ApplicationDescription" in d1["Properties"]:
        assert d1["Properties"]["ApplicationDescription"] is None
    if "ApplicationDescription" in d2["Properties"]:
        assert d2["Properties"]["ApplicationDescription"] is None


@given(
    title1=valid_titles,
    title2=valid_titles.filter(lambda x: x != title1 if 'title1' in locals() else True),
    app_name=st.text(min_size=1, max_size=255),
    role_arn=st.text(min_size=1, max_size=255)
)
def test_same_properties_different_titles(title1, title2, app_name, role_arn):
    """Test that objects with same properties but different titles are not equal"""
    assume(title1 != title2)
    
    kwargs = {
        "ApplicationName": app_name,
        "RoleArn": role_arn
    }
    
    app1 = iotfleethub.Application(title1, **kwargs)
    app2 = iotfleethub.Application(title2, **kwargs)
    
    # Should not be equal due to different titles
    assert app1 != app2
    
    # Hashes should be different (very likely)
    # We won't assert as collisions are possible


@given(title=valid_titles)
def test_setting_invalid_property(title):
    """Test that setting an invalid property raises AttributeError"""
    app = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole"
    )
    
    # Try to set a property that doesn't exist
    try:
        app.InvalidProperty = "value"
        # If we get here, check that it didn't actually set it
        assert not hasattr(app.properties, "InvalidProperty")
    except AttributeError as e:
        # Expected behavior
        assert "does not support attribute InvalidProperty" in str(e)


@given(
    title=valid_titles,
    num_tags=st.integers(min_value=0, max_value=50)
)
def test_many_tags(title, num_tags):
    """Test with many tags"""
    tags_dict = {f"Key{i}": f"Value{i}" for i in range(num_tags)}
    
    app = iotfleethub.Application(
        title,
        ApplicationName="TestApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Tags=Tags(tags_dict) if tags_dict else Tags()
    )
    
    d = app.to_dict()
    if num_tags > 0:
        assert "Tags" in d["Properties"]