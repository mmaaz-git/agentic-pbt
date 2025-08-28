#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

# Test the actual Fibonacci sequence behavior
retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)

print("Testing FibonacciRetry sequence:")
for i in range(10):
    timeout = retry.get_timeout(i)
    print(f"Attempt {i}: timeout = {timeout}")

print("\n\nLet's trace through the implementation:")
print("Initial state: prev_step=1.0, current_step=1.0")

# Fresh instance to trace
retry2 = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)
print(f"Initial: prev_step={retry2.prev_step}, current_step={retry2.current_step}")

for i in range(5):
    print(f"\nCalling get_timeout({i}):")
    print(f"  Before: prev_step={retry2.prev_step}, current_step={retry2.current_step}")
    timeout = retry2.get_timeout(i)
    print(f"  Returned: {timeout}")
    print(f"  After: prev_step={retry2.prev_step}, current_step={retry2.current_step}")