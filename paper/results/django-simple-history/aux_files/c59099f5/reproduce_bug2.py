#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import math
from limits.storage import MemoryStorage

# Test the actual failing case more carefully
storage = MemoryStorage()
key = 'test'
limit = 1
expiry = 1

print("Test case: limit=1, attempting to acquire 1 entry twice")
print("=" * 60)

# First acquire - should succeed
result1 = storage.acquire_sliding_window_entry(key, limit, expiry, 1)
print(f"First acquire (amount=1, limit=1): {result1}")

# Check state after first acquire
prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
weighted = prev_count * prev_ttl / expiry + curr_count
print(f"After first acquire:")
print(f"  prev_count={prev_count}, prev_ttl={prev_ttl:.4f}")
print(f"  curr_count={curr_count}, curr_ttl={curr_ttl:.4f}")
print(f"  weighted_count = {prev_count} * {prev_ttl:.4f} / {expiry} + {curr_count} = {weighted:.4f}")
print(f"  floor(weighted_count) = {math.floor(weighted)}")

# Second acquire - should fail since we're at the limit
result2 = storage.acquire_sliding_window_entry(key, limit, expiry, 1)
print(f"\nSecond acquire (amount=1, limit=1): {result2}")

# Check state after second acquire
prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
weighted = prev_count * prev_ttl / expiry + curr_count
print(f"After second acquire:")
print(f"  prev_count={prev_count}, prev_ttl={prev_ttl:.4f}")
print(f"  curr_count={curr_count}, curr_ttl={curr_ttl:.4f}")
print(f"  weighted_count = {weighted:.4f}")
print(f"  floor(weighted_count) = {math.floor(weighted)}")

print("\n" + "=" * 60)
print("BUG ANALYSIS:")
print("=" * 60)

if result2:
    print("BUG FOUND: Second acquire succeeded when it should have failed!")
    print(f"  After first acquire, curr_count was {1}")
    print(f"  With limit={limit}, no more acquisitions should be allowed")
    print(f"  But second acquire returned True (succeeded)")
    
    print("\nLooking at the code (lines 201-203):")
    print("    weighted_count = previous_count * previous_ttl / expiry + current_count")
    print("    if floor(weighted_count) + amount > limit:")
    print("        return False")
    
    print(f"\n  Before 2nd acquire: floor({1}) + {1} = 2 > {limit} = True")
    print(f"  This SHOULD have caused the function to return False")
    print(f"  But it returned True instead!")
else:
    print("No bug - second acquire correctly failed")