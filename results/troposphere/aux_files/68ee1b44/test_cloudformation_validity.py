"""Test CloudFormation template validity for troposphere.iotfleethub"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, settings
import troposphere
import troposphere.iotfleethub as iotfleethub
from troposphere import Template, Tags, Output, Ref


# Test that generated templates are valid CloudFormation JSON
@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1, max_size=255),
    app_name=st.text(min_size=1, max_size=255),
    role_arn=st.text(min_size=1).map(lambda x: f"arn:aws:iam::123456789012:role/{x}"),
    description=st.one_of(st.none(), st.text(max_size=1024))
)
def test_template_generation(title, app_name, role_arn, description):
    """Test that templates with Application resources are valid"""
    
    template = Template()
    
    kwargs = {
        "ApplicationName": app_name,
        "RoleArn": role_arn
    }
    if description is not None:
        kwargs["ApplicationDescription"] = description
    
    app = iotfleethub.Application(title, **kwargs)
    template.add_resource(app)
    
    # Add an output referencing the application
    template.add_output(Output(
        "ApplicationRef",
        Value=Ref(app),
        Description="Reference to the IoT Fleet Hub Application"
    ))
    
    # Generate JSON
    json_str = template.to_json()
    
    # Parse to ensure it's valid JSON
    parsed = json.loads(json_str)
    
    # Check structure
    assert "AWSTemplateFormatVersion" in parsed
    assert "Resources" in parsed
    assert title in parsed["Resources"]
    assert parsed["Resources"][title]["Type"] == "AWS::IoTFleetHub::Application"
    assert "Outputs" in parsed
    assert "ApplicationRef" in parsed["Outputs"]
    assert parsed["Outputs"]["ApplicationRef"]["Value"]["Ref"] == title


def test_multiple_applications_in_template():
    """Test template with multiple Application resources"""
    
    template = Template()
    
    # Add multiple applications
    for i in range(3):
        app = iotfleethub.Application(
            f"TestApp{i}",
            ApplicationName=f"MyApp{i}",
            RoleArn=f"arn:aws:iam::123456789012:role/TestRole{i}",
            ApplicationDescription=f"Description for app {i}"
        )
        template.add_resource(app)
    
    # Generate JSON
    json_str = template.to_json()
    parsed = json.loads(json_str)
    
    # Check all applications are present
    assert len(parsed["Resources"]) == 3
    for i in range(3):
        assert f"TestApp{i}" in parsed["Resources"]
        assert parsed["Resources"][f"TestApp{i}"]["Type"] == "AWS::IoTFleetHub::Application"


def test_application_with_dependencies():
    """Test Application with DependsOn attribute"""
    
    template = Template()
    
    # Create first application
    app1 = iotfleethub.Application(
        "FirstApp",
        ApplicationName="FirstApplication",
        RoleArn="arn:aws:iam::123456789012:role/FirstRole"
    )
    template.add_resource(app1)
    
    # Create second application that depends on the first
    app2 = iotfleethub.Application(
        "SecondApp",
        ApplicationName="SecondApplication",
        RoleArn="arn:aws:iam::123456789012:role/SecondRole",
        DependsOn=app1  # Can use the object directly
    )
    template.add_resource(app2)
    
    # Also test with string reference
    app3 = iotfleethub.Application(
        "ThirdApp",
        ApplicationName="ThirdApplication",
        RoleArn="arn:aws:iam::123456789012:role/ThirdRole",
        DependsOn=["FirstApp", "SecondApp"]  # String references
    )
    template.add_resource(app3)
    
    json_str = template.to_json()
    parsed = json.loads(json_str)
    
    # Check dependencies
    assert parsed["Resources"]["SecondApp"]["DependsOn"] == "FirstApp"
    assert parsed["Resources"]["ThirdApp"]["DependsOn"] == ["FirstApp", "SecondApp"]


def test_application_with_metadata():
    """Test Application with Metadata attribute"""
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Metadata={
            "Version": "1.0",
            "Environment": "Production",
            "CustomData": {
                "Owner": "TeamA",
                "CostCenter": "12345"
            }
        }
    )
    
    d = app.to_dict()
    
    # Check metadata is preserved
    assert "Metadata" in d
    assert d["Metadata"]["Version"] == "1.0"
    assert d["Metadata"]["Environment"] == "Production"
    assert d["Metadata"]["CustomData"]["Owner"] == "TeamA"


def test_application_with_condition():
    """Test Application with Condition attribute"""
    
    template = Template()
    
    # Add a condition to the template
    template.add_condition(
        "CreateProdResources",
        troposphere.Equals(troposphere.Ref("Environment"), "production")
    )
    
    # Create application with condition
    app = iotfleethub.Application(
        "ConditionalApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        Condition="CreateProdResources"
    )
    template.add_resource(app)
    
    json_str = template.to_json()
    parsed = json.loads(json_str)
    
    # Check condition is set
    assert parsed["Resources"]["ConditionalApp"]["Condition"] == "CreateProdResources"
    assert "Conditions" in parsed
    assert "CreateProdResources" in parsed["Conditions"]


def test_application_with_deletion_policy():
    """Test Application with DeletionPolicy"""
    
    app = iotfleethub.Application(
        "TestApp",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        DeletionPolicy="Retain"  # Keep resource on stack deletion
    )
    
    d = app.to_dict()
    
    # Check DeletionPolicy is set
    assert "DeletionPolicy" in d
    assert d["DeletionPolicy"] == "Retain"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])