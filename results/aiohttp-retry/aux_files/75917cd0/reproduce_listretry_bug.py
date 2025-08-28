#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import ListRetry


def reproduce_bug():
    """Reproduce the ListRetry off-by-one bug.
    
    The bug occurs because:
    1. The retry logic in client.py passes 1-based attempt indices to get_timeout()
    2. ListRetry.get_timeout() expects 0-based indices
    3. This causes the first timeout to be skipped and an IndexError on the last attempt
    """
    
    # Create a ListRetry with 3 different timeout values
    timeouts = [1.0, 2.0, 3.0]
    retry = ListRetry(timeouts=timeouts)
    
    print("BUG REPRODUCTION: ListRetry off-by-one error")
    print("=" * 50)
    print(f"Created ListRetry with timeouts={timeouts}")
    print(f"retry.attempts={retry.attempts}")
    print()
    
    # Simulate the actual retry logic from client.py
    print("Simulating retry logic from client.py:")
    print("(current_attempt starts at 0, incremented before use)")
    print()
    
    current_attempt = 0
    
    # First retry attempt
    current_attempt += 1  # This is what happens in client.py line 112
    print(f"Attempt {current_attempt}:")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) returned {timeout}")
        print(f"  BUG: Expected {timeouts[0]} (first timeout), got {timeouts[current_attempt]} instead!")
    except IndexError as e:
        print(f"  IndexError: {e}")
    print()
    
    # Second retry attempt
    current_attempt += 1
    print(f"Attempt {current_attempt}:")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) returned {timeout}")
        print(f"  BUG: Expected {timeouts[1]} (second timeout), got {timeouts[current_attempt]} instead!")
    except IndexError as e:
        print(f"  IndexError: {e}")
    print()
    
    # Third retry attempt - this will crash
    current_attempt += 1
    print(f"Attempt {current_attempt}:")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) returned {timeout}")
    except IndexError as e:
        print(f"  IndexError: {e}")
        print(f"  BUG: Crashed on attempt {current_attempt} of {retry.attempts}!")
    
    print()
    print("=" * 50)
    print("SUMMARY:")
    print("1. The first timeout value (1.0) is never used")
    print("2. The retry crashes with IndexError on the last attempt")
    print("3. This is a genuine off-by-one bug in ListRetry")


if __name__ == "__main__":
    reproduce_bug()