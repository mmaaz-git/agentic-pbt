#!/usr/bin/env python3
"""
Quick focused test to find bugs in limits.strategies
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
import traceback

from limits.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond


def test_fixed_window_test_boundary():
    """Test edge case in FixedWindowRateLimiter.test() method"""
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    # Create a limit of 5 per second
    item = RateLimitItemPerSecond(5, 1)
    ids = ('test',)
    
    # Clear state
    strategy.clear(item, *ids)
    
    # Use 4 out of 5
    for _ in range(4):
        assert strategy.hit(item, *ids, cost=1), "Hit should succeed"
    
    # Now we have 1 remaining
    stats = strategy.get_window_stats(item, *ids)
    print(f"After 4 hits: remaining={stats.remaining}")
    assert stats.remaining == 1, f"Should have 1 remaining, got {stats.remaining}"
    
    # Test with cost=1 should return True (we have exactly 1 left)
    can_hit_1 = strategy.test(item, *ids, cost=1)
    print(f"test(cost=1) = {can_hit_1}")
    assert can_hit_1, "Should be able to hit with cost=1"
    
    # Test with cost=2 should return False (we only have 1 left)
    can_hit_2 = strategy.test(item, *ids, cost=2)
    print(f"test(cost=2) = {can_hit_2}")
    assert not can_hit_2, "Should NOT be able to hit with cost=2"
    
    # Actually hit with cost=1 should succeed
    hit_result = strategy.hit(item, *ids, cost=1)
    print(f"hit(cost=1) = {hit_result}")
    assert hit_result, "Hit with cost=1 should succeed"
    
    # Now we should have 0 remaining
    stats = strategy.get_window_stats(item, *ids)
    print(f"After 5 hits: remaining={stats.remaining}")
    assert stats.remaining == 0, f"Should have 0 remaining, got {stats.remaining}"
    
    # Test with cost=1 should now return False
    can_hit_after = strategy.test(item, *ids, cost=1)
    print(f"test(cost=1) after exhaustion = {can_hit_after}")
    assert not can_hit_after, "Should NOT be able to hit when exhausted"


def test_fixed_window_boundary_bug():
    """Investigate potential off-by-one error in FixedWindowRateLimiter.test()"""
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    # Create a limit
    item = RateLimitItemPerSecond(10, 1)
    ids = ('boundary_test',)
    
    # Clear state
    strategy.clear(item, *ids)
    
    print(f"\nTesting with limit={item.amount}")
    
    # Test various boundary conditions
    test_cases = [
        (0, 10, True),   # 0 used, cost=10, should work
        (0, 11, False),  # 0 used, cost=11, should fail  
        (9, 1, True),    # 9 used, cost=1, should work
        (9, 2, False),   # 9 used, cost=2, should fail
        (10, 1, False),  # 10 used, cost=1, should fail
    ]
    
    for used, cost, expected in test_cases:
        strategy.clear(item, *ids)
        
        # Use up 'used' amount
        for _ in range(used):
            strategy.hit(item, *ids, cost=1)
        
        # Check storage state
        current_count = strategy.storage.get(item.key_for(*ids))
        print(f"\nUsed={used}, storage.get()={current_count}")
        
        # Test the boundary
        test_result = strategy.test(item, *ids, cost=cost)
        print(f"  test(cost={cost}): expected={expected}, got={test_result}")
        
        # Check the test() implementation
        # From line 177: return self.storage.get(key) < item.amount - cost + 1
        manual_calc = current_count < item.amount - cost + 1
        print(f"  Manual calc: {current_count} < {item.amount} - {cost} + 1 = {current_count} < {item.amount - cost + 1} = {manual_calc}")
        
        if test_result != expected:
            print(f"  ❌ BUG FOUND! test() returned {test_result} but expected {expected}")
            print(f"     Formula: storage.get({current_count}) < amount({item.amount}) - cost({cost}) + 1")
            print(f"     Evaluates to: {current_count} < {item.amount - cost + 1}")
            return False
    
    return True


def test_moving_window_boundary():
    """Test MovingWindowRateLimiter boundary conditions"""
    storage = MemoryStorage()
    strategy = MovingWindowRateLimiter(storage)
    
    item = RateLimitItemPerSecond(5, 1)
    ids = ('moving_test',)
    
    strategy.clear(item, *ids)
    
    # Fill up the limit
    for i in range(5):
        result = strategy.hit(item, *ids, cost=1)
        print(f"Hit {i+1}: {result}")
        assert result, f"Hit {i+1} should succeed"
    
    # This should fail
    result = strategy.hit(item, *ids, cost=1)
    print(f"Hit 6: {result}")
    assert not result, "Hit 6 should fail"
    
    # Check test() behavior at the boundary
    # From line 119: <= item.amount - cost
    can_test = strategy.test(item, *ids, cost=1)
    print(f"test(cost=1) when full: {can_test}")
    
    stats = strategy.get_window_stats(item, *ids)
    print(f"Stats: remaining={stats.remaining}")


def test_consistency_between_strategies():
    """Test that all strategies behave consistently for basic operations"""
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(3, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        print(f"\nTesting {name}:")
        
        # Each strategy uses different keys, so they don't interfere
        ids = (name,)
        
        # Clear and test initial state
        strategy.clear(item, *ids)
        stats = strategy.get_window_stats(item, *ids)
        print(f"  Initial: remaining={stats.remaining}")
        assert stats.remaining == 3, f"{name}: Initial remaining should be 3"
        
        # Hit once
        assert strategy.hit(item, *ids, cost=1), f"{name}: First hit should succeed"
        stats = strategy.get_window_stats(item, *ids)
        print(f"  After 1 hit: remaining={stats.remaining}")
        assert stats.remaining == 2, f"{name}: Should have 2 remaining"
        
        # Hit twice more to exhaust
        assert strategy.hit(item, *ids, cost=1), f"{name}: Second hit should succeed"
        assert strategy.hit(item, *ids, cost=1), f"{name}: Third hit should succeed"
        
        stats = strategy.get_window_stats(item, *ids)
        print(f"  After 3 hits: remaining={stats.remaining}")
        assert stats.remaining == 0, f"{name}: Should have 0 remaining"
        
        # Next hit should fail
        assert not strategy.hit(item, *ids, cost=1), f"{name}: Fourth hit should fail"
        
        # test() should also say no
        assert not strategy.test(item, *ids, cost=1), f"{name}: test() should return False when exhausted"


if __name__ == "__main__":
    print("Running focused bug-hunting tests...\n")
    
    tests = [
        ("Fixed Window Test Boundary", test_fixed_window_test_boundary),
        ("Fixed Window Boundary Bug Check", test_fixed_window_boundary_bug),
        ("Moving Window Boundary", test_moving_window_boundary),
        ("Consistency Between Strategies", test_consistency_between_strategies),
    ]
    
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print('='*60)
        try:
            result = test_func()
            if result is False:
                print(f"❌ {name} revealed a potential bug!")
            else:
                print(f"✅ {name} passed")
        except AssertionError as e:
            print(f"❌ {name} FAILED: {e}")
            traceback.print_exc()
        except Exception as e:
            print(f"❌ {name} ERROR: {e}")
            traceback.print_exc()