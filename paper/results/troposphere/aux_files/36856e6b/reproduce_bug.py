"""Minimal reproduction of the EnvironmentVariable validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codebuild import EnvironmentVariable

# Bug: EnvironmentVariable.validate() doesn't check for required properties

# According to the class definition, Name and Value are required (marked with True):
# props: PropsDictType = {
#     "Name": (str, True),
#     "Type": (str, False),
#     "Value": (str, True),
# }

# Test 1: Create EnvironmentVariable without any properties
env_var1 = EnvironmentVariable()
print(f"Created EnvironmentVariable with no properties: {env_var1.properties}")

# This should fail validation since Name and Value are required, but it doesn't
env_var1.validate()
print("✗ BUG: validate() passed without required Name and Value properties!")

# Test 2: Create with only Name (missing required Value)
env_var2 = EnvironmentVariable(Name="TEST_VAR")
print(f"\nCreated EnvironmentVariable with only Name: {env_var2.properties}")

env_var2.validate()
print("✗ BUG: validate() passed without required Value property!")

# Test 3: Create with only Value (missing required Name)
env_var3 = EnvironmentVariable(Value="test_value")
print(f"\nCreated EnvironmentVariable with only Value: {env_var3.properties}")

env_var3.validate()
print("✗ BUG: validate() passed without required Name property!")

print("\n" + "="*60)
print("CONCLUSION: EnvironmentVariable.validate() only checks the")
print("'Type' property if present, but doesn't verify that the") 
print("required 'Name' and 'Value' properties exist.")