#!/usr/bin/env python3
"""
Minimal reproduction of the name mutability bug in sentinels module.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

from sentinels import Sentinel

# Create a sentinel with name "foo"
sentinel = Sentinel("foo")
print(f"Created sentinel: {repr(sentinel)}")
print(f"Registry has 'foo': {'foo' in Sentinel._existing_instances}")

# Modify the internal _name attribute
sentinel._name = "bar"
print(f"\nModified _name to 'bar'")
print(f"Sentinel repr now: {repr(sentinel)}")

# Try to create a new sentinel with the original name "foo"
new_sentinel = Sentinel("foo")
print(f"\nCalled Sentinel('foo') again")
print(f"Got same object: {new_sentinel is sentinel}")
print(f"But its repr is: {repr(new_sentinel)}")

# This demonstrates the bug:
# 1. We created Sentinel("foo")
# 2. We changed its _name to "bar"
# 3. Calling Sentinel("foo") returns the same object
# 4. But that object now reports itself as <bar> instead of <foo>
#
# This violates the contract that Sentinel("foo") should always
# return a sentinel that represents itself as <foo>

print("\n=== BUG DEMONSTRATED ===")
print("Sentinel('foo') returns an object that claims to be <bar>")
print("This breaks the singleton contract and repr consistency.")