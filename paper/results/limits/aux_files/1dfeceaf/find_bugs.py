#!/usr/bin/env python3
"""
Combined bug finder for limits.aio module
"""
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter, 
    SlidingWindowCounterRateLimiter
)
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def test_fixed_window():
    """Test FixedWindowRateLimiter for bugs"""
    print("\n" + "="*60)
    print("Testing FixedWindowRateLimiter")
    print("="*60)
    
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    item = RateLimitItemPerSecond(10)
    
    # Test boundary
    await limiter.hit(item, "user", cost=9)
    can_test = await limiter.test(item, "user", cost=1)
    can_hit = await limiter.hit(item, "user", cost=1)
    
    if can_test != can_hit:
        print(f"❌ BUG: test()={can_test}, hit()={can_hit} for Fixed Window")
        return True
    
    print("✓ FixedWindowRateLimiter: No bugs found")
    return False

async def test_moving_window():
    """Test MovingWindowRateLimiter for bugs"""
    print("\n" + "="*60)
    print("Testing MovingWindowRateLimiter")
    print("="*60)
    
    storage = MemoryStorage()
    limiter = MovingWindowRateLimiter(storage)
    item = RateLimitItemPerSecond(10)
    
    # Test exact boundary: consume 9, test/hit 1
    result = await limiter.hit(item, "user", cost=9)
    print(f"Consumed 9/10: {result}")
    
    can_test = await limiter.test(item, "user", cost=1)
    print(f"test(cost=1) after 9: {can_test}")
    
    can_hit = await limiter.hit(item, "user", cost=1)
    print(f"hit(cost=1) after 9: {can_hit}")
    
    if can_test != can_hit:
        print(f"\n❌ BUG FOUND in MovingWindowRateLimiter!")
        print(f"test() returned {can_test} but hit() returned {can_hit}")
        print("This indicates an off-by-one error in the test() method")
        
        # Additional diagnosis
        stats = await limiter.get_window_stats(item, "user")
        print(f"Window stats: remaining={stats.remaining}")
        
        return True
    
    # Test at exact limit
    await limiter.clear(item, "user")
    await limiter.hit(item, "user", cost=10)
    
    can_test = await limiter.test(item, "user", cost=1)
    if can_test:
        print(f"❌ BUG: test() returns True when at limit")
        can_hit = await limiter.hit(item, "user", cost=1)
        if can_hit:
            print(f"❌ CRITICAL: Rate limit exceeded!")
        return True
    
    print("✓ MovingWindowRateLimiter: No obvious bugs found")
    return False

async def test_sliding_window():
    """Test SlidingWindowCounterRateLimiter for bugs"""
    print("\n" + "="*60)
    print("Testing SlidingWindowCounterRateLimiter")
    print("="*60)
    
    storage = MemoryStorage()
    limiter = SlidingWindowCounterRateLimiter(storage)
    item = RateLimitItemPerSecond(10)
    
    # Test boundary
    await limiter.hit(item, "user", cost=9)
    can_test = await limiter.test(item, "user", cost=1)
    can_hit = await limiter.hit(item, "user", cost=1)
    
    if can_test != can_hit:
        print(f"❌ BUG: test()={can_test}, hit()={can_hit} for Sliding Window")
        return True
    
    # Test at limit
    await limiter.clear(item, "user")
    await limiter.hit(item, "user", cost=10)
    can_test = await limiter.test(item, "user", cost=1)
    
    if can_test:
        print(f"❌ BUG: test() returns True when at limit")
        return True
    
    print("✓ SlidingWindowCounterRateLimiter: No bugs found")
    return False

async def main():
    print("="*60)
    print("limits.aio Bug Hunter")
    print("="*60)
    
    bugs_found = []
    
    # Test each rate limiter
    if await test_fixed_window():
        bugs_found.append("FixedWindowRateLimiter")
    
    if await test_moving_window():
        bugs_found.append("MovingWindowRateLimiter")
    
    if await test_sliding_window():
        bugs_found.append("SlidingWindowCounterRateLimiter")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if bugs_found:
        print(f"❌ Found bugs in: {', '.join(bugs_found)}")
        return 1
    else:
        print("✓ No bugs found in any rate limiter")
        return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))