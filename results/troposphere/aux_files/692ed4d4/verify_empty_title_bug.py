#!/usr/bin/env python3
"""Verify the empty title validation bypass bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import analytics

# Test various falsy values
test_cases = [
    ("", "empty string"),
    (None, "None"),
]

for title, description in test_cases:
    print(f"Testing {description} as title:")
    try:
        app = analytics.Application(title)
        print(f"  ✓ Created Application with title: {repr(app.title)}")
        
        # Try to call to_dict which should trigger validation
        try:
            result = app.to_dict()
            print(f"  ✓ to_dict() succeeded, returned: {result}")
        except Exception as e:
            print(f"  ✗ to_dict() failed: {e}")
            
    except Exception as e:
        print(f"  ✗ Failed to create: {e}")
    print()

# Test that invalid non-empty strings do fail
print("Testing invalid non-empty string 'test-app':")
try:
    app = analytics.Application("test-app")
    print(f"  ✓ Created Application with title: {repr(app.title)}")
    try:
        result = app.to_dict()
        print(f"  ✓ to_dict() succeeded (should have failed!)")
    except Exception as e:
        print(f"  ✗ to_dict() failed (expected): {e}")
except ValueError as e:
    print(f"  ✗ Failed to create (expected): {e}")

print("\nTesting valid string 'ValidName123':")
try:
    app = analytics.Application("ValidName123")
    print(f"  ✓ Created Application with title: {repr(app.title)}")
    result = app.to_dict()
    print(f"  ✓ to_dict() succeeded")
except Exception as e:
    print(f"  ✗ Failed unexpectedly: {e}")