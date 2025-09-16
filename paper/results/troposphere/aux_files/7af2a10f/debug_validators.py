"""Debug the validators to understand why DeploymentGroup validation fails."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy, NoValue
from troposphere.validators.codedeploy import validate_deployment_group

# Create a DeploymentGroup with both EC2 properties
dg = codedeploy.DeploymentGroup(
    "TestDG",
    ApplicationName="TestApp",
    ServiceRoleArn="arn:aws:iam::123456789012:role/CodeDeployRole",
    Ec2TagFilters=[codedeploy.Ec2TagFilters(Key="Name", Value="Test")],
    Ec2TagSet=codedeploy.Ec2TagSet()
)

print("DeploymentGroup properties:")
for key, value in dg.properties.items():
    print(f"  {key}: {value!r}")

print("\nChecking what validate_deployment_group expects...")
print(f"validate_deployment_group expects these property names:")
print(f"  EC2: ['EC2TagFilters', 'Ec2TagSet']")
print(f"  OnPremises: ['OnPremisesInstanceTagFilters', 'OnPremisesTagSet']")

print("\nActual property names in object:")
print(f"  {list(dg.properties.keys())}")

print("\nNote the case difference!")
print("  Expected: 'EC2TagFilters' (from validator)")  
print("  Actual: 'Ec2TagFilters' (from props definition)")

# Call the validator directly
print("\nCalling validate_deployment_group directly...")
try:
    validate_deployment_group(dg)
    print("No error raised - the bug is confirmed!")
except ValueError as e:
    print(f"Error raised: {e}")