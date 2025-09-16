import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.registry

# Minimal reproduction of the bug
introspector = pyramid.registry.Introspector()

# Create first introspectable
intr1 = pyramid.registry.Introspectable('cat1', 'disc1', 'title1', 'type1')

# Try to unrelate from a non-existent introspectable
intr1.unrelate('cat2', 'disc2')

# Register intr1 - this will process the unrelate command
# This should handle the case gracefully, but it raises KeyError instead
try:
    intr1.register(introspector, None)
    print("No error - unexpected")
except KeyError as e:
    print(f"KeyError raised: {e}")
    print("Bug confirmed: unrelate() fails when target doesn't exist")