from google.protobuf import json_format
from google.protobuf import wrappers_pb2

# Bug 3: Unicode surrogate characters
value = '\ud800'

print(f"Testing Unicode surrogate character: {repr(value)}")

msg = wrappers_pb2.StringValue()
try:
    msg.value = value
    print(f"Successfully set value: {repr(msg.value)}")
    
    json_str = json_format.MessageToJson(msg)
    print(f"JSON representation: {json_str}")
    
    parsed_msg = wrappers_pb2.StringValue()
    json_format.Parse(json_str, parsed_msg)
    print(f"Parsed value: {repr(parsed_msg.value)}")
except UnicodeEncodeError as e:
    print(f"UnicodeEncodeError: {e}")
    print("This is expected - surrogates are not valid Unicode strings")
except Exception as e:
    print(f"Unexpected error: {e}")