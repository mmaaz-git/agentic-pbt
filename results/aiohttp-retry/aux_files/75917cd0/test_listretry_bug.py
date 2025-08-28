#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, example

from aiohttp_retry.retry_options import ListRetry


@given(
    timeouts=st.lists(st.floats(min_value=0.1, max_value=10.0), min_size=1, max_size=5),
    extra_attempts=st.integers(min_value=0, max_value=5)
)
@example(timeouts=[1.0, 2.0], extra_attempts=1)  # Specific failing case
def test_listretry_out_of_bounds_access(timeouts, extra_attempts):
    """Test that ListRetry.get_timeout can access out-of-bounds indices.
    
    The ListRetry class sets self.attempts = len(timeouts), but the get_timeout
    method is called with attempt indices that can range from 0 to attempts-1.
    However, in the retry logic in client.py, the attempt counter starts at 1
    and can go up to self.attempts, meaning get_timeout could be called with
    attempt values from 0 to attempts-1.
    
    The issue is that when retrying, the code might call get_timeout with an
    attempt value that equals or exceeds len(timeouts).
    """
    retry = ListRetry(timeouts=timeouts)
    
    # Attempts is set to len(timeouts)
    assert retry.attempts == len(timeouts)
    
    # Valid indices should be 0 to len(timeouts)-1
    for i in range(len(timeouts)):
        timeout = retry.get_timeout(i)
        assert timeout == timeouts[i]
    
    # But what happens if we call with attempt = len(timeouts)?
    # This simulates what could happen in the retry loop
    invalid_attempt = len(timeouts) + extra_attempts
    try:
        timeout = retry.get_timeout(invalid_attempt)
        print(f"ERROR: No IndexError raised for attempt={invalid_attempt}, len(timeouts)={len(timeouts)}")
        print(f"Got timeout={timeout}")
        # This should have raised an IndexError
        assert False, "Expected IndexError but none was raised"
    except IndexError as e:
        # This is expected
        print(f"IndexError raised as expected: {e}")
        pass


if __name__ == "__main__":
    # Run directly to see the issue
    print("Testing with a simple case: timeouts=[1.0, 2.0], attempt=2")
    retry = ListRetry(timeouts=[1.0, 2.0])
    print(f"retry.attempts = {retry.attempts}")
    print(f"len(timeouts) = 2")
    
    try:
        # This should fail since valid indices are 0 and 1
        timeout = retry.get_timeout(2)
        print(f"ERROR: No exception raised! Got timeout={timeout}")
    except IndexError as e:
        print(f"IndexError raised (expected): {e}")
    
    print("\nRunning property-based tests...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])