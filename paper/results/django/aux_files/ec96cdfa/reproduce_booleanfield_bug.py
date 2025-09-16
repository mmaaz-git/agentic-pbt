#!/usr/bin/env python3
"""
Minimal reproducer for Django BooleanField counterintuitive behavior.
The strings 'no' and 'off' are interpreted as True instead of False.
"""

import django
from django.conf import settings

# Configure minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-secret-key',
)
django.setup()

from django.forms import BooleanField

# Create a BooleanField
field = BooleanField(required=False)

print("BooleanField.clean() with 'no' and 'off' strings:")
print("-" * 50)

# Bug: 'no' becomes True
result = field.clean('no')
print(f"field.clean('no') = {result}")
print(f"Expected: False (intuitive for 'no')")
print(f"Got: {result}")
assert result == False, f"BUG: 'no' was interpreted as {result}"

# Bug: 'off' becomes True
result = field.clean('off')
print(f"\nfield.clean('off') = {result}")
print(f"Expected: False (intuitive for 'off')")
print(f"Got: {result}")
assert result == False, f"BUG: 'off' was interpreted as {result}"

# For comparison, these work as expected:
print("\n\nFor comparison, these work as expected:")
print(f"field.clean('yes') = {field.clean('yes')}")     # True (correct)
print(f"field.clean('on') = {field.clean('on')}")       # True (correct)
print(f"field.clean('false') = {field.clean('false')}")  # False (correct)
print(f"field.clean('0') = {field.clean('0')}")         # False (correct)