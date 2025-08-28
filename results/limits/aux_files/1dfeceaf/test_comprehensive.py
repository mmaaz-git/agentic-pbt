#!/usr/bin/env python3
"""
Comprehensive test to find any bugs in limits.aio
"""
import sys
import asyncio
from hypothesis import given, strategies as st, settings, assume
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

# Manual test for consistency
async def test_consistency_manual():
    """Manually test each limiter for consistency bugs"""
    
    limiters = [
        ("FixedWindow", FixedWindowRateLimiter(MemoryStorage())),
        ("MovingWindow", MovingWindowRateLimiter(MemoryStorage())),
        ("SlidingWindow", SlidingWindowCounterRateLimiter(MemoryStorage()))
    ]
    
    bugs = []
    
    for name, limiter in limiters:
        print(f"\nTesting {name}RateLimiter...")
        
        # Test multiple scenarios
        scenarios = [
            (10, 9, 1, "Boundary case: 9+1=10"),
            (10, 10, 1, "Over limit: 10+1=11"),
            (10, 8, 2, "Exact limit: 8+2=10"),
            (10, 7, 3, "Exact limit: 7+3=10"),
            (10, 5, 5, "Half and half: 5+5=10"),
            (100, 99, 1, "Large boundary: 99+1=100"),
            (1, 0, 1, "Single item: 0+1=1"),
            (1, 1, 1, "Single over: 1+1=2"),
        ]
        
        for limit, consumed, cost, description in scenarios:
            item = RateLimitItemPerSecond(limit)
            
            # Clear any previous state
            await limiter.clear(item, "test")
            
            # Consume initial amount
            if consumed > 0:
                hit_result = await limiter.hit(item, "test", cost=consumed)
                if not hit_result and consumed <= limit:
                    print(f"  ❌ Failed to consume initial {consumed} (limit={limit})")
                    bugs.append((name, f"Initial consumption failed"))
                    continue
            
            # Test consistency
            can_test = await limiter.test(item, "test", cost=cost)
            can_hit = await limiter.hit(item, "test", cost=cost)
            
            # They should match
            if can_test != can_hit:
                print(f"  ❌ {description}")
                print(f"     test()={can_test}, hit()={can_hit}")
                bugs.append((name, f"{description}: test={can_test}, hit={can_hit}"))
                
                # Get more details
                stats = await limiter.get_window_stats(item, "test")
                print(f"     Stats: remaining={stats.remaining}")
            else:
                # Verify the result is correct
                expected = (consumed + cost) <= limit
                if can_test != expected:
                    print(f"  ❌ {description}")
                    print(f"     Expected {expected}, got {can_test}")
                    bugs.append((name, f"{description}: wrong result"))
    
    return bugs

# Property-based test with Hypothesis
@given(
    limit=st.integers(min_value=1, max_value=1000),
    consumed=st.integers(min_value=0, max_value=1000),
    cost=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=500, deadline=None)
async def test_consistency_property(limit, consumed, cost):
    """Property: test() and hit() should be consistent"""
    
    # Only test valid scenarios
    assume(consumed <= limit)
    assume(cost >= 0)
    
    # Test all three limiters
    limiters = [
        FixedWindowRateLimiter(MemoryStorage()),
        MovingWindowRateLimiter(MemoryStorage()),
        SlidingWindowCounterRateLimiter(MemoryStorage())
    ]
    
    item = RateLimitItemPerSecond(limit)
    
    for limiter in limiters:
        # Consume initial amount
        if consumed > 0:
            result = await limiter.hit(item, "test", cost=consumed)
            if not result:
                continue  # Skip if initial consumption failed
        
        # Test consistency
        can_test = await limiter.test(item, "test", cost=cost)
        can_hit = await limiter.hit(item, "test", cost=cost)
        
        # Special case: cost=0 should always succeed for test
        if cost == 0 and not can_test:
            raise AssertionError(f"test(cost=0) returned False")
        
        # They should match (except for race conditions, but we're single-threaded)
        if can_test != can_hit:
            limiter_name = limiter.__class__.__name__
            raise AssertionError(
                f"{limiter_name}: test()={can_test}, hit()={can_hit} "
                f"(limit={limit}, consumed={consumed}, cost={cost})"
            )

# Run the tests
async def main():
    print("="*60)
    print("Comprehensive Bug Hunt for limits.aio")
    print("="*60)
    
    # Run manual tests
    print("\n1. Running manual consistency tests...")
    bugs = await test_consistency_manual()
    
    if bugs:
        print(f"\n❌ Found {len(bugs)} consistency issues:")
        for limiter, issue in bugs:
            print(f"  - {limiter}: {issue}")
    else:
        print("\n✓ Manual tests passed")
    
    # Run property-based tests
    print("\n2. Running property-based tests...")
    try:
        # Run the property test multiple times
        for i in range(10):
            await test_consistency_property()
        print("✓ Property-based tests passed")
    except AssertionError as e:
        print(f"❌ Property test failed: {e}")
        bugs.append(("Property", str(e)))
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    
    if bugs:
        print(f"❌ Total issues found: {len(bugs)}")
        return 1
    else:
        print("✓ All tests passed - no bugs found")
        return 0

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)