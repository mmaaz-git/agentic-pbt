#!/usr/bin/env python3
"""Bug discovery through code analysis and targeted testing"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotcoredeviceadvisor as iotcore
from troposphere import Tags

# Test 1: Check if Tags can be added to SuiteDefinition
print("Test 1: Tags on SuiteDefinition")
config = iotcore.SuiteDefinitionConfiguration(
    DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
    RootGroup="TestGroup"
)

# According to the props, Tags should be accepted
suite = iotcore.SuiteDefinition(
    title="TestSuite",
    SuiteDefinitionConfiguration=config,
    Tags=Tags(Key1="Value1", Key2="Value2")
)

# Serialize and check
suite_dict = suite.to_dict()
print(f"Suite dict keys: {suite_dict.keys()}")
if 'Properties' in suite_dict:
    print(f"Properties keys: {suite_dict['Properties'].keys()}")

# Test 2: Check IntendedForQualification boolean handling
print("\nTest 2: IntendedForQualification with integer boolean")
from troposphere.validators import boolean

# The props show IntendedForQualification uses the boolean validator
# Let's test if it properly converts integers
config2 = iotcore.SuiteDefinitionConfiguration(
    DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
    RootGroup="TestGroup",
    IntendedForQualification=1  # Should be converted to True by boolean validator
)

config2_dict = config2.to_dict()
print(f"IntendedForQualification value: {config2_dict.get('IntendedForQualification')}")
print(f"IntendedForQualification type: {type(config2_dict.get('IntendedForQualification'))}")

# Test 3: Check what happens with extra/unknown properties
print("\nTest 3: Unknown properties handling")
try:
    config3 = iotcore.SuiteDefinitionConfiguration(
        DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
        RootGroup="TestGroup",
        UnknownProperty="ShouldFail"  # This should raise an error
    )
    print("BUG: Accepted unknown property 'UnknownProperty'")
except AttributeError as e:
    print(f"OK: Correctly rejected unknown property: {e}")

# Test 4: Empty Devices list
print("\nTest 4: Empty Devices list")
config4 = iotcore.SuiteDefinitionConfiguration(
    DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
    RootGroup="TestGroup",
    Devices=[]  # Empty list should be valid
)
config4_dict = config4.to_dict()
print(f"Devices in dict: {'Devices' in config4_dict}")
if 'Devices' in config4_dict:
    print(f"Devices value: {config4_dict['Devices']}")

# Test 5: DeviceUnderTest with both fields None
print("\nTest 5: DeviceUnderTest with no fields")
device_empty = iotcore.DeviceUnderTest()  # No args - both fields are optional
device_dict = device_empty.to_dict()
print(f"Empty device dict: {device_dict}")
print(f"Is empty dict: {len(device_dict) == 0}")