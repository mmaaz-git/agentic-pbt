#!/usr/bin/env python3
"""Minimal reproduction of title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotevents as iotevents

# Bug: Non-string falsy values (0, False) bypass title validation
print("BUG DEMONSTRATION: Non-string values accepted as titles")
print("="*60)

# These should all fail but don't:
invalid_titles = [
    (0, "integer zero"),
    (False, "boolean False"),
    (None, "None"),
    ("", "empty string"),
]

for title, description in invalid_titles:
    try:
        obj = iotevents.Input(
            title=title,
            InputDefinition=iotevents.InputDefinition(
                Attributes=[iotevents.Attribute(JsonPath="/test")]
            )
        )
        print(f"✗ ACCEPTED {description}: title={repr(title)} (type: {type(title).__name__})")
    except (ValueError, TypeError) as e:
        print(f"✓ REJECTED {description}: {e}")

print("\n" + "="*60)
print("For comparison, truthy non-strings fail with unclear error:")

# These fail but with confusing error message:
other_invalid = [
    (123, "integer 123"),
    (True, "boolean True"),
]

for title, description in other_invalid:
    try:
        obj = iotevents.Input(
            title=title,
            InputDefinition=iotevents.InputDefinition(
                Attributes=[iotevents.Attribute(JsonPath="/test")]
            )
        )
        print(f"✗ ACCEPTED {description}: title={repr(title)}")
    except Exception as e:
        print(f"  {description}: {type(e).__name__}: {e}")

print("\n" + "="*60)
print("EXPECTED: All non-string values should be rejected")