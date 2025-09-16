#!/usr/bin/env python3
"""
Minimal reproducer for Django JSONField empty collection bug.
When passing empty Python collections directly to JSONField.clean(),
they are incorrectly converted to None.
"""

import django
from django.conf import settings

# Configure minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test-secret-key',
)
django.setup()

from django.forms import JSONField

# Create a JSONField
field = JSONField(required=False)

# Test cases showing the bug
print("JSONField.clean() with empty collections:")
print("-" * 40)

# Bug: Empty list becomes None
empty_list = []
result = field.clean(empty_list)
print(f"field.clean([]) = {result!r}")
print(f"Expected: []")
print(f"Got: {result}")
assert result == [], f"BUG: Empty list [] became {result}"

# Bug: Empty dict becomes None  
empty_dict = {}
result = field.clean(empty_dict)
print(f"\nfield.clean({{}}) = {result!r}")
print(f"Expected: {{}}")
print(f"Got: {result}")
assert result == {}, f"BUG: Empty dict {{}} became {result}"

# Non-empty collections work fine
print("\n\nFor comparison, non-empty collections work:")
print(f"field.clean([1]) = {field.clean([1])!r}")  # Works: [1]
print(f"field.clean({{'a': 1}}) = {field.clean({'a': 1})!r}")  # Works: {'a': 1}