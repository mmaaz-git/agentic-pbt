from google.protobuf import json_format
from google.protobuf import struct_pb2

# Bug 2: Struct with keys that look like scientific notation
msg = struct_pb2.Struct()
msg.fields["0E"].null_value = struct_pb2.NULL_VALUE
msg.fields["00000000"].null_value = struct_pb2.NULL_VALUE

print("Original message fields:")
for key in msg.fields:
    print(f"  {key}: {msg.fields[key]}")

json_str = json_format.MessageToJson(msg)
print(f"\nJSON representation:\n{json_str}")

parsed_msg = struct_pb2.Struct()
json_format.Parse(json_str, parsed_msg)

print("\nParsed message fields:")
for key in parsed_msg.fields:
    print(f"  {key}: {parsed_msg.fields[key]}")

# Check if the order matters for equality
json1 = json_format.MessageToJson(msg)
json2 = json_format.MessageToJson(parsed_msg)

print(f"\nOriginal JSON:\n{json1}")
print(f"\nRound-tripped JSON:\n{json2}")
print(f"\nJSON strings equal: {json1 == json2}")

# Check if messages are equal
print(f"Messages equal: {msg == parsed_msg}")