#!/usr/bin/env python3
"""Minimal reproduction of the YAML round-trip bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._yaml_api import yaml_dumps, yaml_loads

# The failing input: dictionary with key containing U+0085 (Next Line character)
data = {'0\x85': None}

print("Original data:", repr(data))
print("Original key:", repr(list(data.keys())[0]))
print("Key bytes:", list(data.keys())[0].encode('utf-8'))

# Serialize to YAML
serialized = yaml_dumps(data)
print("\nSerialized YAML:")
print(repr(serialized))

# Deserialize back
deserialized = yaml_loads(serialized)
print("\nDeserialized data:", repr(deserialized))
print("Deserialized key:", repr(list(deserialized.keys())[0]))
print("Key bytes:", list(deserialized.keys())[0].encode('utf-8'))

# Check if they match
print("\nRound-trip successful?", data == deserialized)
print("Keys match?", list(data.keys())[0] == list(deserialized.keys())[0])