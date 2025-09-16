"""Property-based tests for troposphere.iotfleethub.Application"""

import json
import re
from hypothesis import given, strategies as st, assume, settings
import troposphere.iotfleethub as iotfleethub
from troposphere import Tags, Ref


# Strategy for valid CloudFormation resource titles (alphanumeric only)
# Must match the regex ^[a-zA-Z0-9]+$
valid_titles = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=255)

# Strategy for invalid titles (with non-alphanumeric characters)
invalid_titles = st.text(min_size=1, max_size=255).filter(
    lambda x: not re.match(r'^[a-zA-Z0-9]+$', x)
)

# Strategy for AWS ARN-like strings
arns = st.text(min_size=1).map(lambda x: f"arn:aws:iam::123456789012:role/{x}")

# Strategy for application names
app_names = st.text(min_size=1, max_size=255)

# Strategy for descriptions
descriptions = st.text(max_size=1024)


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns,
    description=st.one_of(st.none(), descriptions)
)
def test_resource_type_consistency(title, app_name, role_arn, description):
    """Test that resource type is always AWS::IoTFleetHub::Application"""
    kwargs = {
        "ApplicationName": app_name,
        "RoleArn": role_arn,
    }
    if description is not None:
        kwargs["ApplicationDescription"] = description
    
    app = iotfleethub.Application(title, **kwargs)
    
    # Check resource_type attribute
    assert app.resource_type == "AWS::IoTFleetHub::Application"
    
    # Check it appears in the dict representation
    d = app.to_dict()
    assert d["Type"] == "AWS::IoTFleetHub::Application"


@given(title=invalid_titles)
def test_invalid_title_validation(title):
    """Test that invalid titles raise ValueError"""
    # Skip empty strings as they're handled differently
    assume(title != "")
    
    try:
        app = iotfleethub.Application(
            title,
            ApplicationName="TestApp",
            RoleArn="arn:aws:iam::123456789012:role/TestRole"
        )
        # If we get here, check if title validation actually failed
        # The validation happens in validate_title() which is called in __init__
        assert False, f"Expected ValueError for invalid title: {title!r}"
    except ValueError as e:
        # Expected behavior - invalid titles should raise ValueError
        assert "not alphanumeric" in str(e)


@given(
    title=valid_titles,
    app_name=st.one_of(st.none(), app_names),
    role_arn=st.one_of(st.none(), arns),
    description=st.one_of(st.none(), descriptions)
)
def test_required_fields_validation(title, app_name, role_arn, description):
    """Test that missing required fields raise ValueError on validation"""
    kwargs = {}
    if app_name is not None:
        kwargs["ApplicationName"] = app_name
    if role_arn is not None:
        kwargs["RoleArn"] = role_arn
    if description is not None:
        kwargs["ApplicationDescription"] = description
    
    app = iotfleethub.Application(title, **kwargs)
    
    # Check if required fields are missing
    missing_required = []
    if app_name is None:
        missing_required.append("ApplicationName")
    if role_arn is None:
        missing_required.append("RoleArn")
    
    if missing_required:
        # Should raise ValueError when validating
        try:
            app.to_dict()  # This triggers validation
            assert False, f"Expected ValueError for missing required fields: {missing_required}"
        except ValueError as e:
            # Check that at least one of the missing fields is mentioned
            assert any(field in str(e) for field in missing_required)
    else:
        # Should not raise if all required fields are present
        d = app.to_dict()
        assert "Properties" in d
        assert d["Properties"]["ApplicationName"] == app_name
        assert d["Properties"]["RoleArn"] == role_arn


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns,
    description=st.one_of(st.none(), descriptions)
)
def test_round_trip_serialization(title, app_name, role_arn, description):
    """Test that to_dict/from_dict preserve data correctly"""
    kwargs = {
        "ApplicationName": app_name,
        "RoleArn": role_arn,
    }
    if description is not None:
        kwargs["ApplicationDescription"] = description
    
    # Create original object
    app1 = iotfleethub.Application(title, **kwargs)
    
    # Convert to dict
    d = app1.to_dict()
    
    # Extract properties for reconstruction
    props = d.get("Properties", {})
    
    # Create new object from properties
    app2 = iotfleethub.Application.from_dict(title, props)
    
    # Compare the dictionaries
    d1 = app1.to_dict(validation=False)
    d2 = app2.to_dict(validation=False)
    
    assert d1 == d2


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns,
    description=st.one_of(st.none(), descriptions)
)
def test_equality_and_hash_consistency(title, app_name, role_arn, description):
    """Test that equality and hash are consistent"""
    kwargs = {
        "ApplicationName": app_name,
        "RoleArn": role_arn,
    }
    if description is not None:
        kwargs["ApplicationDescription"] = description
    
    # Create two identical objects
    app1 = iotfleethub.Application(title, **kwargs)
    app2 = iotfleethub.Application(title, **kwargs)
    
    # Test equality
    assert app1 == app2
    
    # Test hash consistency with equality
    assert hash(app1) == hash(app2)
    
    # Create a different object (different title)
    app3 = iotfleethub.Application(title + "X", **kwargs)
    
    # Should not be equal
    assert app1 != app3
    
    # Hash should likely be different (not guaranteed but very likely)
    # We won't assert this as hash collisions are technically possible


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns,
    tag_keys=st.lists(st.text(min_size=1, max_size=128), min_size=0, max_size=10),
    tag_values=st.lists(st.text(max_size=256), min_size=0, max_size=10)
)
def test_tags_property(title, app_name, role_arn, tag_keys, tag_values):
    """Test that Tags property works correctly"""
    # Make sure we have same number of keys and values
    min_len = min(len(tag_keys), len(tag_values))
    tag_keys = tag_keys[:min_len]
    tag_values = tag_values[:min_len]
    
    # Create tags dict
    tags_dict = dict(zip(tag_keys, tag_values))
    
    # Create application with tags
    app = iotfleethub.Application(
        title,
        ApplicationName=app_name,
        RoleArn=role_arn,
        Tags=Tags(tags_dict) if tags_dict else Tags()
    )
    
    # Should not raise on to_dict
    d = app.to_dict()
    assert "Properties" in d
    
    # If we had tags, they should be in the output
    if tags_dict:
        assert "Tags" in d["Properties"]


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns,
    description=descriptions
)
def test_json_serialization_validity(title, app_name, role_arn, description):
    """Test that to_json produces valid JSON"""
    app = iotfleethub.Application(
        title,
        ApplicationName=app_name,
        RoleArn=role_arn,
        ApplicationDescription=description
    )
    
    # Get JSON string
    json_str = app.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain expected structure
    assert "Type" in parsed
    assert parsed["Type"] == "AWS::IoTFleetHub::Application"
    assert "Properties" in parsed
    assert parsed["Properties"]["ApplicationName"] == app_name
    assert parsed["Properties"]["RoleArn"] == role_arn
    assert parsed["Properties"]["ApplicationDescription"] == description


@given(
    title=valid_titles,
    app_name=app_names,
    role_arn=arns
)
def test_ref_method(title, app_name, role_arn):
    """Test that ref() method returns correct Ref object"""
    app = iotfleethub.Application(
        title,
        ApplicationName=app_name,
        RoleArn=role_arn
    )
    
    ref = app.ref()
    
    # Should be a Ref object
    assert isinstance(ref, Ref)
    
    # The Ref should reference the application's title
    ref_dict = ref.to_dict()
    assert ref_dict == {"Ref": title}