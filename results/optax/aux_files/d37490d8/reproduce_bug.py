#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import FixedWindowRateLimiter
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def main():
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    item = RateLimitItemPerSecond(10)  # 10 requests per second
    
    # Scenario 1: test() says we can consume, but can we really?
    print("Testing consistency between test() and hit()...")
    
    # Consume 9 out of 10
    await limiter.hit(item, "user", cost=9)
    
    # test() should return True for cost=1 (we have 1 left)
    can_test = await limiter.test(item, "user", cost=1)
    print(f"After consuming 9/10, test(cost=1) returns: {can_test}")
    
    # hit() should also succeed
    can_hit = await limiter.hit(item, "user", cost=1)
    print(f"After consuming 9/10, hit(cost=1) returns: {can_hit}")
    
    if can_test and not can_hit:
        print("BUG FOUND: test() returned True but hit() failed!")
        return
        
    # Reset for next test
    await limiter.clear(item, "user")
    
    # Scenario 2: Edge case at exact boundary
    print("\nTesting exact boundary...")
    
    # Consume exactly the limit
    await limiter.hit(item, "user", cost=10)
    current = await storage.get(item.key_for("user"))
    print(f"After consuming 10/10, storage contains: {current}")
    
    # test() for any positive cost should return False
    can_test = await limiter.test(item, "user", cost=1)
    print(f"test(cost=1) when at limit returns: {can_test}")
    
    if can_test:
        print("BUG FOUND: test() incorrectly allows consumption when at limit!")
        # Try to actually consume
        can_hit = await limiter.hit(item, "user", cost=1)
        print(f"hit(cost=1) when at limit returns: {can_hit}")
        new_count = await storage.get(item.key_for("user"))
        print(f"Storage after hit: {new_count}")
        
        if can_hit and new_count > item.amount:
            print(f"CRITICAL BUG: Rate limit exceeded! {new_count} > {item.amount}")

asyncio.run(main())