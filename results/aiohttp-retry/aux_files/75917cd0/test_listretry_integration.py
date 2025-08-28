#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import ListRetry


def test_listretry_integration_with_retry_logic():
    """Test how ListRetry interacts with the actual retry logic.
    
    Looking at client.py lines 106-149, the retry logic works as follows:
    1. current_attempt starts at 0
    2. It's incremented to 1 before first use (line 112)
    3. get_timeout is called with current_attempt (line 138 or 149)
    
    So get_timeout will be called with values 1, 2, 3, ... up to self.attempts
    But ListRetry.get_timeout expects 0-based indices!
    """
    
    timeouts = [1.0, 2.0, 3.0]
    retry = ListRetry(timeouts=timeouts)
    
    print(f"ListRetry created with timeouts={timeouts}")
    print(f"retry.attempts = {retry.attempts}")
    
    # Simulate the retry logic from client.py
    current_attempt = 0
    
    # First attempt
    current_attempt += 1  # Line 112 in client.py
    print(f"\nAttempt {current_attempt}:")
    
    # Line 138 or 149 would call get_timeout with current_attempt
    # But current_attempt is 1, and valid indices are 0, 1, 2
    # So this should access timeouts[1] = 2.0, not timeouts[0] = 1.0!
    
    try:
        # This simulates line 138/149 in client.py
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) = {timeout}")
        print(f"  Expected timeouts[0] = {timeouts[0]}, but got timeouts[{current_attempt}] = {timeout}")
    except IndexError as e:
        print(f"  IndexError: {e}")
    
    # Second attempt
    current_attempt += 1
    print(f"\nAttempt {current_attempt}:")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) = {timeout}")
    except IndexError as e:
        print(f"  IndexError: {e}")
    
    # Third attempt
    current_attempt += 1
    print(f"\nAttempt {current_attempt}:")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) = {timeout}")
    except IndexError as e:
        print(f"  IndexError: {e}")
    
    # Fourth attempt - this should definitely fail
    current_attempt += 1
    print(f"\nAttempt {current_attempt} (should fail):")
    try:
        timeout = retry.get_timeout(attempt=current_attempt)
        print(f"  get_timeout({current_attempt}) = {timeout}")
        print(f"  ERROR: Should have raised IndexError!")
    except IndexError as e:
        print(f"  IndexError (expected): {e}")


def test_correct_usage():
    """Test what the correct usage should be."""
    timeouts = [1.0, 2.0, 3.0]
    retry = ListRetry(timeouts=timeouts)
    
    print("\nCorrect usage (0-based indexing):")
    for attempt in range(retry.attempts):
        timeout = retry.get_timeout(attempt)
        print(f"  get_timeout({attempt}) = {timeout}")


if __name__ == "__main__":
    print("Testing ListRetry integration with retry logic")
    print("=" * 50)
    test_listretry_integration_with_retry_logic()
    print("\n" + "=" * 50)
    test_correct_usage()