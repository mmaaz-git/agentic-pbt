#!/usr/bin/env python3
"""
Simple test to check if limits.aio has bugs
"""

import sys
import asyncio

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import FixedWindowRateLimiter
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def test_boundary_bug():
    """Test for boundary calculation bug in FixedWindowRateLimiter"""
    
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    # Create a rate limit of 10 per second
    item = RateLimitItemPerSecond(10)
    
    # Consume 9 items
    result = await limiter.hit(item, "user1", cost=9)
    print(f"Hit with cost=9: {result}")
    
    # Now test if we can consume 1 more (should be True)
    can_consume = await limiter.test(item, "user1", cost=1)
    print(f"Test with cost=1 after consuming 9: {can_consume}")
    
    # Try to actually consume it
    hit_result = await limiter.hit(item, "user1", cost=1)
    print(f"Hit with cost=1: {hit_result}")
    
    # Check stats
    stats = await limiter.get_window_stats(item, "user1")
    print(f"Window stats - remaining: {stats.remaining}")
    
    # Now test edge case: exactly at limit
    await limiter.clear(item, "user1")
    
    # Consume exactly the limit
    result = await limiter.hit(item, "user1", cost=10)
    print(f"\nAfter clear, hit with cost=10: {result}")
    
    # Test if we can consume 1 more (should be False)
    can_consume = await limiter.test(item, "user1", cost=1)
    print(f"Test with cost=1 after consuming 10: {can_consume}")
    
    # Check the actual storage value
    current_count = await storage.get(item.key_for("user1"))
    print(f"Current count in storage: {current_count}")
    
    print("\n--- Testing boundary condition ---")
    # The test method uses: storage.get(key) < item.amount - cost + 1
    # Which means: storage.get(key) <= item.amount - cost
    # Let's verify this
    
    await limiter.clear(item, "user1")
    
    # Test different scenarios
    test_cases = [
        (0, 1, True),   # 0 consumed, test 1
        (5, 5, True),   # 5 consumed, test 5  
        (9, 1, True),   # 9 consumed, test 1
        (10, 1, False), # 10 consumed, test 1
        (8, 3, False),  # 8 consumed, test 3
    ]
    
    for consumed, test_cost, expected in test_cases:
        await limiter.clear(item, "user1")
        if consumed > 0:
            await limiter.hit(item, "user1", cost=consumed)
        
        can_consume = await limiter.test(item, "user1", cost=test_cost)
        current = await storage.get(item.key_for("user1"))
        
        # Check the formula: current < amount - cost + 1
        formula_result = current < item.amount - test_cost + 1
        
        print(f"Consumed: {consumed}, Test cost: {test_cost}")
        print(f"  Current in storage: {current}")
        print(f"  Formula (current < amount - cost + 1): {current} < {item.amount} - {test_cost} + 1 = {formula_result}")
        print(f"  test() returned: {can_consume}, Expected: {expected}")
        
        if can_consume != expected:
            print(f"  ❌ MISMATCH! Expected {expected}, got {can_consume}")
        else:
            print(f"  ✓ Correct")
        
        # Also check if hit() agrees
        if can_consume:
            hit_result = await limiter.hit(item, "user1", cost=test_cost)
            if not hit_result:
                print(f"  ❌ test() returned True but hit() failed!")

# Run the test
asyncio.run(test_boundary_bug())