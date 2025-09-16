#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

# Test Fibonacci retry state mutation bug
print("Testing FibonacciRetry state mutation...")
retry1 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
retry2 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)

# Get timeouts from first instance
seq1 = []
for i in range(5):
    timeout = retry1.get_timeout(i)
    seq1.append(timeout)

# Get timeouts from second instance  
seq2 = []
for i in range(5):
    timeout = retry2.get_timeout(i)
    seq2.append(timeout)

print(f"Instance 1 sequence: {seq1}")
print(f"Instance 2 sequence: {seq2}")

# Check if they match
if seq1 == seq2:
    print("✓ Sequences match - no bug found")
else:
    print("✗ BUG FOUND: Fresh instances give different sequences!")
    print("  This violates the expectation that fresh instances should behave identically")

# Let's also verify the Fibonacci pattern
expected_fib = [1.0, 2.0, 3.0, 5.0, 8.0]
print(f"\nExpected Fibonacci: {expected_fib}")
print(f"Actual from inst 1: {seq1}")

if seq1 != expected_fib:
    print("✗ BUG FOUND: Does not follow Fibonacci sequence!")
    
# Let's check if calling get_timeout changes internal state
print("\n\nTesting if get_timeout mutates state...")
retry3 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)

# Call with same index multiple times
val1 = retry3.get_timeout(0)
val2 = retry3.get_timeout(0)
val3 = retry3.get_timeout(0)

print(f"Calling get_timeout(0) three times: {val1}, {val2}, {val3}")

if val1 != val2 or val2 != val3:
    print("✗ BUG FOUND: get_timeout(0) returns different values on repeated calls!")
    print("  This indicates the internal state is being mutated incorrectly")