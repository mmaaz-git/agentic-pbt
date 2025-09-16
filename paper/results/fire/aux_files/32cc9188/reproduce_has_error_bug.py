#!/usr/bin/env python3
"""Minimal reproduction of HasError() bug."""

import fire.trace as trace

# Create a FireTrace with initial component None
t = trace.FireTrace(None)

# Initially should have no error
print(f"HasError() before AddError: {t.HasError()}")  # Expected: False

# Add an error
error = ValueError('0')
t.AddError(error, [])

# Now should have error
print(f"HasError() after AddError: {t.HasError()}")  # Expected: True

# Check if this is actually True
if not t.HasError():
    print("BUG: HasError() returns False after AddError() was called!")
    print(f"Trace elements: {len(t.elements)}")
    print(f"Last element has error: {t.elements[-1].HasError() if t.elements else 'No elements'}")