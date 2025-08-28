"""Minimal reproduction of CodeDeployLambdaAliasUpdate bug"""

import troposphere.policies as policies

# Create instance of the class
obj = policies.CodeDeployLambdaAliasUpdate()

# According to AWS CloudFormation docs, ApplicationName should be a string
# representing the name of a CodeDeploy application
# See: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-codedeploy-lambdaalias-update.html

print("Attempting to set ApplicationName to 'MyCodeDeployApp' (a valid application name)...")
try:
    obj.ApplicationName = "MyCodeDeployApp"
    print(f"Success! ApplicationName = {obj.ApplicationName}")
except ValueError as e:
    print(f"Failed with ValueError: {e}")
    print("The field uses a boolean validator but AWS expects a string!")

print("\nAttempting to set DeploymentGroupName to 'MyDeploymentGroup' (a valid group name)...")
try:
    obj.DeploymentGroupName = "MyDeploymentGroup"
    print(f"Success! DeploymentGroupName = {obj.DeploymentGroupName}")
except ValueError as e:
    print(f"Failed with ValueError: {e}")
    print("The field uses a boolean validator but AWS expects a string!")

print("\n--- Bug Analysis ---")
print("CodeDeployLambdaAliasUpdate has incorrect validators:")
print(f"  ApplicationName: {policies.CodeDeployLambdaAliasUpdate.props['ApplicationName']}")
print(f"  DeploymentGroupName: {policies.CodeDeployLambdaAliasUpdate.props['DeploymentGroupName']}")
print("\nThese use (boolean, True) but should use (str, True) based on AWS documentation.")