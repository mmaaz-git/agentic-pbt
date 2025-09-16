#!/usr/bin/env python3
"""
Test for potential off-by-one error in MovingWindowRateLimiter.test()
"""
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import MovingWindowRateLimiter
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def main():
    storage = MemoryStorage()
    limiter = MovingWindowRateLimiter(storage)
    item = RateLimitItemPerSecond(10)  # 10 requests per second
    
    print("Testing MovingWindowRateLimiter boundary condition...")
    print("Rate limit: 10 per second")
    print()
    
    # Test Case 1: Consume 9, then test and hit with 1
    print("Test Case 1: Consume 9, then test/hit with 1")
    print("-" * 40)
    
    # Consume 9 out of 10
    result = await limiter.hit(item, "user", cost=9)
    print(f"1. hit(cost=9): {result}")
    
    # Get current window stats
    stats = await limiter.get_window_stats(item, "user")
    print(f"2. Window stats - remaining: {stats.remaining}")
    
    # test() for cost=1 (should return True since 9+1=10 is within limit)
    can_test = await limiter.test(item, "user", cost=1)
    print(f"3. test(cost=1): {can_test}")
    
    # hit() for cost=1 (should succeed if test was True)
    can_hit = await limiter.hit(item, "user", cost=1)
    print(f"4. hit(cost=1): {can_hit}")
    
    # Check final stats
    stats = await limiter.get_window_stats(item, "user")
    print(f"5. Final window stats - remaining: {stats.remaining}")
    
    if can_test != can_hit:
        print(f"\n❌ BUG FOUND: test() returned {can_test} but hit() returned {can_hit}")
        print("This is an inconsistency between test() and hit()!")
        return True
    
    # Reset for next test
    await limiter.clear(item, "user")
    print()
    
    # Test Case 2: Exact boundary - consume 10, then test with 1
    print("Test Case 2: Consume 10, then test with 1")
    print("-" * 40)
    
    # Consume exactly the limit
    result = await limiter.hit(item, "user", cost=10)
    print(f"1. hit(cost=10): {result}")
    
    # Get current window stats
    stats = await limiter.get_window_stats(item, "user")
    print(f"2. Window stats - remaining: {stats.remaining}")
    
    # test() for cost=1 (should return False since we're at limit)
    can_test = await limiter.test(item, "user", cost=1)
    print(f"3. test(cost=1) when at limit: {can_test}")
    
    if can_test:
        print(f"\n❌ BUG FOUND: test() incorrectly returns True when at limit!")
        # Try to actually consume
        can_hit = await limiter.hit(item, "user", cost=1)
        print(f"4. hit(cost=1) when at limit: {can_hit}")
        
        if can_hit:
            stats = await limiter.get_window_stats(item, "user")
            print(f"5. Window stats after exceeding: remaining={stats.remaining}")
            print(f"\n❌ CRITICAL: Rate limit exceeded! Consumed 11 when limit is 10")
            return True
    
    # Reset
    await limiter.clear(item, "user")
    print()
    
    # Test Case 3: Edge case with exact amounts
    print("Test Case 3: Multiple edge cases")
    print("-" * 40)
    
    test_cases = [
        (8, 2, True, "8+2=10, should succeed"),
        (9, 2, False, "9+2=11, should fail"),
        (10, 0, True, "10+0=10, zero cost should always succeed"),
        (10, 1, False, "10+1=11, should fail"),
    ]
    
    for consumed, test_cost, expected, description in test_cases:
        await limiter.clear(item, "user")
        
        if consumed > 0:
            await limiter.hit(item, "user", cost=consumed)
        
        can_test = await limiter.test(item, "user", cost=test_cost)
        
        print(f"  {description}")
        print(f"    test(cost={test_cost}) after consuming {consumed}: {can_test}")
        
        if can_test != expected:
            print(f"    ❌ Expected {expected}, got {can_test}")
            
            # Also verify with hit()
            can_hit = await limiter.hit(item, "user", cost=test_cost)
            print(f"    hit(cost={test_cost}): {can_hit}")
            
            if can_test != can_hit:
                print(f"    ❌ INCONSISTENCY: test()={can_test}, hit()={can_hit}")
                return True
    
    print("\n✓ All tests passed - no bugs found")
    return False

# Run the test
bug_found = asyncio.run(main())
if bug_found:
    sys.exit(1)