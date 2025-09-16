#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

print("Testing potential bug in FibonacciRetry")
print("="*50)

# Issue 1: The 'attempt' parameter is ignored!
print("\nIssue 1: The 'attempt' parameter seems to be ignored")
print("Creating a fresh FibonacciRetry instance...")
retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)

print("\nCalling get_timeout with different attempt numbers (should they all be different?):")
print(f"get_timeout(0) = {retry.get_timeout(0)}")
print(f"get_timeout(5) = {retry.get_timeout(5)}")  
print(f"get_timeout(1) = {retry.get_timeout(1)}")  
print(f"get_timeout(10) = {retry.get_timeout(10)}")

print("\n" + "="*50)
print("Issue 2: State pollution across different retry contexts")
print("\nIn a real retry scenario, we'd expect:")
print("- First request fails at attempts 0, 1, 2 with timeouts 2, 3, 5")
print("- Second request (different URL/context) should also get 2, 3, 5")
print("But if we reuse the same FibonacciRetry instance:")

retry2 = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)

print("\nFirst request retry sequence:")
for attempt in range(3):
    print(f"  Attempt {attempt}: timeout = {retry2.get_timeout(attempt)}")

print("\nSecond request (reusing same retry instance):")
for attempt in range(3):
    print(f"  Attempt {attempt}: timeout = {retry2.get_timeout(attempt)}")

print("\nThe second request gets different timeouts! This violates the expectation")
print("that retry behavior should be consistent across different requests.")

print("\n" + "="*50)
print("Issue 3: Comparison with ExponentialRetry")

from aiohttp_retry.retry_options import ExponentialRetry

exp_retry = ExponentialRetry(start_timeout=1.0, factor=2.0)
print("\nExponentialRetry properly uses the attempt parameter:")
print(f"get_timeout(0) = {exp_retry.get_timeout(0)}")
print(f"get_timeout(1) = {exp_retry.get_timeout(1)}")
print(f"get_timeout(2) = {exp_retry.get_timeout(2)}")
print("\nCalling again with same attempts gives same results:")
print(f"get_timeout(0) = {exp_retry.get_timeout(0)}")
print(f"get_timeout(1) = {exp_retry.get_timeout(1)}")
print(f"get_timeout(2) = {exp_retry.get_timeout(2)}")

print("\nBut FibonacciRetry ignores the attempt parameter completely!")