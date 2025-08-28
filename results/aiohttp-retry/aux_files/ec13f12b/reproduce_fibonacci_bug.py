#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

# Create a FibonacciRetry instance
retry = FibonacciRetry(attempts=5, multiplier=1.0, max_timeout=100.0)

# Call get_timeout(0) multiple times
print("Calling get_timeout(0) three times on the same instance:")
print(f"First call:  {retry.get_timeout(0)}")
print(f"Second call: {retry.get_timeout(0)}")
print(f"Third call:  {retry.get_timeout(0)}")

# Expected: All three calls should return the same value since we're asking for attempt 0
# Actual: Each call returns a different value (2.0, 3.0, 5.0) following Fibonacci sequence

# This demonstrates that the class maintains internal state that affects
# subsequent calls, even when called with the same attempt number.

print("\n" + "="*50)
print("Testing with different attempt numbers in sequence:")
retry2 = FibonacciRetry(attempts=5, multiplier=1.0, max_timeout=100.0)
print(f"get_timeout(0): {retry2.get_timeout(0)}")
print(f"get_timeout(1): {retry2.get_timeout(1)}")  
print(f"get_timeout(2): {retry2.get_timeout(2)}")
print(f"get_timeout(0) again: {retry2.get_timeout(0)}")  # This will be different from the first call!

print("\n" + "="*50)
print("Compare with ExponentialRetry (correct behavior):")
from aiohttp_retry.retry_options import ExponentialRetry
exp_retry = ExponentialRetry(attempts=5, start_timeout=1.0, max_timeout=100.0, factor=2.0)
print(f"First call to get_timeout(0):  {exp_retry.get_timeout(0)}")
print(f"Second call to get_timeout(0): {exp_retry.get_timeout(0)}")
print(f"Third call to get_timeout(0):  {exp_retry.get_timeout(0)}")
print("All calls return the same value - this is correct!")