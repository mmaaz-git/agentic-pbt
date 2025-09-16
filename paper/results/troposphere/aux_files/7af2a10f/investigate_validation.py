"""Investigate when validation happens in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy

# Test 1: Does validation happen on to_dict()?
print("Test 1: DeploymentGroup with mutually exclusive properties")
dg = codedeploy.DeploymentGroup(
    "TestDG",
    ApplicationName="TestApp",
    ServiceRoleArn="arn:aws:iam::123456789012:role/CodeDeployRole",
    Ec2TagFilters=[codedeploy.Ec2TagFilters(Key="Name", Value="Test")],
    Ec2TagSet=codedeploy.Ec2TagSet()
)

print("Calling to_dict()...")
try:
    result = dg.to_dict()
    print(f"to_dict() succeeded! Result keys: {result.keys()}")
except ValueError as e:
    print(f"to_dict() raised ValueError: {e}")

print("\nCalling to_dict(validation=False)...")
try:
    result = dg.to_dict(validation=False)
    print(f"to_dict(validation=False) succeeded! Result keys: {result.keys()}")
except ValueError as e:
    print(f"to_dict(validation=False) raised ValueError: {e}")

print("\nDirect call to validate()...")
try:
    dg.validate()
    print("validate() succeeded - this is the bug!")
except ValueError as e:
    print(f"validate() raised ValueError: {e}")

# Test 2: Does LoadBalancerInfo validation work?
print("\n\nTest 2: LoadBalancerInfo with multiple properties")
lb = codedeploy.LoadBalancerInfo(
    ElbInfoList=[codedeploy.ElbInfoList(Name="elb1")],
    TargetGroupInfoList=[codedeploy.TargetGroupInfo(Name="tg1")]
)

print("Calling to_dict()...")
try:
    result = lb.to_dict()
    print(f"to_dict() succeeded! Result: {result}")
except ValueError as e:
    print(f"to_dict() raised ValueError: {e}")

print("\nDirect call to validate()...")
try:
    lb.validate()
    print("validate() succeeded - unexpected!")
except ValueError as e:
    print(f"validate() raised ValueError: {e}")