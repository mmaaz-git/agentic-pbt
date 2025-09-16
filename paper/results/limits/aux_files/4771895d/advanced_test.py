#!/usr/bin/env python3
"""
Advanced tests to find bugs in limits.strategies
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import time
from limits.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond, RateLimitItemPerMinute


def test_concurrent_operations():
    """Test that test() and hit() remain consistent under concurrent-like operations"""
    
    print("Testing concurrent-like operations")
    print("="*60)
    
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(10, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        ids = (name, 'concurrent')
        
        strategy.clear(item, *ids)
        
        # Simulate concurrent hits
        successful_hits = 0
        failed_hits = 0
        
        for i in range(20):  # Try more hits than the limit
            # Always check test() first
            if strategy.test(item, *ids, cost=1):
                # test() says we can hit
                if strategy.hit(item, *ids, cost=1):
                    successful_hits += 1
                else:
                    print(f"❌ BUG in {name}: test() returned True but hit() failed!")
                    print(f"  After {successful_hits} successful hits")
                    stats = strategy.get_window_stats(item, *ids)
                    print(f"  Stats: remaining={stats.remaining}")
                    return False
            else:
                # test() says we can't hit
                if strategy.hit(item, *ids, cost=1):
                    print(f"❌ BUG in {name}: test() returned False but hit() succeeded!")
                    failed_hits += 1
                    
        print(f"{name}: {successful_hits} successful, {failed_hits} failed")
        
        # Verify we hit exactly the limit
        if successful_hits != 10:
            print(f"  Warning: Expected 10 successful hits, got {successful_hits}")
    
    print("✅ Concurrent operations test passed")
    return True


def test_large_costs():
    """Test behavior with costs larger than the limit"""
    
    print("\nTesting large costs")
    print("="*60)
    
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(5, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        ids = (name, 'large_cost')
        
        strategy.clear(item, *ids)
        
        # Try cost larger than limit
        test_result = strategy.test(item, *ids, cost=10)
        hit_result = strategy.hit(item, *ids, cost=10)
        
        print(f"{name}: cost=10 (limit=5)")
        print(f"  test() = {test_result}")
        print(f"  hit() = {hit_result}")
        
        if test_result != hit_result:
            print(f"  ❌ BUG: test() and hit() disagree!")
            return False
        
        # Stats should still be at full capacity
        stats = strategy.get_window_stats(item, *ids)
        if stats.remaining != 5:
            print(f"  ❌ BUG: Large failed hit modified state! remaining={stats.remaining}")
            return False
    
    print("✅ Large costs test passed")
    return True


def test_zero_cost():
    """Test behavior with cost=0"""
    
    print("\nTesting cost=0")
    print("="*60)
    
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(3, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        ids = (name, 'zero_cost')
        
        # Test at various fill levels
        for used in [0, 2, 3]:  # empty, partial, full
            strategy.clear(item, *ids)
            
            # Use up 'used' slots
            for _ in range(used):
                strategy.hit(item, *ids, cost=1)
            
            # Try cost=0
            test_result = strategy.test(item, *ids, cost=0)
            hit_result = strategy.hit(item, *ids, cost=0)
            
            stats_before = strategy.get_window_stats(item, *ids)
            
            print(f"{name}: used={used}/3, cost=0")
            print(f"  test() = {test_result}")
            print(f"  hit() = {hit_result}")
            
            if test_result != hit_result:
                print(f"  ❌ BUG: test() and hit() disagree on cost=0!")
                return False
            
            # Verify state didn't change (for cost=0)
            stats_after = strategy.get_window_stats(item, *ids)
            if hit_result and stats_after.remaining != stats_before.remaining:
                print(f"  Note: cost=0 hit changed remaining from {stats_before.remaining} to {stats_after.remaining}")
    
    print("✅ Zero cost test passed")
    return True


def test_negative_costs():
    """Test behavior with negative costs (edge case)"""
    
    print("\nTesting negative costs")
    print("="*60)
    
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    item = RateLimitItemPerSecond(5, 1)
    ids = ('negative',)
    
    strategy.clear(item, *ids)
    
    # Use 3 out of 5
    for _ in range(3):
        strategy.hit(item, *ids, cost=1)
    
    try:
        # Try negative cost
        test_result = strategy.test(item, *ids, cost=-1)
        hit_result = strategy.hit(item, *ids, cost=-1)
        
        print(f"With 3/5 used, cost=-1:")
        print(f"  test() = {test_result}")
        print(f"  hit() = {hit_result}")
        
        # Check if state changed
        stats = strategy.get_window_stats(item, *ids)
        print(f"  Remaining after: {stats.remaining}")
        
        if test_result != hit_result:
            print("  ❌ BUG: test() and hit() disagree on negative cost!")
            return False
            
    except Exception as e:
        print(f"  Exception with negative cost: {e}")
    
    print("✅ Negative cost test completed")
    return True


def test_fractional_weighted_count():
    """Test SlidingWindowCounterRateLimiter with fractional weighted counts"""
    
    print("\nTesting SlidingWindowCounterRateLimiter weighted count")
    print("="*60)
    
    storage = MemoryStorage()
    strategy = SlidingWindowCounterRateLimiter(storage)
    
    item = RateLimitItemPerSecond(10, 1)
    ids = ('weighted',)
    
    strategy.clear(item, *ids)
    
    # Do some hits
    for i in range(5):
        result = strategy.hit(item, *ids, cost=1)
        print(f"Hit {i+1}: {result}")
    
    # Get the weighted count info
    stats = strategy.get_window_stats(item, *ids)
    print(f"After 5 hits: remaining={stats.remaining}")
    
    # Test boundary with fractional weighted count
    test_5 = strategy.test(item, *ids, cost=5)
    hit_5 = strategy.hit(item, *ids, cost=5)
    
    print(f"test(cost=5) = {test_5}")
    print(f"hit(cost=5) = {hit_5}")
    
    if test_5 != hit_5:
        print("❌ BUG: test() and hit() disagree in sliding window!")
        return False
    
    print("✅ Weighted count test passed")
    return True


def main():
    print("Running advanced bug hunting tests")
    print("="*70)
    
    tests = [
        ("Concurrent Operations", test_concurrent_operations),
        ("Large Costs", test_large_costs),
        ("Zero Cost", test_zero_cost),
        ("Negative Costs", test_negative_costs),
        ("Fractional Weighted Count", test_fractional_weighted_count),
    ]
    
    all_passed = True
    for name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
                print(f"\n❌ {name} test revealed a bug!")
        except Exception as e:
            all_passed = False
            print(f"\n❌ {name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All advanced tests passed - no bugs found")
    else:
        print("❌ Some tests failed - bugs were found!")
    
    return all_passed


if __name__ == "__main__":
    main()