#!/usr/bin/env python3
"""Minimal reproduction of the has_changes bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyatlan.events.atlan_event_handler import AtlanEventHandler
from pyatlan.model.assets import Asset

# Create handler
client = Mock()
handler = AtlanEventHandler(client)

# Create two mock assets
asset1 = Mock(spec=Asset)
asset2 = Mock(spec=Asset)

# Make them equal
asset1.__eq__ = lambda self, other: True
asset2.__eq__ = lambda self, other: True

# Test has_changes
result = handler.has_changes(asset1, asset2)
print(f"When assets are equal, has_changes returns: {result}")
print(f"Expected: False (no changes when equal)")
print(f"Bug: Returns {result}, but should return False when assets are equal")

# Make them not equal
asset3 = Mock(spec=Asset)
asset4 = Mock(spec=Asset)
asset3.__eq__ = lambda self, other: False
asset4.__eq__ = lambda self, other: False

result2 = handler.has_changes(asset3, asset4)
print(f"\nWhen assets are not equal, has_changes returns: {result2}")
print(f"Expected: True (has changes when not equal)")
print(f"Bug: Returns {result2}, but should return True when assets are not equal")

print("\n--- EXPLANATION ---")
print("The has_changes method's documentation says:")
print("':returns: True if the modified asset should be sent on to (updated in) Atlan, or False if there are no actual changes to apply'")
print("\nBut the implementation returns `current == modified`, which is backwards!")
print("It returns True when they're equal (no changes) and False when they're different (has changes).")
print("This is the opposite of what the documentation claims.")