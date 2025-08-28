#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import ExponentialRetry


def test_exponential_retry_with_actual_usage():
    """Test if ExponentialRetry has an off-by-one issue.
    
    The formula in ExponentialRetry is: start_timeout * (factor ** attempt)
    If attempt is 1-based instead of 0-based, the calculations will be wrong.
    """
    
    start_timeout = 1.0
    factor = 2.0
    retry = ExponentialRetry(attempts=3, start_timeout=start_timeout, factor=factor, max_timeout=100.0)
    
    print("Testing ExponentialRetry with actual retry logic")
    print("=" * 50)
    print(f"ExponentialRetry(start_timeout={start_timeout}, factor={factor})")
    print()
    
    # What we EXPECT if attempts are 0-based (correct behavior)
    print("Expected timeouts (0-based attempts):")
    for i in range(3):
        expected = start_timeout * (factor ** i)
        print(f"  Attempt {i}: {start_timeout} * {factor}^{i} = {expected}")
    print()
    
    # What ACTUALLY happens with 1-based attempts from client.py
    print("Actual timeouts (1-based attempts from client.py):")
    current_attempt = 0
    for i in range(3):
        current_attempt += 1  # This happens in client.py
        timeout = retry.get_timeout(current_attempt)
        print(f"  Attempt {current_attempt}: {start_timeout} * {factor}^{current_attempt} = {timeout}")
    
    print()
    print("BUG: The first attempt uses factor^1 instead of factor^0")
    print("     This means the first retry waits 2 seconds instead of 1 second")
    print("     All subsequent retries also wait twice as long as intended")


if __name__ == "__main__":
    test_exponential_retry_with_actual_usage()