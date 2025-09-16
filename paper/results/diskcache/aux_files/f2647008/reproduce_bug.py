#!/usr/bin/env python
"""Minimal reproduction of the Timeout handling bug in FanoutCache._remove."""

from diskcache.core import Timeout

# This simulates what happens in FanoutCache._remove (fanout.py line 489)
# when a Timeout is raised without a count argument

print("Demonstrating bug in FanoutCache._remove")
print("="*60)

# Case 1: Timeout with count (as raised by cull/clear)
try:
    timeout_with_count = Timeout(42)  # As raised in core.py lines 2149, 2201
    count = timeout_with_count.args[0]
    print(f"✓ Timeout with count: extracted {count}")
except IndexError:
    print("✗ Failed to extract count from Timeout(42)")

# Case 2: Timeout without count (as raised elsewhere)
try:
    timeout_no_count = Timeout()  # As raised in core.py line 730
    count = timeout_no_count.args[0]  # This line will fail
    print(f"✓ Timeout without args: extracted {count}")
except IndexError as e:
    print(f"✗ IndexError when accessing args[0]: {e}")
    print("  This is the bug in FanoutCache._remove!")

print("\nThe bug occurs in fanout.py lines 488-489:")
print("    except Timeout as timeout:")
print("        total += timeout.args[0]  # IndexError if Timeout has no args!")
print("\nThis assumes ALL Timeout exceptions have a count in args[0],")
print("but only some methods (cull, clear) actually provide this.")