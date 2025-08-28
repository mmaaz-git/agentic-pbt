#!/usr/bin/env python3
"""Investigate the bugs found in troposphere.iotevents"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotevents as iotevents

# Test 1: Character 'µ' should not be considered alphanumeric
print("Test 1: Testing with 'µ' as title")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title='µ',
        InputDefinition=input_def
    )
    print(f"Created object with title 'µ': {obj}")
except ValueError as e:
    print(f"ValueError: {e}")

# Test 2: What happens with title '0'?
print("\nTest 2: Testing with '0' as title")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title='0',
        InputDefinition=input_def
    )
    dict_repr = obj.to_dict()
    print(f"Created object with title '0'")
    print(f"Dict representation keys: {list(dict_repr.keys())}")
    print(f"Full dict: {dict_repr}")
except Exception as e:
    print(f"Exception: {e}")

# Test 3: What about other numeric titles?
print("\nTest 3: Testing with '123' as title")
try:
    attr = iotevents.Attribute(JsonPath="/test")
    input_def = iotevents.InputDefinition(Attributes=[attr])
    obj = iotevents.Input(
        title='123',
        InputDefinition=input_def
    )
    dict_repr = obj.to_dict()
    print(f"Created object with title '123'")
    print(f"Dict representation keys: {list(dict_repr.keys())}")
except Exception as e:
    print(f"Exception: {e}")

# Test 4: Check the regex pattern
import re
print("\nTest 4: Checking regex pattern")
pattern = re.compile(r'^[a-zA-Z0-9]+$')
test_strings = ['µ', '0', '123', 'Test', 'Test123', 'Test_123', 'Test-123', 'Tëst']
for s in test_strings:
    matches = bool(pattern.match(s))
    print(f"'{s}': {matches}")