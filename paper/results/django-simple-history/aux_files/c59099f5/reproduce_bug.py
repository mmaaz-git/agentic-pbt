#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.storage import MemoryStorage

# Minimal reproduction from Hypothesis
storage = MemoryStorage()
key = '0'
limit = 1
expiry = 1
initial_amount = 2
acquire_amount = 1

print(f"Testing with: limit={limit}, initial_amount={initial_amount}, acquire_amount={acquire_amount}")

# Try to acquire initial_amount (which is > limit)
result1 = storage.acquire_sliding_window_entry(key, limit, expiry, initial_amount)
print(f"First acquire (amount={initial_amount} > limit={limit}): {result1}")

# Check sliding window state
prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
print(f"After first attempt - prev_count: {prev_count}, curr_count: {curr_count}")

# Now try to acquire more
result2 = storage.acquire_sliding_window_entry(key, limit, expiry, acquire_amount)
print(f"Second acquire (amount={acquire_amount}): {result2}")

# Check final state
prev_count, prev_ttl, curr_count, curr_ttl = storage.get_sliding_window(key, expiry)
weighted = prev_count * prev_ttl / expiry + curr_count
print(f"Final state - prev_count: {prev_count}, curr_count: {curr_count}, weighted: {weighted}")

print("\n--- Analysis ---")
print(f"BUG: First acquire with amount={initial_amount} > limit={limit} returned {result1}")
print(f"Expected: False (should fail when amount > limit)")
print(f"Actual: {result1}")

if result1 is not False:
    print("\nLooking at the code (line 191-192):")
    print("    if amount > limit:")
    print("        return False")
    print(f"\nWith amount={initial_amount} and limit={limit}, the condition {initial_amount} > {limit} is {initial_amount > limit}")
    print("So the function SHOULD have returned False immediately.")