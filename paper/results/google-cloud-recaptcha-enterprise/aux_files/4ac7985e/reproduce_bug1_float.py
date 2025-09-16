from google.protobuf import json_format
from google.protobuf import wrappers_pb2

# Bug 1: Float value too large
value = 3.402823364973241e+38

msg = wrappers_pb2.FloatValue()
msg.value = value

print(f"Original value: {msg.value}")
print(f"Value type: {type(msg.value)}")

json_str = json_format.MessageToJson(msg)
print(f"JSON representation: {json_str}")

parsed_msg = wrappers_pb2.FloatValue()
try:
    json_format.Parse(json_str, parsed_msg)
    print(f"Parsed value: {parsed_msg.value}")
except Exception as e:
    print(f"ERROR: {e}")
    print(f"This is a bug: FloatValue serializes to JSON but can't be parsed back")