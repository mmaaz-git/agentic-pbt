"""Test to demonstrate integer validation behavior."""

import sys
import json

# Add the venv site-packages to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediapackage import StreamSelection

# Test 1: Float values are accepted but not converted to int
stream_selection = StreamSelection()
stream_selection.MaxVideoBitsPerSecond = 100.5

print("Test 1: Float value 100.5 assigned to MaxVideoBitsPerSecond")
print(f"  Value type: {type(stream_selection.MaxVideoBitsPerSecond)}")
print(f"  Value: {stream_selection.MaxVideoBitsPerSecond}")

# Convert to dict to see how it's serialized
dict_repr = stream_selection.to_dict()
print(f"  Dict representation: {dict_repr}")
print(f"  JSON representation: {json.dumps(dict_repr)}")

# Test 2: Check if the float value is preserved through serialization
stream_selection2 = StreamSelection()
stream_selection2.MinVideoBitsPerSecond = 50.9
stream_selection2.MaxVideoBitsPerSecond = 100.1

dict_repr2 = stream_selection2.to_dict()
print("\nTest 2: Multiple float values")
print(f"  Dict: {dict_repr2}")
print(f"  JSON: {json.dumps(dict_repr2)}")

# Test 3: Test with negative float
stream_selection3 = StreamSelection()
stream_selection3.MaxVideoBitsPerSecond = -10.5
dict_repr3 = stream_selection3.to_dict()
print("\nTest 3: Negative float value -10.5")
print(f"  Dict: {dict_repr3}")
print(f"  JSON: {json.dumps(dict_repr3)}")

# Test 4: Test if AWS CloudFormation would accept these float values
# CloudFormation expects integer types for these properties
print("\nCloudFormation Expectation:")
print("  MaxVideoBitsPerSecond should be type: Integer")
print("  MinVideoBitsPerSecond should be type: Integer")
print("  But troposphere allows floats and serializes them as floats!")