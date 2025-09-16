import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cloud9 as cloud9

# Bug: from_dict with empty string property name gives unclear error
print("Testing from_dict with empty string as property name...")

data = {
    "": "some_value",  # Empty string as property name
    "ImageId": "ami-12345678",
    "InstanceType": "t2.micro"
}

try:
    env = cloud9.EnvironmentEC2.from_dict("TestEnv", data)
    print("ERROR: Should have raised an error, but succeeded")
except AttributeError as e:
    print(f"Error message: {e}")
    print(f"BUG: Error message has double space after 'have a'")
    # The error says: "Object type EnvironmentEC2 does not have a  property."
    # Note the double space between "a" and "property"