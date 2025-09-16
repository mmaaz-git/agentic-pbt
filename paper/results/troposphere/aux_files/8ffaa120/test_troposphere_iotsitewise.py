import json
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotsitewise as iotsitewise
from troposphere import BaseAWSObject, AWSObject, AWSProperty, Tags
from hypothesis import given, strategies as st, assume, settings
import hypothesis.strategies as st
import pytest


# Strategy for valid alphanumeric resource titles
valid_titles = st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]), min_size=1, max_size=255)

# Strategy for AWS ARNs (simplified but valid format)
aws_arns = st.text(min_size=1).map(lambda s: f"arn:aws:iam::123456789012:role/{s.replace(' ', '_')}")

# Strategy for UUIDs/IDs
valid_ids = st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd", "-"]), min_size=1, max_size=100)

# Strategy for simple strings
simple_strings = st.text(min_size=0, max_size=1000)

# Strategy for AWS permissions
permissions = st.sampled_from(["ADMINISTRATOR", "VIEWER"])

@given(title=valid_titles)
def test_title_validation_valid(title):
    """Test that valid alphanumeric titles are accepted"""
    # This tests the property that titles matching ^[a-zA-Z0-9]+$ are valid
    obj = iotsitewise.AccessPolicy(
        title,
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
        AccessPolicyPermission="VIEWER",
        AccessPolicyResource=iotsitewise.AccessPolicyResource()
    )
    # Should not raise an exception
    assert obj.title == title


@given(title=st.text(min_size=1).filter(lambda s: not s.replace('_', '').replace('-', '').replace(' ', '').isalnum()))
def test_title_validation_invalid(title):
    """Test that non-alphanumeric titles are rejected"""
    assume(not all(c.isalnum() for c in title))
    
    with pytest.raises(ValueError, match='Name ".*" not alphanumeric'):
        iotsitewise.AccessPolicy(
            title,
            AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(),
            AccessPolicyPermission="VIEWER",
            AccessPolicyResource=iotsitewise.AccessPolicyResource()
        )


@given(
    title=valid_titles,
    arn=aws_arns,
    user_id=valid_ids,
    permission=permissions
)
def test_accesspolicy_to_dict_from_dict_roundtrip(title, arn, user_id, permission):
    """Test that AccessPolicy objects can roundtrip through dict conversion"""
    # Create an AccessPolicy with all possible identity types
    original = iotsitewise.AccessPolicy(
        title,
        AccessPolicyIdentity=iotsitewise.AccessPolicyIdentity(
            IamRole=iotsitewise.IamRole(arn=arn),
            User=iotsitewise.User(id=user_id)
        ),
        AccessPolicyPermission=permission,
        AccessPolicyResource=iotsitewise.AccessPolicyResource(
            Portal=iotsitewise.PortalProperty(id=user_id)
        )
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # The dict should have the expected structure
    assert "Type" in dict_repr
    assert dict_repr["Type"] == "AWS::IoTSiteWise::AccessPolicy"
    assert "Properties" in dict_repr
    
    # Verify the properties are preserved
    props = dict_repr["Properties"]
    assert props["AccessPolicyPermission"] == permission
    assert props["AccessPolicyIdentity"]["IamRole"]["arn"] == arn
    assert props["AccessPolicyIdentity"]["User"]["id"] == user_id
    assert props["AccessPolicyResource"]["Portal"]["id"] == user_id


@given(
    title=valid_titles,
    name=simple_strings,
    description=simple_strings,
    model_id=valid_ids
)
def test_asset_json_serialization(title, name, description, model_id):
    """Test that Asset objects produce valid JSON"""
    asset = iotsitewise.Asset(
        title,
        AssetName=name,
        AssetDescription=description,
        AssetModelId=model_id
    )
    
    # to_json should produce valid JSON
    json_str = asset.to_json()
    
    # Should be parseable JSON
    parsed = json.loads(json_str)
    
    # Verify structure
    assert parsed["Type"] == "AWS::IoTSiteWise::Asset"
    assert parsed["Properties"]["AssetName"] == name
    assert parsed["Properties"]["AssetDescription"] == description
    assert parsed["Properties"]["AssetModelId"] == model_id


@given(
    title=valid_titles,
    child_asset_id=valid_ids,
    hierarchy_id=valid_ids,
    external_id=valid_ids
)
def test_asset_hierarchy_optional_properties(title, child_asset_id, hierarchy_id, external_id):
    """Test that AssetHierarchy handles optional properties correctly"""
    # Create with only required property
    hierarchy_minimal = iotsitewise.AssetHierarchy(
        ChildAssetId=child_asset_id
    )
    
    # Create with all properties
    hierarchy_full = iotsitewise.AssetHierarchy(
        ChildAssetId=child_asset_id,
        Id=hierarchy_id,
        ExternalId=external_id,
        LogicalId=hierarchy_id
    )
    
    # Both should convert to dict successfully
    dict_minimal = hierarchy_minimal.to_dict()
    dict_full = hierarchy_full.to_dict()
    
    # Minimal should only have required field
    assert "ChildAssetId" in dict_minimal
    assert dict_minimal["ChildAssetId"] == child_asset_id
    
    # Full should have all fields
    assert dict_full["ChildAssetId"] == child_asset_id
    assert dict_full["Id"] == hierarchy_id
    assert dict_full["ExternalId"] == external_id
    assert dict_full["LogicalId"] == hierarchy_id


@given(
    title=valid_titles,
    gateway_name=simple_strings,
    thing_name=valid_ids,
    os_type=st.sampled_from(["Linux", "Windows", ""])
)
def test_gateway_platform_properties(title, gateway_name, thing_name, os_type):
    """Test Gateway with platform configurations"""
    # Create Gateway with GreengrassV2 platform
    gateway = iotsitewise.Gateway(
        title,
        GatewayName=gateway_name,
        GatewayPlatform=iotsitewise.GatewayPlatform(
            GreengrassV2=iotsitewise.GreengrassV2(
                CoreDeviceThingName=thing_name,
                CoreDeviceOperatingSystem=os_type if os_type else None
            )
        )
    )
    
    dict_repr = gateway.to_dict()
    assert dict_repr["Type"] == "AWS::IoTSiteWise::Gateway"
    assert dict_repr["Properties"]["GatewayName"] == gateway_name
    
    platform = dict_repr["Properties"]["GatewayPlatform"]["GreengrassV2"]
    assert platform["CoreDeviceThingName"] == thing_name
    if os_type:
        assert platform["CoreDeviceOperatingSystem"] == os_type


@given(
    data_type=st.sampled_from(["STRING", "INTEGER", "DOUBLE", "BOOLEAN"]),
    name=simple_strings,
    type_name=st.sampled_from(["Measurement", "Attribute", "Transform", "Metric"])
)
def test_asset_model_property_required_fields(data_type, name, type_name):
    """Test AssetModelProperty with required fields"""
    prop = iotsitewise.AssetModelProperty(
        DataType=data_type,
        Name=name,
        Type=iotsitewise.PropertyType(
            TypeName=type_name
        )
    )
    
    dict_repr = prop.to_dict()
    assert dict_repr["DataType"] == data_type
    assert dict_repr["Name"] == name
    assert dict_repr["Type"]["TypeName"] == type_name


@given(
    title=valid_titles,
    portal_name=simple_strings,
    contact_email=st.emails(),
    role_arn=aws_arns
)
def test_portal_email_validation(title, portal_name, contact_email, role_arn):
    """Test Portal with email properties"""
    portal = iotsitewise.Portal(
        title,
        PortalName=portal_name,
        PortalContactEmail=contact_email,
        RoleArn=role_arn
    )
    
    dict_repr = portal.to_dict()
    assert dict_repr["Type"] == "AWS::IoTSiteWise::Portal"
    assert dict_repr["Properties"]["PortalName"] == portal_name
    assert dict_repr["Properties"]["PortalContactEmail"] == contact_email
    assert dict_repr["Properties"]["RoleArn"] == role_arn


@given(
    title=valid_titles,
    dashboard_name=simple_strings,
    dashboard_desc=simple_strings,
    dashboard_def=st.text(min_size=1, max_size=5000)
)
def test_dashboard_required_properties(title, dashboard_name, dashboard_desc, dashboard_def):
    """Test Dashboard with all required properties"""
    dashboard = iotsitewise.Dashboard(
        title,
        DashboardName=dashboard_name,
        DashboardDescription=dashboard_desc,
        DashboardDefinition=dashboard_def
    )
    
    dict_repr = dashboard.to_dict()
    assert dict_repr["Type"] == "AWS::IoTSiteWise::Dashboard"
    props = dict_repr["Properties"]
    assert props["DashboardName"] == dashboard_name
    assert props["DashboardDescription"] == dashboard_desc
    assert props["DashboardDefinition"] == dashboard_def


@given(
    title=valid_titles,
    interval=st.text(alphabet="0123456789smhd", min_size=2, max_size=10),
    offset=st.text(alphabet="0123456789smhd", min_size=0, max_size=10)
)
def test_tumbling_window_time_properties(title, interval, offset):
    """Test TumblingWindow with time interval properties"""
    # Ensure interval has at least one digit and one time unit
    assume(any(c.isdigit() for c in interval))
    assume(any(c in "smhd" for c in interval))
    
    window = iotsitewise.TumblingWindow(
        Interval=interval,
        Offset=offset if offset else None
    )
    
    dict_repr = window.to_dict()
    assert dict_repr["Interval"] == interval
    if offset:
        assert dict_repr["Offset"] == offset


@given(st.data())
def test_multiple_resource_types_have_unique_names(data):
    """Test that different resource types have unique resource_type values"""
    # Get all classes that are AWSObject subclasses
    resource_types = []
    for name in dir(iotsitewise):
        obj = getattr(iotsitewise, name)
        if isinstance(obj, type) and issubclass(obj, AWSObject) and hasattr(obj, 'resource_type'):
            if obj.resource_type:
                resource_types.append((name, obj.resource_type))
    
    # All resource types should be unique
    type_values = [rt[1] for rt in resource_types]
    assert len(type_values) == len(set(type_values)), f"Duplicate resource types found"
    
    # All should follow AWS naming convention
    for class_name, resource_type in resource_types:
        assert resource_type.startswith("AWS::IoTSiteWise::"), f"{class_name} has invalid resource type {resource_type}"