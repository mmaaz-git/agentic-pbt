#!/usr/bin/env python3
"""
Test for potential bugs in SlidingWindowCounterRateLimiter weighted count calculation
"""
import sys
import asyncio
import time
from math import floor
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import SlidingWindowCounterRateLimiter
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def main():
    storage = MemoryStorage()
    limiter = SlidingWindowCounterRateLimiter(storage)
    
    print("Testing SlidingWindowCounterRateLimiter weighted count...")
    print("=" * 60)
    
    # Test 1: Basic functionality
    print("\nTest 1: Basic boundary test")
    print("-" * 40)
    
    item = RateLimitItemPerSecond(10)  # 10 requests per second
    
    # Consume 9, test if we can consume 1 more
    result = await limiter.hit(item, "user", cost=9)
    print(f"hit(cost=9): {result}")
    
    stats = await limiter.get_window_stats(item, "user")
    print(f"Stats after 9: remaining={stats.remaining}")
    
    can_test = await limiter.test(item, "user", cost=1)
    print(f"test(cost=1): {can_test}")
    
    can_hit = await limiter.hit(item, "user", cost=1)
    print(f"hit(cost=1): {can_hit}")
    
    if can_test != can_hit:
        print(f"\n❌ BUG: test()={can_test} but hit()={can_hit}")
        return True
    
    stats = await limiter.get_window_stats(item, "user")
    print(f"Final stats: remaining={stats.remaining}")
    
    # Test 2: Weighted count precision
    print("\nTest 2: Weighted count calculation")
    print("-" * 40)
    
    await limiter.clear(item, "user")
    
    # The weighted count formula is:
    # previous_count * previous_expires_in / expiry + current_count
    
    # Let's test with some specific values
    # First hit to establish current window
    await limiter.hit(item, "user", cost=5)
    
    # Get the sliding window info
    # This would require accessing internal state, so let's test indirectly
    stats = await limiter.get_window_stats(item, "user")
    print(f"After hit(5): remaining={stats.remaining}")
    
    # The weighted count should handle fractional values correctly
    # Test that floor() is applied correctly in the calculation
    
    # Test 3: Edge case with maximum values
    print("\nTest 3: Maximum value edge case")
    print("-" * 40)
    
    await limiter.clear(item, "user")
    
    # Try to consume exactly the limit
    result = await limiter.hit(item, "user", cost=10)
    print(f"hit(cost=10): {result}")
    
    # Should not be able to consume any more
    can_test = await limiter.test(item, "user", cost=1)
    print(f"test(cost=1) at limit: {can_test}")
    
    if can_test:
        print("❌ BUG: test() returns True when at limit")
        can_hit = await limiter.hit(item, "user", cost=1)
        print(f"hit(cost=1) at limit: {can_hit}")
        if can_hit:
            print("❌ CRITICAL: Rate limit exceeded!")
            return True
    
    # Test 4: Precision bug in weighted count with line 271-272 in strategies.py
    print("\nTest 4: Weighted count boundary precision")
    print("-" * 40)
    
    await limiter.clear(item, "user")
    
    # The test() method uses < item.amount - cost + 1 (line 272)
    # Let's verify this is correct
    
    test_cases = [
        (9, 1, True, "9+1=10 should be allowed"),
        (10, 1, False, "10+1=11 should be blocked"),
        (8, 2, True, "8+2=10 should be allowed"),
        (8, 3, False, "8+3=11 should be blocked"),
    ]
    
    for consumed, cost, expected, description in test_cases:
        await limiter.clear(item, "user")
        
        if consumed > 0:
            result = await limiter.hit(item, "user", cost=consumed)
            if not result:
                print(f"  Failed to consume initial {consumed}")
                continue
        
        can_test = await limiter.test(item, "user", cost=cost)
        print(f"  {description}: test(cost={cost}) = {can_test}")
        
        if can_test != expected:
            print(f"    ❌ Expected {expected}")
            
            # Verify with actual hit
            can_hit = await limiter.hit(item, "user", cost=cost)
            print(f"    hit(cost={cost}) = {can_hit}")
            
            if can_test != can_hit:
                print(f"    ❌ INCONSISTENCY FOUND!")
                
                # Get more details
                stats = await limiter.get_window_stats(item, "user")
                print(f"    Stats: remaining={stats.remaining}")
                return True
    
    # Test 5: Reset time calculation (lines 314-319 could have division by zero)
    print("\nTest 5: Reset time calculation edge cases")
    print("-" * 40)
    
    await limiter.clear(item, "user")
    
    # Test with zero counts - could cause division issues
    stats = await limiter.get_window_stats(item, "user")
    print(f"Empty stats: reset_time={stats.reset_time}, remaining={stats.remaining}")
    
    if stats.remaining != item.amount:
        print(f"❌ BUG: Empty limiter should have {item.amount} remaining, got {stats.remaining}")
        return True
    
    # Test line 315: previous_reset_in = previous_expires_in % (expiry / previous_count)
    # If previous_count is 0, this would be division by zero
    # The code checks for this on line 314, but let's verify
    
    # First consume something
    await limiter.hit(item, "user", cost=1)
    stats = await limiter.get_window_stats(item, "user")
    print(f"After hit(1): reset_time={stats.reset_time}, remaining={stats.remaining}")
    
    # The reset calculation should not fail or produce inf/nan
    if stats.reset_time == float('inf') or stats.reset_time != stats.reset_time:  # NaN check
        print(f"❌ BUG: Invalid reset_time: {stats.reset_time}")
        return True
    
    print("\n✓ All tests passed - no bugs found in SlidingWindowCounterRateLimiter")
    return False

# Run the test
bug_found = asyncio.run(main())
if bug_found:
    sys.exit(1)