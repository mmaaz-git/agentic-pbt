#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.pcaconnectorad import VpcInformation, Connector
import troposphere

print("=== Test 1: VpcInformation without required properties ===")
try:
    vpc = VpcInformation()
    print(f"VpcInformation created without error!")
    print(f"Properties: {vpc.properties}")
    print(f"Props definition: {vpc.props}")
    
    # Try to convert to dict (this might trigger validation)
    try:
        vpc_dict = vpc.to_dict()
        print(f"to_dict() succeeded: {vpc_dict}")
    except Exception as e:
        print(f"to_dict() failed: {e}")
        
except Exception as e:
    print(f"Error creating VpcInformation: {e}")

print("\n=== Test 2: Connector title requirement ===")
try:
    # Test if Connector needs a title
    connector = Connector(
        title="TestConnector",
        CertificateAuthorityArn="arn:aws:acm-pca:us-east-1:123456789012:certificate-authority/12345678",
        DirectoryId="d-1234567890",
        VpcInformation=VpcInformation(SecurityGroupIds=["sg-123"]),
        Tags={"Key": "Value"}
    )
    print(f"Connector created with title: {connector.title}")
    print(f"Properties: {connector.properties}")
except Exception as e:
    print(f"Error creating Connector: {e}")

print("\n=== Test 3: Check if validation happens on to_dict() ===")
vpc_incomplete = VpcInformation()
print("Created incomplete VpcInformation")
try:
    result = vpc_incomplete.to_dict()
    print(f"to_dict() succeeded even without required properties: {result}")
except Exception as e:
    print(f"to_dict() validation caught missing properties: {e}")

print("\n=== Test 4: Check validation method ===")
vpc_incomplete = VpcInformation()
try:
    vpc_incomplete._validate_props()
    print("_validate_props() passed even without required properties!")
except Exception as e:
    print(f"_validate_props() caught missing properties: {e}")