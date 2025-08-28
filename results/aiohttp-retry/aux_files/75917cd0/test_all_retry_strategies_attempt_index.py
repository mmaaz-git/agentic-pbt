#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import (
    ExponentialRetry, ListRetry, FibonacciRetry, JitterRetry, RandomRetry
)


def test_all_strategies_with_1_based_attempt():
    """Test how all retry strategies handle 1-based attempt indexing.
    
    The retry logic in client.py passes current_attempt starting from 1.
    Let's see how each strategy handles this.
    """
    
    print("Testing all retry strategies with attempt values 1, 2, 3...")
    print("=" * 60)
    
    # ListRetry - we know this has a bug
    print("\n1. ListRetry with timeouts=[1.0, 2.0, 3.0]:")
    list_retry = ListRetry(timeouts=[1.0, 2.0, 3.0])
    for attempt in [1, 2, 3]:
        try:
            timeout = list_retry.get_timeout(attempt)
            print(f"   attempt={attempt}: timeout={timeout}")
        except IndexError as e:
            print(f"   attempt={attempt}: IndexError - {e}")
    
    # ExponentialRetry - uses attempt as exponent, so 1-based might be wrong
    print("\n2. ExponentialRetry (start=1.0, factor=2.0):")
    exp_retry = ExponentialRetry(attempts=3, start_timeout=1.0, factor=2.0, max_timeout=100.0)
    for attempt in [0, 1, 2, 3]:
        timeout = exp_retry.get_timeout(attempt)
        expected = 1.0 * (2.0 ** attempt)
        print(f"   attempt={attempt}: timeout={timeout}, expected={expected}")
    
    # FibonacciRetry - doesn't use attempt parameter at all!
    print("\n3. FibonacciRetry (multiplier=1.0):")
    fib_retry = FibonacciRetry(attempts=3, multiplier=1.0, max_timeout=100.0)
    for attempt in [1, 2, 3]:
        timeout = fib_retry.get_timeout(attempt)
        print(f"   attempt={attempt}: timeout={timeout}")
    
    # JitterRetry - inherits from ExponentialRetry
    print("\n4. JitterRetry (inherits from ExponentialRetry):")
    jitter_retry = JitterRetry(attempts=3, start_timeout=1.0, factor=2.0, max_timeout=100.0, random_interval_size=0.0)
    for attempt in [0, 1, 2, 3]:
        timeout = jitter_retry.get_timeout(attempt)
        expected = 1.0 * (2.0 ** attempt)
        print(f"   attempt={attempt}: timeout={timeout}, expected={expected}")
    
    # RandomRetry - doesn't use attempt parameter
    print("\n5. RandomRetry (min=1.0, max=1.0 for deterministic test):")
    random_retry = RandomRetry(attempts=3, min_timeout=1.0, max_timeout=1.0)
    for attempt in [1, 2, 3]:
        timeout = random_retry.get_timeout(attempt)
        print(f"   attempt={attempt}: timeout={timeout}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("- ListRetry: Has off-by-one error, skips first timeout and crashes on last attempt")
    print("- ExponentialRetry: If passed 1-based attempts, the first retry will use factor^1 instead of factor^0")
    print("- FibonacciRetry: Ignores attempt parameter, uses internal state instead")
    print("- JitterRetry: Same issue as ExponentialRetry (inherits from it)")
    print("- RandomRetry: Ignores attempt parameter")


if __name__ == "__main__":
    test_all_strategies_with_1_based_attempt()