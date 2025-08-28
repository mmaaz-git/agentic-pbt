"""Reproduce DeploymentGroup validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy

# According to the documentation and validators, having both Ec2TagFilters 
# and Ec2TagSet should be mutually exclusive and raise an error
dg = codedeploy.DeploymentGroup(
    "TestDG",
    ApplicationName="TestApp",
    ServiceRoleArn="arn:aws:iam::123456789012:role/CodeDeployRole",
    Ec2TagFilters=[codedeploy.Ec2TagFilters(Key="Name", Value="Test")],
    Ec2TagSet=codedeploy.Ec2TagSet()
)

print("DeploymentGroup created with both Ec2TagFilters and Ec2TagSet")

# Try to validate - should raise ValueError  
try:
    dg.validate()
    print("ERROR: validate() did not raise an exception!")
    print("This violates the mutually_exclusive constraint defined in validators/codedeploy.py")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")