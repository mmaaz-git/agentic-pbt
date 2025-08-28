#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

# Demonstrate the bug: FibonacciRetry ignores the attempt parameter
retry = FibonacciRetry(multiplier=1.0, max_timeout=1000.0)

# These should return different values based on the attempt number
# but they don't - the attempt parameter is completely ignored
print("FibonacciRetry ignores the attempt parameter:")
print(f"get_timeout(attempt=0) = {retry.get_timeout(0)}")  # Returns 2.0
print(f"get_timeout(attempt=5) = {retry.get_timeout(5)}")  # Returns 3.0, not what we'd expect for attempt 5
print(f"get_timeout(attempt=0) = {retry.get_timeout(0)}")  # Returns 5.0, not 2.0 again!