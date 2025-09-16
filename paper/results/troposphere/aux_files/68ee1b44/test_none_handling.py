"""Test None handling in troposphere.iotfleethub.Application"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotfleethub as iotfleethub
from troposphere import Tags


def test_none_for_optional_property():
    """Test that None for optional properties raises TypeError"""
    
    print("Testing None for optional ApplicationDescription...")
    
    # This works - omitting the optional property
    app1 = iotfleethub.Application(
        "TestApp1",
        ApplicationName="MyApp",
        RoleArn="arn:aws:iam::123456789012:role/TestRole"
    )
    d1 = app1.to_dict()
    print(f"Without ApplicationDescription: {d1}")
    
    # This raises TypeError - explicitly passing None
    try:
        app2 = iotfleethub.Application(
            "TestApp2",
            ApplicationName="MyApp",
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            ApplicationDescription=None  # Explicit None
        )
        print("Unexpected: None was accepted for ApplicationDescription")
    except TypeError as e:
        print(f"Expected TypeError: {e}")
    
    # What about required fields?
    print("\nTesting None for required fields...")
    
    try:
        app3 = iotfleethub.Application(
            "TestApp3",
            ApplicationName=None,  # None for required field
            RoleArn="arn:aws:iam::123456789012:role/TestRole"
        )
        print("Unexpected: None was accepted for ApplicationName")
    except TypeError as e:
        print(f"Expected TypeError for ApplicationName=None: {e}")
    
    try:
        app4 = iotfleethub.Application(
            "TestApp4",
            ApplicationName="MyApp",
            RoleArn=None  # None for required field
        )
        print("Unexpected: None was accepted for RoleArn")
    except TypeError as e:
        print(f"Expected TypeError for RoleArn=None: {e}")
    
    # What about Tags?
    print("\nTesting None for Tags...")
    
    try:
        app5 = iotfleethub.Application(
            "TestApp5",
            ApplicationName="MyApp",
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            Tags=None  # None for Tags
        )
        print("Unexpected: None was accepted for Tags")
    except TypeError as e:
        print(f"Expected TypeError for Tags=None: {e}")


if __name__ == "__main__":
    test_none_for_optional_property()