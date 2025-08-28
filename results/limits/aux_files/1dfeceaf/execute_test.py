#!/usr/bin/env python3
"""Execute the comprehensive test inline"""
import sys
import asyncio

# Add packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

# Import everything we need
from limits.aio.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

async def main():
    """Test for the most likely bug - boundary consistency"""
    
    print("Testing for consistency bugs in limits.aio rate limiters...")
    print("="*60)
    
    # Test each limiter type
    limiters = [
        ("FixedWindow", FixedWindowRateLimiter(MemoryStorage())),
        ("MovingWindow", MovingWindowRateLimiter(MemoryStorage())),
        ("SlidingWindow", SlidingWindowCounterRateLimiter(MemoryStorage()))
    ]
    
    for name, limiter in limiters:
        print(f"\nTesting {name}RateLimiter:")
        print("-"*40)
        
        # Create a simple rate limit: 10 per second
        item = RateLimitItemPerSecond(10)
        
        # Test Case 1: Boundary - consume 9, then try 1 more
        print("  Test 1: Consume 9/10, then test and hit with 1")
        
        # Consume 9
        result = await limiter.hit(item, "user", cost=9)
        print(f"    hit(9) = {result}")
        
        # test() should say we can consume 1 more
        can_test = await limiter.test(item, "user", cost=1)
        print(f"    test(1) = {can_test}")
        
        # hit() should also succeed
        can_hit = await limiter.hit(item, "user", cost=1)
        print(f"    hit(1) = {can_hit}")
        
        if can_test and not can_hit:
            print(f"\n    ❌ BUG FOUND in {name}RateLimiter!")
            print(f"    test() returned True but hit() returned False")
            print(f"    This is a consistency bug between test() and hit()")
            
            # Get more diagnostic info
            stats = await limiter.get_window_stats(item, "user")
            print(f"    Window stats: remaining={stats.remaining}")
            
            # This is a genuine bug
            return name
        elif not can_test and can_hit:
            print(f"\n    ❌ BUG FOUND in {name}RateLimiter!")
            print(f"    test() returned False but hit() returned True")
            print(f"    This could allow exceeding the rate limit!")
            return name
        
        # Clear for next test
        await limiter.clear(item, "user")
        
        # Test Case 2: At limit - consume 10, then try 1 more
        print("  Test 2: Consume 10/10, then test with 1")
        
        result = await limiter.hit(item, "user", cost=10)
        print(f"    hit(10) = {result}")
        
        can_test = await limiter.test(item, "user", cost=1)
        print(f"    test(1) = {can_test}")
        
        if can_test:
            print(f"\n    ❌ BUG FOUND in {name}RateLimiter!")
            print(f"    test() returns True when at limit!")
            
            # Try to actually hit
            can_hit = await limiter.hit(item, "user", cost=1)
            print(f"    hit(1) = {can_hit}")
            
            if can_hit:
                print(f"    ❌❌ CRITICAL: Rate limit can be exceeded!")
            
            return name
        
        print(f"  ✓ {name}RateLimiter passed basic tests")
    
    print("\n" + "="*60)
    print("✓ All limiters passed - no obvious bugs found")
    return None

# Execute
bug_found = asyncio.run(main())

if bug_found:
    print(f"\n🐛 Bug detected in {bug_found}RateLimiter")
    print("This needs further investigation and reporting")
    sys.exit(1)
else:
    print("\n✅ No bugs found in limits.aio rate limiters")
    sys.exit(0)