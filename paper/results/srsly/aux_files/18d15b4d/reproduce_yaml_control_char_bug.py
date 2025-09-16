#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
import srsly

# Test YAML with control characters in dictionary keys
print("Testing YAML with control characters in dictionary keys:")
print()

# The character that Hypothesis found
test_char = '\x85'  # NEL (Next Line) character
test_data = {test_char: None}

print(f"Original data: {repr(test_data)}")
print(f"Key character code: U+{ord(test_char):04X} (NEL - Next Line)")
print()

# Serialize to YAML
yaml_str = srsly.yaml_dumps(test_data)
print(f"Serialized YAML:")
print(repr(yaml_str))
print()
print("Raw YAML output:")
print(yaml_str)
print()

# Deserialize back
deserialized = srsly.yaml_loads(yaml_str)
print(f"Deserialized data: {repr(deserialized)}")
print()

# Check if they're equal
print(f"Are they equal? {test_data == deserialized}")

if test_data != deserialized:
    print("\nDifference found!")
    original_key = list(test_data.keys())[0]
    deserialized_key = list(deserialized.keys())[0]
    print(f"  Original key: {repr(original_key)} (U+{ord(original_key):04X})")
    print(f"  Deserialized key: {repr(deserialized_key)} (U+{ord(deserialized_key):04X})")

# Test more control characters
print("\n" + "="*60)
print("Testing various control characters:")
control_chars = [
    ('\x00', 'NULL'),
    ('\x01', 'SOH'),
    ('\x09', 'TAB'),
    ('\x0A', 'LF'),
    ('\x0D', 'CR'),
    ('\x1F', 'US'),
    ('\x7F', 'DEL'),
    ('\x85', 'NEL'),
    ('\xA0', 'NBSP'),
]

for char, name in control_chars:
    test_data = {char: f"value_for_{name}"}
    try:
        yaml_str = srsly.yaml_dumps(test_data)
        deserialized = srsly.yaml_loads(yaml_str)
        original_key = list(test_data.keys())[0]
        deserialized_key = list(deserialized.keys())[0]
        
        if original_key == deserialized_key:
            print(f"  U+{ord(char):04X} ({name:4}): ✓ Preserved correctly")
        else:
            print(f"  U+{ord(char):04X} ({name:4}): ✗ Changed from {repr(original_key)} to {repr(deserialized_key)}")
    except Exception as e:
        print(f"  U+{ord(char):04X} ({name:4}): ERROR - {e}")